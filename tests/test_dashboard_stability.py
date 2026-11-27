"""Regression tests for daily supplements, waterfall and throttled updates."""
from datetime import date
import pandas as pd
import pytest
from src.app import pages, charts
from src.analytics.ssi_history_stats import expected_sessions
from src.ingest import ssi_dashboard_close as close
from src.finance.engine import Quote
from src.analytics.planner import calculate


def daily(symbol,day,price=20000.,volume=1000.):
    return dict(symbol=symbol,tradingDate=pd.Timestamp(day),close=price,volume=volume,
                source="ssi_fastconnect_v3",data_kind="historical")


def test_daily_supplement_respects_base_and_snapshot_date(tmp_path):
    folder=tmp_path/"data/processed"
    folder.mkdir(parents=True)
    asof=date(2026,11,30)
    days=expected_sessions(asof)
    base=pd.DataFrame([daily("HPG",d) for d in days[:-1]])
    path=folder/"ssi_history.parquet"
    base.to_parquet(path,index=False)
    before=path.read_bytes()
    assert pages._ssi_stats(tmp_path,asof,{"HPG"}).quality_status.iloc[0]=="stale"
    extra=pd.DataFrame([daily("HPG",days[-2],price=99999),
                        daily("HPG",days[-1],price=20100),
                        daily("HPG",asof,price=99999)])
    extra.to_parquet(tmp_path/close.CLOSE_FILE,index=False)
    merged=pages._daily_history(tmp_path)
    assert merged.loc[merged.tradingDate.eq(days[-2]),"close"].iloc[0]==20000
    stats=pages._ssi_stats(tmp_path,asof,{"HPG"})
    assert stats.quality_status.iloc[0]=="complete"
    assert stats.adv.iloc[0]==1000
    assert stats.asof_date.iloc[0]==str(days[-1].date())
    assert path.read_bytes()==before


def test_missing_daily_symbols_requires_valid_ohlcv():
    d=pd.DataFrame([daily("HPG","2026-11-27"),daily("ACB","2026-11-26"),
                    daily("VPB","2026-11-27",volume=float("nan"))])
    assert close.missing_daily_symbols(d,["HPG","VPB","ACB","FPT"],date(2026,11,27))==["ACB","FPT","VPB"]


def test_daily_merge_rejects_other_source():
    d=pd.DataFrame([daily("HPG","2026-11-27")])
    with pytest.raises(ValueError):close.merge_daily_history(d,d.assign(source="other"))


@pytest.mark.parametrize("bid",[9950.,10050.])
def test_waterfall_reconciles_signed_execution_difference(bid):
    q=Quote("HPG",10000.,((bid,1000),))
    plan=calculate({"HPG":1000},{"HPG":q},5000000,.5,.0015,.001)["B"]
    trace=charts.waterfall_fig(plan,charts.apply_palette("Sáng","#2563EB")).data[0]
    ref=sum(d["sold"]*d["last"] for d in plan["details"])
    assert trace.y[0]==ref
    assert trace.y[1]==pytest.approx(plan["gross"]-ref)
    assert sum(trace.y[:4])==pytest.approx(plan["net"])
    assert (trace.y[1]>0)==(bid>10000)
    assert plan["cost"]>=0


def test_close_worker_global_backoff_and_priority(tmp_path,monkeypatch):
    monkeypatch.setenv("EXITPLAN_SSI_AUTO","1")
    monkeypatch.setenv("SSI_API_KEY","test")
    monkeypatch.setenv("SSI_API_SECRET","test")
    monkeypatch.setattr(close,"market_phase",lambda:"closed")
    worker=close.CloseWorker(tmp_path)
    class Active:
        def is_alive(self):return True
    worker._thread=Active()
    target=date(2026,11,27)
    worker.request(["HPG","ACB"],target,bulk=True)
    worker.request(["VPB","ACB"],target)
    assert worker._pending=={("HPG",target):False,("ACB",target):True,("VPB",target):True}
    worker._retry_at=float("inf")
    worker.request(["TCB"],target)
    assert ("TCB",target) not in worker._pending
