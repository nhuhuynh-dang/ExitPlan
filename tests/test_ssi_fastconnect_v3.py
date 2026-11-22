"""Offline tests for official SSI V3 read-only integration. No real API credentials."""
from datetime import date

import pandas as pd
import pytest

from src.ingest.ssi_fastconnect_v3 import (
    SSIAuthError, SSIReadOnlyClient, SSIResponseError, normalize_ohlc,
)
from scripts.ssi_v3_sync import main


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, *, auth_status=200, error_get=None):
        self.auth_status = auth_status
        self.error_get = error_get
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return FakeResponse(self.auth_status, {"accessToken": "mock.jwt.not_real"})

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if self.error_get is not None:
            return FakeResponse(self.error_get, {"code": self.error_get, "msg": "test"})
        if url.endswith("/securitiesByBoard"):
            return FakeResponse(200, [{"symbol": "HPG", "board": "HOSE", "lotSize": "100"}])
        if url.endswith("/ohlc"):
            return FakeResponse(200, {"data": [
                {"symbol": "HPG", "tradingDate": "2026/11/20",
                 "open": "26.2", "high": "27.0", "low": "26.0",
                 "close": "26.7", "volume": "1200000"},
            ], "pageIndex": 1, "pagesCount": 1})
        raise AssertionError("Unexpected test endpoint: " + url)


def _client(session):
    return SSIReadOnlyClient(session=session, api_key="fake_key", api_secret="fake_secret")


def test_read_only_client_token_then_catalog_and_ohlc():
    session = FakeSession()
    client = _client(session)
    assert client.securities_by_board("HOSE")[0]["symbol"] == "HPG"
    rows = client.ohlc_daily("HPG", date(2026, 11, 1), date(2026, 11, 20), wait=0)
    assert len(rows) == 1
    assert session.calls[0][1] == "https://api.ssi.com.vn/api/v3/auth/token"
    assert session.calls[0][2]["json"] == {"apiKey": "fake_key", "apiSecret": "fake_secret"}
    assert session.calls[1][1] == "https://api.ssi.com.vn/api/v3/data/securitiesByBoard"
    assert session.calls[-1][2]["params"]["timeFrame"] == "1d"
    assert session.calls[-1][2]["params"]["from"] == "2026/11/01"
    assert session.calls[-1][2]["params"]["pageIndex"] == 1
    assert not any("/trade/" in path.lower() for _, path, _ in session.calls)


def test_auth_missing_never_makes_network_request():
    session = FakeSession()
    client = SSIReadOnlyClient(session=session, api_key="", api_secret="")
    with pytest.raises(SSIAuthError, match="Chưa có SSI_API_KEY"):
        client.authenticate()
    assert session.calls == []


def test_http_403_and_429_do_not_fabricate_prices():
    for status in (403, 429):
        session = FakeSession(error_get=status)
        client = _client(session)
        with pytest.raises((SSIAuthError, SSIResponseError)):
            client.ohlc_daily("HPG", date(2026, 11, 1), date(2026, 11, 20), wait=0)
        assert len(session.calls) == 2


def test_ohlcv_source_labels_and_no_bid_columns():
    rows = _client(FakeSession()).ohlc_daily(
        "HPG", date(2026, 11, 1), date(2026, 11, 20), wait=0
    )
    result = normalize_ohlc(rows)
    assert result["source"].unique().tolist() == ["ssi_fastconnect_v3"]
    assert result["data_kind"].unique().tolist() == ["historical"]
    assert result["volume"].iloc[0] == 1_200_000
    assert pd.Timestamp("2026-11-20") == result["tradingDate"].iloc[0]
    assert all(col not in result for col in ("bidPrice1", "bidVol1", "askPrice1"))


def test_invalid_ohlcv_never_returns_fake_candles():
    with pytest.raises(SSIResponseError):
        normalize_ohlc([])
    with pytest.raises(SSIResponseError):
        normalize_ohlc([{"symbol": "HPG", "close": "2"}])


def test_cli_without_keys_exits_before_network_or_writing(tmp_path, monkeypatch):
    monkeypatch.delenv("SSI_API_KEY", raising=False)
    monkeypatch.delenv("SSI_API_SECRET", raising=False)
    monkeypatch.chdir(tmp_path)
    assert main(["--check"]) == 2
    assert list(tmp_path.iterdir()) == []
