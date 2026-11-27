"""Local single-process dashboard market-data worker. No trading, no Streamlit calls.

One 60-second recording batch at a time, reusing the authenticated token until
a failed connection. Completed raw files are retained; imports use the existing
validated pipeline and atomic append. The worker stops at a session boundary.
"""
from __future__ import annotations
import asyncio
from datetime import datetime, timedelta, timezone
import math
import os
from pathlib import Path
import threading
import time

import pandas as pd
from scripts.record_ssi_v3_ws import capture
from scripts.import_ssi_ws import main as import_capture
from scripts.ssi_market_history import select_catalog
from src.analytics.ssi_history_stats import HOLIDAYS_2026
from src.ingest.ssi_books import session
from src.ingest.ssi_fastconnect_v3 import SSIReadOnlyClient

VN=timezone(timedelta(hours=7))
BOARDS=["HOSE","HNX","UPCOM"]
FACTORS=("quote_price_factor","trade_price_factor","volume_factor","history_volume_factor")


def market_window_seconds(now):
    """Only the project's verified 2026 continuous-session windows."""
    now=pd.Timestamp(now)
    now=now.tz_localize("Asia/Ho_Chi_Minh") if now.tzinfo is None else now.tz_convert("Asia/Ho_Chi_Minh")
    if now.year!=2026 or now.tz_localize(None).normalize() in HOLIDAYS_2026:
        return 0.
    current=session(now)
    if current is None:return 0.
    end=now.normalize()+pd.Timedelta(hours=11,minutes=30) if current[1]=="AM" else now.normalize()+pd.Timedelta(hours=14,minutes=30)
    return max(0.,(end-now).total_seconds())


def stored_factors(path):
    """Reuse the operator's existing unit settings; do not silently assume new units."""
    d=pd.read_parquet(path,columns=["source","data_kind",*FACTORS])
    if d.empty or set(d.source)!={"ssi_fastconnect_v3_ws"} or set(d.data_kind)!={"live"}:
        raise ValueError("Cần file snapshot SSI hợp lệ để lấy hệ số quy đổi.")
    result={}
    for key in FACTORS:
        values=d[key].unique()
        if len(values)!=1 or not math.isfinite(float(values[0])) or float(values[0])<=0:
            raise ValueError("Hệ số quy đổi chưa nhất quán.")
        result[key]=float(values[0])
    return result


class DashboardLive:
    """One shared worker per local Streamlit server; status is thread-safe."""
    def __init__(self,root):
        self.root=Path(root).resolve()
        self._lock=threading.Lock()
        self._stop=threading.Event()
        self._thread=None
        self._auto_retry_at=0.
        self._last_view=time.monotonic()
        self._automatic=False
        self._status={"state":"idle","last_event_vn":None,"last_snapshot_vn":None,
                      "published_batches":0,"batch_records":0,"rest_verified":False}

    def _update(self,**kwargs):
        with self._lock:self._status.update(kwargs)

    def snapshot(self):
        with self._lock:
            info=dict(self._status)
            info["active"]=self._thread is not None and self._thread.is_alive()
        return info

    def auto_tick(self,now=None):
        """Called by the visible UI fragment; do not start a second worker."""
        self._last_view=time.monotonic()
        if os.getenv("EXITPLAN_SSI_AUTO","1")=="0":
            if self.snapshot()["active"]:self.stop()
            return False
        if market_window_seconds(now or datetime.now(VN))<2:return False
        if self.snapshot()["active"] or time.monotonic()<self._auto_retry_at:return False
        return self.start(automatic=True)

    def start(self,*,automatic=False):
        with self._lock:
            if self._thread is not None and self._thread.is_alive():return False
            self._stop=threading.Event()
            self._automatic=automatic
            self._auto_retry_at=time.monotonic()+120
            self._status=dict(state="authenticating",last_event_vn=None,last_snapshot_vn=None,
                              published_batches=0,batch_records=0,rest_verified=False)
            self._thread=threading.Thread(target=self._run,daemon=True,name="exitplan-ssi-live")
            self._thread.start()
            return True

    def stop(self):
        self._stop.set()
        with self._lock:
            if self._thread is not None and self._thread.is_alive():self._status["state"]="stopping"

    def _capture_status(self,payload):
        if self._stop.is_set():return
        state=payload.get("state")
        if state in ("stopped","stopped_no_data"):return
        self._update(state=state,batch_records=payload.get("records",0),
                     last_event_vn=payload.get("last_event_vn"))

    def _run(self):
        client=None
        try:
            if not os.getenv("SSI_API_KEY") or not os.getenv("SSI_API_SECRET"):
                self._update(state="missing_credentials")
                return
            client=SSIReadOnlyClient()
            client.authenticate()
            self._update(rest_verified=True)
            if self._stop.is_set():
                self._update(state="stopped")
                return
            if market_window_seconds(datetime.now(VN))<=0:
                self._update(state="outside_hours")
                return
            path=self.root/"data/processed/ssi_book_snapshots.parquet"
            factors=stored_factors(path)
            catalog=pd.read_parquet(self.root/"data/processed/ssi_securities.parquet")
            symbols=select_catalog(catalog,BOARDS)
            if not symbols:raise ValueError("Danh mục SSI trống")
            deadline=time.monotonic()+90*60
            failures=0
            published=0
            while not self._stop.is_set():
                if self._automatic and time.monotonic()-self._last_view>90:break
                seconds=min(60.,deadline-time.monotonic(),market_window_seconds(datetime.now(VN)))
                if seconds<2:break
                raw=self.root/"data/raw/ssi_ws"/(datetime.now(VN).strftime("%Y%m%d_%H%M%S_%f")+"_dashboard.jsonl")
                self._update(state="connecting",batch_records=0,last_event_vn=None)
                code=1
                try:
                    code=asyncio.run(capture(client._token,symbols,seconds/60,BOARDS,50,
                        output_path=raw,status_file=self.root/"outputs/tables/ssi_dashboard_recorder_status.json",
                        stop_event=self._stop,on_status=self._capture_status))
                except Exception:
                    # Never expose authentication headers or raw server payloads.
                    code=1
                imported=False
                if raw.is_file() and raw.stat().st_size:
                    self._update(state="importing")
                    args=["--all-market","--append","--input",str(raw)]
                    for key,value in factors.items():
                        args.extend(["--"+key.replace("_","-"),str(value)])
                    try:
                        imported=import_capture(args,backup=published==0)==0
                    except (Exception,SystemExit):
                        imported=False
                    if imported:
                        published+=1
                        dates=pd.read_parquet(path,columns=["ts_vn"])
                        self._update(published_batches=published,last_snapshot_vn=str(dates.ts_vn.max()))
                if self._stop.is_set():break
                if code==0 and imported:
                    failures=0
                    continue
                failures+=1
                self._update(state="retrying",last_event_vn=None)
                if failures>=3:
                    self._update(state="error")
                    return
                if self._stop.wait(5*failures):break
                if market_window_seconds(datetime.now(VN))<=0:break
                if code!=0:
                    client.authenticate()
                    self._update(rest_verified=True)
            self._update(state="stopped" if self._stop.is_set() or market_window_seconds(datetime.now(VN))>0 else "outside_hours")
        except Exception:
            self._update(state="stopped" if self._stop.is_set() else "error")
        finally:
            self._auto_retry_at=time.monotonic()+120 if self._status.get("state") in ("error","missing_credentials") else 0.
            if client is not None:client.session.close()
