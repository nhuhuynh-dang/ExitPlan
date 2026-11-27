"""Daily close reference data, strictly separate from recorded order books."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import threading
import time

import pandas as pd
from src.analytics.ssi_history_stats import HOLIDAYS_2026, expected_sessions
from src.ingest.ssi_fastconnect_v3 import SSIReadOnlyClient, normalize_ohlc

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


class CloseWorker:
    """Bounded per-symbol requests, deduplicated across UI reruns."""
    def __init__(self,root):
        self.root=Path(root)
        self._lock=threading.Lock()
        self._pending={}
        self._attempt={}
        self._thread=None

    def request(self,symbols,target):
        if target is None or market_phase()!="closed" or os.getenv("EXITPLAN_SSI_AUTO","1")=="0":return
        if not os.getenv("SSI_API_KEY") or not os.getenv("SSI_API_SECRET"):return
        with self._lock:
            now=time.monotonic()
            self._attempt={k:v for k,v in self._attempt.items() if k[1]==target}
            for sym in list(dict.fromkeys(symbols))[:24]:
                key=(sym,target)
                if key not in self._attempt or now-self._attempt[key]>=300:
                    if len(self._pending)<48:self._pending[key]=None
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
                    (sym,target),_=self._pending.popitem()
                    self._attempt[(sym,target)]=time.monotonic()
                if completed_date()!=target:continue
                try:
                    records=client.ohlc_daily(sym,target,target,wait=.5)
                    if records:
                        frame=normalize_ohlc(records)
                        frame=frame[frame.symbol.eq(sym)&frame.tradingDate.eq(pd.Timestamp(target))]
                        if not frame.empty:self._save(frame)
                except Exception:
                    # No secret/payload logging; a later UI poll can retry.
                    with self._lock:
                        for key in self._pending:self._attempt[key]=time.monotonic()
                        self._pending.clear()
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
