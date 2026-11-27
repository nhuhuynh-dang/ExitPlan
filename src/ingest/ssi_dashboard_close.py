"""Daily close reference data, strictly separate from recorded order books."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import threading
import time

import pandas as pd
from src.analytics.ssi_history_stats import HOLIDAYS_2026, expected_sessions
from src.ingest.ssi_fastconnect_v3 import SSIReadOnlyClient, normalize_ohlc, SSIAuthError, SSIBadRequest, SSISymbolNotFound

VN=timezone(timedelta(hours=7))
CLOSE_FILE="data/processed/ssi_dashboard_closes.parquet"


def market_phase(now=None):
    t=pd.Timestamp(now if now is not None else datetime.now(VN))
    t=t.tz_localize("Asia/Ho_Chi_Minh") if t.tzinfo is None else t.tz_convert("Asia/Ho_Chi_Minh")
    if t.year!=2026:return "calendar_unknown"
    if t.weekday()>=5 or t.tz_localize(None).normalize() in HOLIDAYS_2026:return "closed"
    minute=t.hour*60+t.minute
    if minute<9*60:return "closed"
    if 9*60+15<=minute<11*60+30 or 13*60<=minute<14*60+30:return "continuous"
    if 11*60+30<=minute<13*60:return "lunch"
    if minute>=15*60+15:return "closed"
    return "transition"


def completed_date(now=None):
    """Wait until 15:15 ICT before requesting the day's daily OHLC.
    No current-day close during lunch, auctions or the publication buffer.
    """
    t=pd.Timestamp(now if now is not None else datetime.now(VN))
    t=t.tz_localize("Asia/Ho_Chi_Minh") if t.tzinfo is None else t.tz_convert("Asia/Ho_Chi_Minh")
    if t.year!=2026:return None
    day=t.tz_localize(None).normalize()
    if t.hour*60+t.minute>=15*60+15:day+=pd.Timedelta(days=1)
    dates=expected_sessions(day,1)
    return dates[-1].date() if dates is not None else None


def close_references(history,extra,symbols,target):
    """Return latest actual daily close per requested symbol, at or before target."""
    rows=[]
    for d in (history,extra):
        if d is None or d.empty:continue
        if not {"symbol","tradingDate","close","source","data_kind"}.issubset(d):continue
        d=d[d.source.eq("ssi_fastconnect_v3") & d.data_kind.eq("historical") & d.symbol.isin(symbols)].copy()
        d["tradingDate"]=pd.to_datetime(d.tradingDate,errors="coerce").dt.normalize()
        d["close"]=pd.to_numeric(d.close,errors="coerce")
        d=d[d.tradingDate.le(pd.Timestamp(target)) & d.close.gt(0) & d.close.lt(float("inf"))]
        rows.append(d[["symbol","tradingDate","close"]])
    if not rows:return {}
    d=pd.concat(rows,ignore_index=True).sort_values("tradingDate",kind="stable").drop_duplicates("symbol",keep="last")
    return {r.symbol:dict(close=float(r.close),date=r.tradingDate.date(),current=r.tradingDate.date()==target)
            for r in d.itertuples()}


def merge_daily_history(base,extra):
    """Supplement missing daily bars without rewriting or superseding research data."""
    required={'symbol','tradingDate','close','volume','source','data_kind'}
    frames=[]
    for frame in (base,extra):
        if frame is None or frame.empty:continue
        if not required.issubset(frame.columns) or set(frame.source)!={'ssi_fastconnect_v3'} or set(frame.data_kind)!={'historical'}:
            raise ValueError('Nguồn OHLCV SSI không hợp lệ')
        d=frame.copy()
        d['tradingDate']=pd.to_datetime(d.tradingDate,errors='raise').dt.normalize()
        if d.duplicated(['symbol','tradingDate']).any():raise ValueError('OHLCV trùng phiên')
        if 'price_unit' in d and set(d.price_unit.dropna())-{'as_returned_by_ssi_api'}:
            raise ValueError('Đơn vị OHLCV không tương thích')
        frames.append(d)
    if not frames:return None
    # Base is authoritative if an independently retrieved daily bar overlaps.
    return pd.concat(frames,ignore_index=True).drop_duplicates(['symbol','tradingDate'],keep='first').sort_values(['symbol','tradingDate']).reset_index(drop=True)


def missing_daily_symbols(history,symbols,target):
    """Only request symbols without a valid bar for the most recent completed day."""
    if history is None or history.empty:return sorted(set(symbols))
    dates=pd.to_datetime(history.tradingDate,errors='coerce').dt.normalize()
    close=pd.to_numeric(history.close,errors='coerce')
    vol=pd.to_numeric(history.volume,errors='coerce')
    good=history[dates.eq(pd.Timestamp(target)) & close.gt(0)&close.lt(float('inf'))&vol.ge(0)&vol.lt(float('inf'))]
    return sorted(set(symbols)-set(good.symbol))


class CloseWorker:
    """Bounded per-symbol requests, deduplicated across UI reruns."""
    def __init__(self,root):
        self.root=Path(root)
        self._lock=threading.Lock()
        self._pending={}
        self._attempt={}
        self._thread=None
        self._retry_at=0.

    def request(self,symbols,target,*,bulk=False):
        if target is None or market_phase()!="closed" or os.getenv("EXITPLAN_SSI_AUTO","1")=="0":return
        if not os.getenv("SSI_API_KEY") or not os.getenv("SSI_API_SECRET"):return
        with self._lock:
            now=time.monotonic()
            if now<self._retry_at:return
            self._attempt={k:v for k,v in self._attempt.items() if k[1]==target}
            self._pending={k:v for k,v in self._pending.items() if k[1]==target}
            for sym in dict.fromkeys(symbols):
                key=(sym,target)
                if key in self._attempt and now-self._attempt[key]<300:continue
                if key in self._pending:
                    if not bulk:self._pending[key]=True
                    continue
                if len(self._pending)>=48:
                    if bulk:break
                    discard=next((k for k,v in reversed(self._pending.items()) if not v),None)
                    if discard is None:break
                    self._pending.pop(discard)
                self._pending[key]=not bulk
            if self._pending and (self._thread is None or not self._thread.is_alive()):
                self._thread=threading.Thread(target=self._run,daemon=True,name="exitplan-ssi-close")
                self._thread.start()

    def _run(self):
        client=None
        try:
            client=SSIReadOnlyClient()
            while market_phase()=="closed":
                with self._lock:
                    if not self._pending:
                        self._thread=None
                        return
                    key=next((k for k,v in self._pending.items() if v),next(iter(self._pending)))
                    sym,target=key
                    self._pending.pop(key)
                    self._attempt[(sym,target)]=time.monotonic()
                if completed_date()!=target:continue
                try:
                    try:
                        records=client.ohlc_daily(sym,target,target,wait=.5)
                    except SSIAuthError as exc:
                        if "401" not in str(exc):raise
                        client.authenticate()
                        records=client.ohlc_daily(sym,target,target,wait=.5)
                    if records:
                        frame=normalize_ohlc(records)
                        frame=frame[frame.symbol.eq(sym)&frame.tradingDate.eq(pd.Timestamp(target))]
                        if not frame.empty:self._save(frame)
                except (SSIBadRequest,SSISymbolNotFound):
                    # A missing/unsupported ticker must not block all other symbols.
                    pass
                except Exception:
                    # No secret/payload logging; a later UI poll can retry.
                    with self._lock:
                        for key in self._pending:self._attempt[key]=time.monotonic()
                        self._pending.clear()
                        self._retry_at=time.monotonic()+300
                    return
                time.sleep(1.)
        finally:
            if client is not None:client.session.close()

    def _save(self,frame):
        path=self.root/CLOSE_FILE
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            old=pd.read_parquet(path)
            if set(old.source)!={"ssi_fastconnect_v3"} or set(old.data_kind)!={"historical"}:
                raise ValueError("Invalid saved close source")
            frame=pd.concat([old,frame],ignore_index=True)
        frame=frame.drop_duplicates(["symbol","tradingDate"],keep="last").sort_values(["symbol","tradingDate"])
        tmp=path.with_suffix(".parquet.tmp")
        frame.to_parquet(tmp,index=False)
        os.replace(tmp,path)
