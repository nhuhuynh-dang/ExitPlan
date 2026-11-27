"""Offline automatic mode checks, no real SSI calls."""
from datetime import date
import pandas as pd
from src.ingest import ssi_dashboard_live as live
from src.ingest import ssi_dashboard_close as close


def test_market_phase_and_completed_date():
    assert close.market_phase("2026-11-30 10:00")=="continuous"
    assert close.market_phase("2026-11-30 12:00")=="lunch"
    assert close.market_phase("2026-11-30 14:35")=="transition"
    assert close.market_phase("2026-11-30 15:15")=="closed"
    assert close.completed_date("2026-11-30 14:35")==date(2026,11,27)
    assert close.completed_date("2026-11-30 15:15")==date(2026,11,30)
    assert close.completed_date("2026-11-28 10:00")==date(2026,11,27)
    assert close.completed_date("2026-11-24 16:00")==date(2026,11,23)
    assert close.market_phase("2027-01-04 10:00")=="calendar_unknown"


def test_close_refs_keep_dates_and_reject_future_and_wrong_source():
    def row(symbol,day,price,source="ssi_fastconnect_v3"):
        return dict(symbol=symbol,tradingDate=day,close=price,source=source,data_kind="historical")
    history=pd.DataFrame([row("HPG","2026-11-26",20000),
                          row("ACB","2026-11-26",19000),
                          row("HPG","2026-11-30",99999),
                          row("ACB","2026-11-27",99999,"other")])
    extra=pd.DataFrame([row("HPG","2026-11-27",19800)])
    result=close.close_references(history,extra,["HPG","ACB","VPB"],date(2026,11,27))
    assert result["HPG"]==dict(close=19800.,date=date(2026,11,27),current=True)
    assert result["ACB"]==dict(close=19000.,date=date(2026,11,26),current=False)
    assert "VPB" not in result


def test_auto_tick_starts_only_during_window(tmp_path,monkeypatch):
    monkeypatch.setenv("EXITPLAN_SSI_AUTO","1")
    monkeypatch.setenv("SSI_API_KEY","test")
    monkeypatch.setenv("SSI_API_SECRET","test")
    worker=live.DashboardLive(tmp_path)
    calls=[]
    monkeypatch.setattr(worker,"start",lambda **kwargs:calls.append(kwargs) or True)
    assert not worker.auto_tick("2026-11-28 10:00")
    assert not worker.auto_tick("2026-11-30 12:00")
    assert worker.auto_tick("2026-11-30 10:00")
    assert calls==[{"automatic":True}]
    worker._auto_retry_at=float("inf")
    assert not worker.auto_tick("2026-11-30 10:00")
    monkeypatch.setenv("EXITPLAN_SSI_AUTO","0")
    assert not worker.auto_tick("2026-11-30 10:00")


def test_close_cache_does_not_modify_book_or_history(tmp_path):
    worker=close.CloseWorker(tmp_path)
    folder=tmp_path/"data/processed"
    folder.mkdir(parents=True)
    book=folder/"ssi_book_snapshots.parquet"
    history=folder/"ssi_history.parquet"
    book.write_bytes(b"book")
    history.write_bytes(b"history")
    frame=pd.DataFrame([dict(symbol="HPG",tradingDate=pd.Timestamp("2026-11-27"),close=19800.,
                             source="ssi_fastconnect_v3",data_kind="historical")])
    worker._save(frame)
    worker._save(frame.assign(close=19900.))
    saved=pd.read_parquet(tmp_path/close.CLOSE_FILE)
    assert len(saved)==1 and saved.close.iloc[0]==19900.
    assert book.read_bytes()==b"book" and history.read_bytes()==b"history"


def test_no_personal_api_uses_saved_data_without_starting_worker(tmp_path,monkeypatch):
    monkeypatch.setenv("EXITPLAN_SSI_AUTO","1")
    monkeypatch.delenv("SSI_API_KEY",raising=False)
    monkeypatch.delenv("SSI_API_SECRET",raising=False)
    worker=live.DashboardLive(tmp_path)
    def unexpected_start(**kwargs):
        raise AssertionError("Offline user must not start SSI worker")
    monkeypatch.setattr(worker,"start",unexpected_start)
    assert not live.operator_live_enabled()
    assert not worker.auto_tick("2026-11-30 10:00")
    assert worker.snapshot()["state"]=="idle"
