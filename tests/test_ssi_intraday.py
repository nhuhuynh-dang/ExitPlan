"""Offline regression tests for minute history; no credentials or real API."""
from datetime import date
import pytest
from scripts.ssi_intraday_history import normalize_minutes, fetch_day
from src.ingest.ssi_fastconnect_v3 import SSIResponseError

DAY=date(2026,11,26)

def candle(stamp, close="19800"):
    return dict(symbol="HPG", tradingDate=stamp, open="19800", high="19900",
                low="19700", close=close, volume="1200")

def test_minute_timestamps_preserved_and_exact_duplicates_removed():
    a=candle("2026/11/26 09:15:00")
    b=candle("2026/11/26 09:16:00")
    d=normalize_minutes([b,a,a],"HPG",DAY)
    assert len(d)==2
    assert str(d.ts_vn.dt.tz)=="Asia/Ho_Chi_Minh"
    assert d.ts_vn.dt.minute.tolist()==[15,16]
    assert set(d.data_kind)=={"historical_intraday"}

@pytest.mark.parametrize("rows",[
    [candle("2026-11-26")],
    [candle("2026-11-26 09:15:00"),candle("2026-11-26 09:15:00","19850")],
    [candle("2026-11-25 09:15:00")],
    [candle("2026-11-26 09:15:00","99999")],
])
def test_invalid_minutes_rejected(rows):
    with pytest.raises(SSIResponseError):
        normalize_minutes(rows,"HPG",DAY)

def test_pagination_follows_server_size(monkeypatch):
    monkeypatch.setattr("scripts.ssi_intraday_history.time.sleep",lambda _:None)
    class Client:
        def _get(self, endpoint, params):
            assert endpoint=="/api/v3/data/ohlc"
            assert params["timeFrame"]=="1m"
            page=params["pageIndex"]
            return dict(pageSize=1,data=[candle(f"2026-11-26 09:{14+page}:00")] if page<3 else [])
    assert len(fetch_day(Client(),"HPG",DAY))==2

def test_repeated_page_rejected(monkeypatch):
    monkeypatch.setattr("scripts.ssi_intraday_history.time.sleep",lambda _:None)
    class Client:
        def _get(self, endpoint, params):
            return dict(pageSize=1,data=[candle("2026-11-26 09:15:00")])
    with pytest.raises(SSIResponseError,match="Repeated"):
        fetch_day(Client(),"HPG",DAY)
