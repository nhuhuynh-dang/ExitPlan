"""Offline regression tests; no SSI requests or production data writes."""
import pandas as pd
import pytest
from scripts.ssi_market_history import ready_history_symbols
from scripts.import_ssi_ws import append_snapshots


def snapshot(symbol, stamp, price=10000, volume_factor=1):
    return dict(symbol=symbol,ts_vn=pd.Timestamp(stamp,tz="Asia/Ho_Chi_Minh"),
                source="ssi_fastconnect_v3_ws",data_kind="live",closePrice=price,
                quote_price_factor=1,trade_price_factor=1,volume_factor=volume_factor,
                history_volume_factor=1)


def test_append_preserves_multiple_dates_and_removes_exact_keys():
    morning=snapshot("HPG","2026-11-27 10:00")
    afternoon=snapshot("HPG","2026-11-27 13:00")
    following=snapshot("ACB","2026-11-30 10:00")
    old=pd.DataFrame([morning,afternoon])
    new=pd.DataFrame([afternoon,following])
    merged=append_snapshots(old,new)
    assert len(merged)==3
    assert merged.ts_vn.dt.date.nunique()==2
    assert set(merged.symbol)=={"HPG","ACB"}
    assert len(append_snapshots(merged,new))==3
    assert len(old)==2


@pytest.mark.parametrize("change",["factor","source"])
def test_append_rejects_incompatible_inputs(change):
    old=pd.DataFrame([snapshot("HPG","2026-11-27 10:00")])
    new=pd.DataFrame([snapshot("HPG","2026-11-27 13:00")])
    if change=="factor":new["volume_factor"]=100
    else:new["data_kind"]="synthetic"
    with pytest.raises(ValueError):append_snapshots(old,new)


def test_history_readiness_requires_21_prior_prices_and_20_valid_volumes():
    dates=pd.bdate_range(end="2026-11-26",periods=21)
    rows=[]
    for sym,days in [("HPG",dates),("ACB",dates[1:]),("VPB",dates)]:
        for i,day in enumerate(days):
            rows.append(dict(symbol=sym,tradingDate=day,close=10000+i*10,
                             volume=1000 if sym!="VPB" else None,
                             source="ssi_fastconnect_v3",data_kind="historical"))
    rows.append(dict(symbol="ACB",tradingDate=pd.Timestamp("2026-11-27"),
                     close=10500,volume=1000,source="ssi_fastconnect_v3",data_kind="historical"))
    assert ready_history_symbols(pd.DataFrame(rows),"2026-11-27")=={"HPG"}
    assert ready_history_symbols(None,"2026-11-27")==set()
