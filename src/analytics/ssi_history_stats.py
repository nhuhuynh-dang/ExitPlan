"""Point-in-time ADV20 from official historical daily bars, never from partial WS volume."""
import pandas as pd
import numpy as np

def asof_history_stats(history, snapshot_date=None, window=20):
    required={"source","data_kind","symbol","tradingDate","close","volume"}
    if not required.issubset(history.columns):
        raise ValueError("Thiếu cột lịch sử SSI")
    if set(history["source"]) != {"ssi_fastconnect_v3"} or set(history["data_kind"]) != {"historical"}:
        raise ValueError("Chỉ chấp nhận OHLCV SSI FastConnect V3")
    d=history.copy()
    d["tradingDate"]=pd.to_datetime(d["tradingDate"],errors="coerce")
    if d["tradingDate"].isna().any():
        raise ValueError("Ngày lịch sử không hợp lệ")
    if snapshot_date is not None:
        d=d[d["tradingDate"].dt.date < pd.Timestamp(snapshot_date).date()]
    if d.duplicated(["symbol","tradingDate"]).any():
        raise ValueError("Lịch sử trùng phiên")
    rows=[]
    for sym,g in d.groupby("symbol"):
        g=g.sort_values("tradingDate").tail(window+1)
        v=pd.to_numeric(g["volume"],errors="coerce").tail(window)
        p=pd.to_numeric(g["close"],errors="coerce")
        adv=v.mean() if len(v)==window and np.isfinite(v).all() and (v>=0).all() else np.nan
        sigma=p.pct_change(fill_method=None).tail(window).std(ddof=1) if len(p)==window+1 and np.isfinite(p).all() and (p>0).all() else np.nan
        rows.append(dict(symbol=sym,adv=adv,sigma=sigma,n_sessions=len(v),
            source="ssi_fastconnect_v3",data_kind="historical",adv_window=window,
            asof_date=str(g["tradingDate"].max().date()),volume_note="OHLCV daily, raw SSI volume; verify shares before use"))
    return pd.DataFrame(rows,columns=["symbol","adv","sigma","n_sessions","source","data_kind","adv_window","asof_date","volume_note"])
