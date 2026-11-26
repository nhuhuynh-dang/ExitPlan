"""Capture only public SSI V3 market quote/trade events using official SDK.

Raw observations are NOT planner snapshots. Do not mix with synthetic data.
No OTP, account queries, private key, or trading subscriptions.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import json
import math
import os
from pathlib import Path
import re
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
VN = timezone(timedelta(hours=7))


def safe_number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        n = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return n if math.isfinite(n) else None


def levels(values):
    if not isinstance(values, (list, tuple)):
        return []
    return [safe_number(value) for value in values[:3]]


def market_record(msg, symbols, quote_type, trade_type):
    symbol = str(getattr(msg, "symbol", "")).strip().upper()
    if symbol not in symbols:
        return None
    row = {"source": "ssi_fastconnect_v3_ws",
           "received_at": datetime.now(VN).isoformat(timespec="milliseconds"),
           "trading_time": str(getattr(msg, "trading_time", "")),
           "symbol": symbol}
    if isinstance(msg, quote_type):
        row["event"] = "quote"
        for name in ("bid_prices", "bid_volumes", "ask_prices", "ask_volumes"):
            row[name] = levels(getattr(msg, name, None))
        if not all(len(row[k]) == 3 for k in ("bid_prices", "bid_volumes")):
            return None
        return row
    if isinstance(msg, trade_type):
        row["event"] = "trade"
        for name in ("price", "quantity", "total_volume"):
            row[name] = safe_number(getattr(msg, name, None))
        if row["price"] is None or row["price"] <= 0:
            return None
        return row
    return None


def main():
    parser = argparse.ArgumentParser(description="SSI market-data WebSocket read-only capture")
    parser.add_argument("--symbols", nargs="+", default=["HPG", "VPB", "ACB"])
    parser.add_argument("--minutes", type=float, default=5)
    args = parser.parse_args()
    symbols = sorted(set(s.strip().upper() for s in args.symbols))
    if not 1 <= len(symbols) <= 12 or any(not re.fullmatch(r"[A-Z0-9]{1,12}", s) for s in symbols):
        parser.error("Choose 1-12 valid symbols")
    if not math.isfinite(args.minutes) or not 0 < args.minutes <= 360:
        parser.error("--minutes must be between 0 and 360")
    key, secret = os.getenv("SSI_API_KEY"), os.getenv("SSI_API_SECRET")
    client_id = os.getenv("SSI_CLIENT_ID")
    if not key or not secret or not client_id:
        print("Can SSI_API_KEY, SSI_API_SECRET va SSI_CLIENT_ID do SSI cung cap.")
        return 2
    try:
        from ssi_sdk import Auth, Config, Stream
        from ssi_sdk.models.streaming import QuoteMessage, TradeMessage
    except ImportError:
        print("Cai SDK chinh thuc: py -m pip install ssi-sdk")
        return 2

    folder = ROOT / "data/raw/ssi_ws"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (datetime.now(VN).strftime("%Y%m%d_%H%M%S_%f") + ".jsonl")
    counts = Counter()
    lock = threading.Lock()
    stop = threading.Event()
    try:
        config = Config(client_id=client_id, api_key=key, api_secret=secret)
        with path.open("x", encoding="utf-8") as out:
            def on_data(msg):
                row = market_record(msg, symbols, QuoteMessage, TradeMessage)
                if row is None or stop.is_set():
                    return
                with lock:
                    if stop.is_set():
                        return
                    out.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
                    out.flush()
                    counts[(row["symbol"], row["event"])] += 1
                    if counts[(row["symbol"], row["event"])] == 1:
                        print(f"Received {row['event']}: {row['symbol']}", flush=True)

            def on_connection(ev):
                state = str(getattr(ev, "state", ""))
                if state.lower() in ("connected", "reconnected", "disconnected", "failed"):
                    print("WebSocket:", state, flush=True)

            with Auth(config) as auth:
                auth.authenticate()
                with Stream(auth) as stream:
                    ws = stream.streaming
                    ws.on_data = on_data
                    ws.on_connection = on_connection
                    try:
                        ws.connect()
                        ws.subscribe_symbol_quote(symbols)
                        ws.subscribe_symbol_trade(symbols)
                        print("Subscribed request sent; waiting for actual quote/trade events.", flush=True)
                        ws.wait(timeout_ms=int(args.minutes * 60000))
                    finally:
                        with lock:
                            stop.set()
    except KeyboardInterrupt:
        print("Stopped by user.")
    except Exception as exc:
        # No raw SDK error or response dump: may contain credential data.
        print(f"SSI stream not verified: {type(exc).__name__}. Check DATA streaming scope and SDK requirements.")
        return 1
    finally:
        print("Recorded counts:")
        for sym in symbols:
            print(f"{sym}: quote={counts[(sym, 'quote')]} trade={counts[(sym, 'trade')]}")
        if sum(counts.values()):
            print("Raw file:", path.relative_to(ROOT))
        elif path.exists() and path.stat().st_size == 0:
            path.unlink()
    if not all(counts[(s, "quote")] and counts[(s, "trade")] for s in symbols):
        print("Not enough quote/trade events for all symbols. Try during continuous trading; verify permissions.")
        return 1
    print("Quote/trade received for all requested symbols. Verify units and time alignment before planner import.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
