"""Point-in-time SSI daily liquidity metrics. No imputation or future observations.

2026 scheduled closures: HOSE 2294/TB-SGDHCM (09/12/2025),
HNX 5305/TB-SGDHN (03/12/2025), VSDC 1517/SGDVN-THHC update for 02/01,
HOSE 2215/TB-SGDHCM (11/11/2026) and HNX 4892/TB-SGDHN for 24/11.
Sources:
https://www.hsx.vn/vi/tin-tuc/hose-thong-bao-lich-nghi-giao-dich-nam-2026/2437411
https://vpdt.hnx.vn/vi-vn/chi-tiet-lich-nghi-gd-60023839.html?_page=1
https://vsdc.vn/vi/ad/198399
https://www.bsc.com.vn/tin-tuc/tin-chi-tiet/107351-thong-bao-lich-nghi-giao-dich-ngay-van-hoa-viet-nam-2026/
"""
import pandas as pd
import numpy as np

HOLIDAYS_2026 = pd.DatetimeIndex(pd.to_datetime([
    "2026-01-01","2026-01-02","2026-02-16","2026-02-17","2026-02-18",
    "2026-02-19","2026-02-20","2026-04-27","2026-04-30","2026-05-01",
    "2026-08-31","2026-09-01","2026-09-02","2026-11-24"
]))

def expected_sessions(asof, count=21):
    """Scheduled VN sessions strictly before asof; None outside supported window."""
    day=pd.Timestamp(asof).normalize()
    if day.tzinfo is not None:
        day=day.tz_localize(None)
    if not pd.Timestamp("2026-01-01") < day <= pd.Timestamp("2027-01-01"):
        return None
    dates=pd.bdate_range("2026-01-01",day-pd.Timedelta(days=1)).difference(HOLIDAYS_2026)
    return dates[-count:] if len(dates)>=count else None

def asof_history_stats(history, snapshot_date=None, window=20, strict_calendar=False):
    """Legacy observation mode is explicit in metadata; strict mode requires calendar."""
    required={"source","data_kind","symbol","tradingDate","close","volume"}
    if not required.issubset(history.columns):
        raise ValueError("Thiếu cột lịch sử SSI")
    if set(history["source"]) != {"ssi_fastconnect_v3"} or set(history["data_kind"]) != {"historical"}:
        raise ValueError("Chỉ chấp nhận OHLCV SSI FastConnect V3")
    d=history.copy()
    d["tradingDate"]=pd.to_datetime(d["tradingDate"],errors="coerce").dt.normalize()
    if d["tradingDate"].isna().any():
        raise ValueError("Ngày lịch sử không hợp lệ")
    if snapshot_date is None and not d.empty:
        snapshot_date=d["tradingDate"].max()+pd.Timedelta(days=1)
    if snapshot_date is not None:
        d=d[d["tradingDate"].dt.date < pd.Timestamp(snapshot_date).date()]
    if d.duplicated(["symbol","tradingDate"]).any():
        raise ValueError("Lịch sử trùng phiên")
    expected=expected_sessions(snapshot_date,window+1) if strict_calendar and snapshot_date is not None else None
    rows=[]
    for sym,g in d.groupby("symbol"):
        g=g.sort_values("tradingDate")
        latest=g["tradingDate"].max()
        actual=g.set_index("tradingDate")
        missing=[]
        if strict_calendar and expected is not None:
            missing=expected.difference(actual.index)
            aligned=actual.reindex(expected)
            v=pd.to_numeric(aligned["volume"],errors="coerce").tail(window)
            p=pd.to_numeric(aligned["close"],errors="coerce")
            n=int(expected[-window:].isin(actual.index).sum())
            status="stale" if latest<expected[-1] else ("missing_sessions" if len(missing) else "complete")
        elif strict_calendar:
            v=pd.Series(dtype=float); p=pd.Series(dtype=float)
            n=0; status="calendar_unavailable"
        else:
            tail=g.tail(window+1)
            v=pd.to_numeric(tail["volume"],errors="coerce").tail(window)
            p=pd.to_numeric(tail["close"],errors="coerce")
            n=len(v); status="observations_only"
        adv=v.mean() if len(v)==window and np.isfinite(v).all() and (v>=0).all() else np.nan
        sigma=p.pct_change(fill_method=None).tail(window).std(ddof=1) if len(p)==window+1 and np.isfinite(p).all() and (p>0).all() else np.nan
        if status=="complete" and (not np.isfinite(adv) or not np.isfinite(sigma)):
            status="invalid_values"
        rows.append(dict(symbol=sym,adv=adv,sigma=sigma,n_sessions=n,
            source="ssi_fastconnect_v3",data_kind="historical",adv_window=window,
            asof_date=str(latest.date()),volume_note="OHLCV daily, raw SSI volume; verify shares before use",
            quality_status=status,expected_last_session=str(expected[-1].date()) if expected is not None else "",
            missing_sessions=",".join(str(x.date()) for x in missing),missing_session_count=len(missing) if expected is not None else None,
            calendar_scope="VN scheduled sessions 2026" if strict_calendar else "unverified observed dates"))
    return pd.DataFrame(rows,columns=["symbol","adv","sigma","n_sessions","source","data_kind","adv_window","asof_date","volume_note","quality_status","expected_last_session","missing_sessions","missing_session_count","calendar_scope"])
