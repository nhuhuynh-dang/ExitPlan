"""Offline fixtures are invented ONLY for software tests, never stored as market observations."""
import pandas as pd
from src.ingest.ssi_books import build_snapshots
from src.analytics.ssi_history_stats import asof_history_stats

SYMS=["HPG","ACB"]
def event(sym,kind,second=0,exchange_second=None):
    sec=second if exchange_second is None else exchange_second
    d={"s":sym,"t":f"2026/11/27 09:30:{sec:02d}"}
    if kind=="quote":
        d.update(bids=[["25.00","1000"],["24.95","2000"],["24.90","3000"]],
                 asks=[["25.05","1000"],["25.10","2000"],["25.15","3000"]])
    else:
        d.update(p="25000",v="100000")
    return dict(source="ssi_fastconnect_v3_ws",symbol=sym,event=kind,
                received_at=f"2026-11-27T09:30:{second:02d}+07:00",data=d)

def build(events, factor=1000):
    return build_snapshots(events,SYMS,quote_price_factor=factor,trade_price_factor=1,volume_factor=1)

def events():
    return [event("HPG","trade",0),event("ACB","trade",0),
            event("HPG","quote",1),event("ACB","quote",2)]

def test_synchronized_book_and_explicit_unit():
    b,qa=build(events())
    assert len(b)==2 and b.ts_vn.nunique()==1
    assert set(b.symbol)==set(SYMS)
    assert b.bidPrice1.eq(25000).all()
    assert b.bidVol3.eq(3000).all()
    assert b.quote_age_seconds.max()==1
    assert qa["aligned_snapshots"]==1

def test_missing_symbol_no_snapshot():
    b,_=build(events()[:-1])
    assert b.empty

def test_wrong_unit_no_snapshot():
    b,q=build(events(),factor=1)
    assert b.empty and q["price_scale_or_stale"]>0

def test_stale_quote_no_snapshot():
    e=events()
    e[-1]=event("ACB","quote",15)
    b,_=build(e)
    assert b.empty

def test_incomplete_book_rejected():
    e=events()
    e[-1]["data"]["bids"].pop()
    b,q=build(e)
    assert b.empty and q["invalid_quote"]==1

def test_invalid_update_invalidates_old_quote():
    e=events()
    e[-2]["data"]["bids"].pop()
    e.insert(2,event("HPG","quote",0))
    b,q=build(e)
    assert b.empty and q["invalid_quote"]==1

def test_history_excludes_current_and_future_day():
    dates=pd.bdate_range(end="2026-11-30",periods=25)
    h=pd.DataFrame(dict(symbol="HPG",tradingDate=dates,close=range(100,125),
                        volume=1000,source="ssi_fastconnect_v3",data_kind="historical"))
    h.loc[h.tradingDate>=pd.Timestamp("2026-11-27"),"volume"]=9999999
    s=asof_history_stats(h,"2026-11-27").iloc[0]
    assert s.adv==1000 and s.n_sessions==20
    assert s.asof_date=="2026-11-26" and s.sigma>=0

def test_history_short_sample_no_adv():
    h=pd.DataFrame(dict(symbol=["HPG"],tradingDate=["2026-11-26"],close=[25],volume=[100],
                        source=["ssi_fastconnect_v3"],data_kind=["historical"]))
    s=asof_history_stats(h).iloc[0]
    assert pd.isna(s.adv) and pd.isna(s.sigma)


def test_market_mode_does_not_require_all_symbols():
    b,qa=build_snapshots(events()[:-1],SYMS+["VNM"],
                          quote_price_factor=1000,trade_price_factor=1,
                          volume_factor=1,require_all=False)
    assert set(b.symbol)=={"HPG"} and qa["aligned_snapshots"]==1


def test_portfolio_uses_latest_shared_time_not_latest_per_symbol():
    from src.data.repository import portfolio_snapshot
    b,_=build(events())
    newer=b.iloc[[0]].copy()
    newer["ts_vn"]=newer.ts_vn+pd.Timedelta(seconds=10)
    mixed=pd.concat([b,newer],ignore_index=True)
    selected=portfolio_snapshot(mixed,SYMS)
    assert set(selected.symbol)==set(SYMS)
    assert selected.ts_vn.nunique()==1
    assert selected.ts_vn.iloc[0]==b.ts_vn.iloc[0]


def test_catalog_three_board_selection():
    from scripts.ssi_market_history import select_catalog
    catalog=pd.DataFrame({"symbol":["HPG","ACB","VGI","CW123"],
         "board":["HOSE","HOSE","UPCOM","HOSE"],
         "name":["Hoa Phat","ACB","Viettel Global","Covered warrant"],"source":["ssi_fastconnect_v3"]*4,"stockType":["example-stock"]*3+["example-other"]})
    assert select_catalog(catalog,["HOSE","UPCOM"])==["ACB","HPG","VGI"]
    assert select_catalog(catalog,["HOSE"],["example-stock"])==["ACB","HPG"]
