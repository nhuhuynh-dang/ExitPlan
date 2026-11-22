"""SSI FastConnect V3 read-only Market Data client for ExitPlan.

Official endpoints (no trading/OTP support):
  POST /api/v3/auth/token
  GET  /api/v3/data/securitiesByBoard
  GET  /api/v3/data/ohlc
  GET  /api/v3/data/securitiesSummary

Credentials are read from process environment, NEVER sent to the dashboard
or persisted in parquet/CSV. Historical OHLCV is not a bid/ask order book.
"""
from __future__ import annotations

from datetime import date
import os
import re
import time

import pandas as pd
import requests

BASE_URL = "https://api.ssi.com.vn"
ALLOWED_BOARDS = ("HOSE", "HNX", "UPCOM")
_SYMBOL = re.compile(r"^[A-Z0-9]{1,12}$")
_SOURCE = "ssi_fastconnect_v3"
_HISTORY_COLUMNS = ("symbol", "tradingDate", "open", "high", "low", "close", "volume")


class SSIAuthError(RuntimeError):
    """Missing authorization or denied read-only API permissions."""


class SSIResponseError(RuntimeError):
    """Malformed/missing data or market API error (without secret payloads)."""


def _validate_symbol(symbol: str) -> str:
    val = str(symbol).strip().upper()
    if not _SYMBOL.fullmatch(val):
        raise ValueError("Mã cổ phiếu không hợp lệ")
    return val


def _format_date(value: date) -> str:
    if not isinstance(value, date):
        raise TypeError("Ngày phải có kiểu datetime.date")
    return value.strftime("%Y/%m/%d")


