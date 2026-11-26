"""SSI V3 direct read-only DATA stream using existing Market Data token.
Only quote/trade topics; no OTP, client ID, private key or account subscription.
Raw captures are separate from planner snapshots and historical OHLCV.
"""
from __future__ import annotations
import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone, timedelta
import json
import math
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ingest.ssi_fastconnect_v3 import SSIReadOnlyClient, SSIAuthError
from websockets.asyncio.client import connect

URL = "wss://stream.ssi.com.vn/ws/v3"
VN = timezone(timedelta(hours=7))
SENSITIVE = ("token", "secret", "password", "authorization", "privatekey",
             "apikey", "account", "username", "clientid", "otp")


def redact(value):
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()
                if not any(word in re.sub(r"[^a-z]", "", k.lower()) for word in SENSITIVE)}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def market_rows(frame, symbols):
    """Capture DATA quote/trade payloads without inventing a normalized schema."""
    if not isinstance(frame, dict):
        return []
    if str(frame.get("channel", "")).upper() != "DATA":
        return []
    topic = str(frame.get("topic", "")).lower()
    event = topic.split(".", 1)[0]
    if event not in ("quote", "trade"):
        return []
    payload = frame.get("data")
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except ValueError:
            return []
    items = payload if isinstance(payload, list) else [payload]
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sym = str(item.get("s") or item.get("symbol") or "").upper()
        if sym not in symbols:
            continue
        rows.append({"source": "ssi_fastconnect_v3_ws",
                     "received_at": datetime.now(VN).isoformat(timespec="milliseconds"),
                     "event": event, "symbol": sym, "topic": topic,
                     "data": redact(item)})
    return rows


async def capture(token, symbols, minutes):
    topics = [f"{kind}.{sym}" for sym in symbols for kind in ("quote", "trade")]
    folder = ROOT / "data/raw/ssi_ws"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (datetime.now(VN).strftime("%Y%m%d_%H%M%S_%f") + ".jsonl")
    counts = Counter()
    try:
        async with connect(URL, additional_headers={"Authorization": "Bearer " + token},
                           open_timeout=15, ping_interval=20, max_size=2**20) as ws:
            print("WebSocket transport connected; waiting for subscription/data.", flush=True)
            await ws.send(json.dumps({"method": "SUBSCRIBE", "channel": "DATA", "topics": topics}))
            deadline = time.monotonic() + minutes * 60
            next_ping = time.monotonic() + 30
            with path.open("x", encoding="utf-8") as out:
                while time.monotonic() < deadline:
                    now = time.monotonic()
                    if now >= next_ping:
                        await ws.send(json.dumps({"method": "ping_pong"}))
                        next_ping = now + 30
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=min(5, max(.1, deadline-now)))
                    except asyncio.TimeoutError:
                        continue
                    try:
                        frame = json.loads(raw)
                    except (ValueError, TypeError):
                        continue
                    if isinstance(frame, dict):
                        code = str(frame.get("code", frame.get("status", "")))
                        if re.fullmatch(r"[45][0-9]{2,5}", code):
                            print("Server error code:", code, flush=True)
                            return 1
                        method = str(frame.get("method", "")).lower()
                        if method == "subscribe":
                            print("Subscription response received; actual data still required.", flush=True)
                    for row in market_rows(frame, symbols):
                        out.write(json.dumps(row, ensure_ascii=False) + "\n")
                        counts[(row["symbol"], row["event"])] += 1
                        if counts[(row["symbol"], row["event"])] == 1:
                            print(f"Received {row['event']}: {row['symbol']}", flush=True)
                    out.flush()
    finally:
        for sym in symbols:
            print(f"{sym}: quote={counts[(sym, 'quote')]} trade={counts[(sym, 'trade')]}")
        if path.exists():
            if path.stat().st_size:
                print("Raw file:", path.relative_to(ROOT))
            else:
                path.unlink()
    if not all(counts[(s, "quote")] and counts[(s, "trade")] for s in symbols):
        print("Incomplete quote/trade capture. Try during market hours; check scope/schema.")
        return 1
    print("Quote and trade events received for all symbols. Verify schema and units before import.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="SSI V3 direct market data streaming")
    parser.add_argument("--symbols", nargs="+", default=["HPG", "VPB", "ACB"])
    parser.add_argument("--minutes", type=float, default=5)
    args = parser.parse_args()
    symbols = sorted(set(s.strip().upper() for s in args.symbols))
    if not 1 <= len(symbols) <= 12 or any(not re.fullmatch(r"[A-Z0-9]{1,12}", s) for s in symbols):
        parser.error("Choose 1-12 valid symbols")
    if not math.isfinite(args.minutes) or not 0 < args.minutes <= 360:
        parser.error("--minutes must be between 0 and 360")
    try:
        client = SSIReadOnlyClient()
        client.authenticate()
        print("SSI Market Data token received. No OTP or Client ID.", flush=True)
        return asyncio.run(capture(client._token, symbols, args.minutes))
    except KeyboardInterrupt:
        print("Stopped by user.")
        return 130
    except SSIAuthError as exc:
        print(str(exc))
        return 1
    except Exception as exc:
        # Never print handshake headers or raw exception payloads.
        print("Stream not verified:", type(exc).__name__)
        response = getattr(exc, "response", None)
        code = getattr(response, "status_code", None)
        if isinstance(code, int):
            print("Handshake HTTP:", code)
        return 1
    finally:
        if "client" in locals():
            client.session.close()


if __name__ == "__main__":
    sys.exit(main())
