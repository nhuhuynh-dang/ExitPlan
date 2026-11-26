"""Read-only VPBankS NeoAPI diagnostic and REST snapshot capture.

No account/trading endpoints. Credentials prompted locally; no token persisted.
REST captures are stored separately from the planner's processed book.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
from getpass import getpass
import json
from pathlib import Path
import re
import sys

import requests

AUTH = "https://external.vpbanks.com.vn/auth/token"
BASE = "https://neoapi.vpbanks.com.vn/neo-api"
ROOT = Path(__file__).resolve().parents[1]
VN = timezone(timedelta(hours=7))
FIELDS = (
    "symbol", "marketCode", "stockType", "tradingDate", "tradingSession",
    "tradingStatus", "closePrice", "refPrice", "openPrice", "highPrice",
    "lowPrice", "totalTradingVolume", "bidPrice1", "bidPrice2", "bidPrice3",
    "bidVol1", "bidVol2", "bidVol3", "askPrice1", "askPrice2", "askPrice3",
    "askVol1", "askVol2", "askVol3",
)


class NeoError(RuntimeError):
    pass


def response_data(response, label):
    # Do not print arbitrary response bodies: they may contain tokens or PII.
    print(f"{label}: HTTP {response.status_code}")
    if response.status_code != 200:
        raise NeoError(f"{label}: HTTP {response.status_code}; "
                       "401/403: verify token, NeoAPI permissions and IP with VPBankS.")
    try:
        body = response.json()
    except ValueError:
        raise NeoError(f"{label}: expected JSON") from None
    if not isinstance(body, dict) or body.get("status") != 1:
        raise NeoError(f"{label}: API status is not success")
    return body.get("data"), body.get("timestamp")


def authenticate(session, username, password):
    resp = session.post(AUTH, json={"username": username, "password": password},
                        headers={"Accept": "application/json", "Content-Type": "application/json"},
                        timeout=20, allow_redirects=False)
    data, _ = response_data(resp, "Authentication")
    token = data.get("access_token") if isinstance(data, dict) else None
    if not isinstance(token, str) or not token.strip():
        raise NeoError("Missing access_token")
    print("JWT received; token is not displayed or saved.")
    return token


def market_get(session, token, endpoint, params):
    if endpoint not in ("/market/marketStatus", "/stock/stockDetail"):
        raise NeoError("Only documented read-only market endpoints are permitted")
    response = session.get(BASE + endpoint, params=params,
                           headers={"Authorization": "Bearer " + token,
                                    "x-device": "ExitPlan", "x-devicetype": "chrome",
                                    "Accept": "application/json"},
                           timeout=20, allow_redirects=False)
    return response_data(response, endpoint)


def capture(session, token, symbols):
    status, status_timestamp = market_get(session, token, "/market/marketStatus",
                                          {"marketCode": "ALL"})
    if not isinstance(status, list) or not status:
        raise NeoError("Unexpected or empty marketStatus response")
    data, server_timestamp = market_get(session, token, "/stock/stockDetail", {
        "marketCode": "ALL", "symbols": ",".join(symbols),
        "stockType": "ST", "pageNo": 1, "pageSize": 100,
    })
    rows = data.get("content") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise NeoError("Unexpected stockDetail response: expected data.content")
    result = [{k: row.get(k) for k in FIELDS} for row in rows
              if isinstance(row, dict) and row.get("symbol") in symbols]
    if set(row["symbol"] for row in result) != set(symbols) or len(result) != len(symbols):
        raise NeoError("Missing or duplicate requested symbols; capture not saved")
    safe_status = [{k: row.get(k) for k in ("marketCode", "indexCode", "marketStatus")}
                   for row in status if isinstance(row, dict)]
    return {"source": "neo_rest_stockDetail", "received_at": datetime.now(VN).isoformat(),
            "server_timestamp": server_timestamp, "status_timestamp": status_timestamp,
            "market_status": safe_status, "data": result,
            "note": "REST observation; not a verified simultaneous executable order book. "
                    "Check tradingDate/session, quote age and units before planner import."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", nargs="+", default=["HPG", "VPB", "ACB"])
    args = parser.parse_args()
    symbols = list(dict.fromkeys(s.strip().upper() for s in args.symbols))
    if not 1 <= len(symbols) <= 12 or any(not re.fullmatch(r"[A-Z0-9]{1,12}", s) for s in symbols):
        parser.error("Choose 1-12 valid stock symbols")
    username = input("VPBankS custody account: ").strip()
    password = getpass("VPBankS password: ")
    try:
        with requests.Session() as session:
            token = authenticate(session, username, password)
            del password
            sample = capture(session, token, symbols)
        folder = ROOT / "data/raw/neo_rest"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / (datetime.now(VN).strftime("%Y%m%d_%H%M%S_%f") + ".json")
        with path.open("x", encoding="utf-8") as output:
            json.dump(sample, output, ensure_ascii=False, indent=2)
        print(f"Saved {len(sample['data'])} REST observations to {path.relative_to(ROOT)}")
        print("No processed files overwritten. Inspect session/date/bid fields before import.")
        return 0
    except NeoError as exc:
        print(str(exc), file=sys.stderr)
    except requests.RequestException as exc:
        print(f"Network request failed: {type(exc).__name__}", file=sys.stderr)
    except OSError as exc:
        print(f"Local storage failed: {type(exc).__name__}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