class SSIReadOnlyClient:
    def __init__(self, *, session=None, api_key=None, api_secret=None, timeout=20):
        self.session = session if session is not None else requests.Session()
        self.api_key = api_key if api_key is not None else os.getenv("SSI_API_KEY", "")
        self.api_secret = api_secret if api_secret is not None else os.getenv("SSI_API_SECRET", "")
        self.timeout = timeout
        self._token = None
        # Explicitly FIXED to SSI official HTTPS host; never accept a login URL from data.
        self.base_url = BASE_URL

    def authenticate(self):
        if not self.api_key or not self.api_secret:
            raise SSIAuthError(
                "Chưa có SSI_API_KEY/SSI_API_SECRET. Chờ SSI cấp quyền và đặt "
                "biến môi trường trên máy cá nhân, không commit khóa lên GitHub."
            )
        try:
            response = self.session.post(
                self.base_url + "/api/v3/auth/token",
                json={"apiKey": self.api_key, "apiSecret": self.api_secret},
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise SSIAuthError("Không kết nối được máy chủ xác thực SSI qua HTTPS.") from exc
        if response.status_code != 200:
            raise SSIAuthError(
                "SSI từ chối cấp token (HTTP %d). Kiểm tra quyền Market Data, "
                "trạng thái kích hoạt và cặp key/secret." % response.status_code
            )
        try:
            body = response.json()
        except ValueError as exc:
            raise SSIAuthError("SSI trả về phản hồi xác thực không phải JSON.") from exc
        if not isinstance(body, dict) or not isinstance(body.get("accessToken"), str) or not body["accessToken"]:
            raise SSIAuthError("Không tìm thấy accessToken trong phản hồi SSI.")
        self._token = body["accessToken"]
        return True

    def _get(self, endpoint, params):
        if self._token is None:
            self.authenticate()
        if endpoint not in (
            "/api/v3/data/securitiesByBoard",
            "/api/v3/data/ohlc",
            "/api/v3/data/securitiesSummary",
        ):
            raise ValueError("Chỉ hỗ trợ các endpoint Market Data chỉ đọc.")
        try:
            resp = self.session.get(
                self.base_url + endpoint,
                params=params,
                headers={"Accept": "application/json", "Authorization": "Bearer " + self._token},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise SSIResponseError("Không kết nối được SSI Market Data.") from exc
        if resp.status_code == 401:
            raise SSIAuthError("Token SSI hết hạn hoặc không hợp lệ (401). Chạy lại script.")
        if resp.status_code == 403:
            raise SSIAuthError("SSI chưa cấp quyền đọc Market Data (403).")
        if resp.status_code == 429:
            raise SSIResponseError("SSI giới hạn tần suất (429). Không tự động gửi dồn request.")
        if resp.status_code != 200:
            raise SSIResponseError("SSI Market Data trả lỗi HTTP %d (%s)." % (resp.status_code, endpoint))
        try:
            body = resp.json()
        except ValueError as exc:
            raise SSIResponseError("SSI trả về dữ liệu không phải JSON (%s)." % endpoint) from exc
        if isinstance(body, dict) and body.get("code") not in (None, 0, "0", "SUCCESS", 200):
            raise SSIResponseError("SSI thông báo lỗi ở %s; kiểm tra quyền và tham số." % endpoint)
        return body

    def securities_by_board(self, board: str) -> list[dict]:
        board = str(board).strip().upper()
        if board not in ALLOWED_BOARDS:
            raise ValueError("Sàn phải thuộc HOSE, HNX hoặc UPCOM.")
        payload = self._get("/api/v3/data/securitiesByBoard", {"board": board})
        records = payload if isinstance(payload, list) else payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(records, list):
            raise SSIResponseError("SSI trả về danh sách chứng khoán sai cấu trúc.")
        return [row for row in records if isinstance(row, dict) and _SYMBOL.fullmatch(str(row.get("symbol", "")).upper())]

    def ohlc_daily(self, symbol: str, start: date, end: date,
                   *, page_size=200, max_pages=30, wait=0.25) -> list[dict]:
        sym = _validate_symbol(symbol)
        if start > end:
            raise ValueError("Ngày bắt đầu không được sau ngày kết thúc.")
        if not 1 <= page_size <= 500 or not 1 <= max_pages <= 200:
            raise ValueError("Giới hạn phân trang không hợp lệ.")
        rows = []
        last_page_fingerprint = None
        for page in range(1, max_pages + 1):
            body = self._get("/api/v3/data/ohlc", {
                "symbol": sym, "from": _format_date(start), "to": _format_date(end),
                "timeFrame": "1d", "pageIndex": page, "pageSize": page_size,
            })
            part = body.get("data") if isinstance(body, dict) else None
            if not isinstance(part, list):
                raise SSIResponseError("SSI OHLC không chứa danh sách data.")
            if not part:
                break
            fingerprint = (
                len(part), str(part[0].get("tradingDate")) if isinstance(part[0], dict) else "",
                str(part[-1].get("tradingDate")) if isinstance(part[-1], dict) else ""
            )
            if fingerprint == last_page_fingerprint:
                raise SSIResponseError("Trang dữ liệu SSI bị lặp; dừng thay vì tiếp tục ghi dữ liệu sai.")
            last_page_fingerprint = fingerprint
            for entry in part:
                if not isinstance(entry, dict):
                    raise SSIResponseError("Dữ liệu nến SSI có dòng không phải object.")
                # Keep raw API fields, do not fabricate missing values.
                rows.append(dict(entry, symbol=sym))
            count = body.get("pagesCount")
            if isinstance(count, int) and count > 0 and page >= count:
                break
            if len(part) < page_size:
                break
            if page < max_pages:
                time.sleep(wait)
        return rows


def normalize_ohlc(records: list[dict]) -> pd.DataFrame:
    """Normalize ONLY actual rows returned by official SSI V3 daily OHLC API."""
    if not records:
        raise SSIResponseError("SSI OHLC không trả bản ghi. Không tạo dữ liệu giả.")
    data = pd.DataFrame(records)
    missing = set(_HISTORY_COLUMNS) - set(data.columns)
    if missing:
        raise SSIResponseError("Thiếu trường OHLCV chính thức: " + ", ".join(sorted(missing)))
    data = data[list(_HISTORY_COLUMNS)].copy()
    data["symbol"] = data["symbol"].astype(str).str.strip().str.upper()
    # SSI daily API uses YYYY/MM/DD; tolerate its ISO equivalents and timestamps.
    data["tradingDate"] = pd.to_datetime(
        data["tradingDate"].astype(str).str.slice(0, 10).str.replace("/", "-", regex=False),
        format="%Y-%m-%d", errors="coerce"
    )
    for column in ("open", "high", "low", "close", "volume"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=list(_HISTORY_COLUMNS)).copy()
    data = data[
        data["symbol"].str.fullmatch(_SYMBOL)
        & (data["close"] > 0)
        & (data["volume"] >= 0)
        & (data["high"] >= data["low"])
        & (data["high"] >= data[["open", "close"]].max(axis=1))
        & (data["low"] <= data[["open", "close"]].min(axis=1))
    ]
    if data.empty:
        raise SSIResponseError("Dữ liệu OHLCV không có bản ghi hợp lệ sau kiểm tra.")
    data = data.drop_duplicates(["symbol", "tradingDate"], keep="last")
    data = data.sort_values(["symbol", "tradingDate"]).reset_index(drop=True)
    data["source"] = _SOURCE
    data["data_kind"] = "historical"
    # SSI may report prices in thousand VND; preserve raw API units.
    data["price_unit"] = "as_returned_by_ssi_api"
    return data
