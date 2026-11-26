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
import pandas as pd
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


async def capture(token, symbols, minutes, boards=None, max_mb=512):
    filters=[b.lower() for b in boards] if boards else symbols
    topics = [f"{kind}.{sym}@tick" for sym in filters for kind in ("quote", "trade")]
    wanted=set(symbols)
    bytes_written=0
    next_status=time.monotonic()+15
    print(f'Subscribing {len(topics)} topics; catalog candidates={len(wanted)}',flush=True)
    folder = ROOT / "data/raw/ssi_ws"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (datetime.now(VN).strftime("%Y%m%d_%H%M%S_%f") + ".jsonl")
    counts = Counter()
    frames = Counter()
    status_path=ROOT/"outputs/tables/ssi_recorder_status.json"
    status_path.parent.mkdir(parents=True,exist_ok=True)
    def save_status(state):
        temp=status_path.with_suffix(".json.tmp")
        temp.write_text(json.dumps({"state":state,"channel":"DATA","data_kind":"live",
            "source":"ssi_fastconnect_v3_ws","records":sum(counts.values()),
            "last_update_vn":datetime.now(VN).isoformat(),"symbols":symbols,"boards":boards,"bytes_written":bytes_written,
            "frames":dict(frames)},ensure_ascii=False,indent=2),encoding="utf-8")
        temp.replace(status_path)
    save_status("connecting")
    subscribed = False
    try:
        async with connect(URL, additional_headers={"Authorization": "Bearer " + token},
                           open_timeout=15, ping_interval=20, max_size=2**20) as ws:
            save_status("connected_unverified_auth")
            print("WebSocket transport connected; waiting for subscription/data.", flush=True)
            await ws.send(json.dumps({"method": "SUBSCRIBE", "channel": "DATA", "topics": topics}))
            await ws.send(json.dumps({"method": "LIST_SUBSCRIPTION"}))
            deadline = time.monotonic() + minutes * 60
            with path.open("x", encoding="utf-8") as out:
                while time.monotonic() < deadline:
                    now = time.monotonic()
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=min(5, max(.1, deadline-now)))
                    except asyncio.TimeoutError:
                        continue
                    try:
                        frame = json.loads(raw)
                    except (ValueError, TypeError):
                        frames["invalid_json"] += 1
                        continue
                    frames["json"] += 1
                    if isinstance(frame, dict):
                        code = str(frame.get("code", frame.get("status", "")))
                        if re.fullmatch(r"[45][0-9]{2,5}", code):
                            print("Server error code:", code, flush=True)
                            return 1
                        method = str(frame.get("method", "")).lower()
                        channel = str(frame.get("channel", "")).upper()
                        if method == "ping" and channel == "HEARTBEAT":
                            reply = {"method": "PONG", "channel": "HEARTBEAT"}
                            if "time" in frame:
                                reply["time"] = frame["time"]
                            await ws.send(json.dumps(reply))
                            frames["heartbeat"] += 1
                            continue
                        if method == "subscribe":
                            state = str(frame.get("status", "")).lower()
                            subscribed = state in ("ok", "success", "200")
                            print("SUBSCRIBE:", "OK" if subscribed else "ERROR" if state in ("error", "failed") else "UNCONFIRMED", flush=True)
                            if subscribed:save_status("subscribed_no_data")
                            if state in ("error", "failed"):
                                print("Subscription refused; check DATA streaming scope/topic with SSI.", flush=True)
                                return 1
                        if method == "list_subscription" or ("data" in frame and "trading" in frame and "topic" not in frame):
                            scope = frame.get("data")
                            if isinstance(scope, dict):
                                scope = scope.get("data")
                            if isinstance(scope, str):
                                allowed = [x.strip() for x in scope.split(";")
                                           if re.fullmatch(r"(quote|trade)\.[A-Za-z0-9*._@-]+", x.strip())]
                                print("DATA quote/trade scope or subscriptions:", "; ".join(allowed) or "not listed", flush=True)
                            else:
                                print("LIST_SUBSCRIPTION response received (shape not verified).", flush=True)
                            frames["subscription_list"] += 1
                            continue
                        if channel == "DATA":
                            frames["data"] += 1
                    rows = market_rows(frame, wanted)
                    if isinstance(frame, dict) and str(frame.get("channel", "")).upper() == "DATA" and not rows:
                        frames["data_unmatched"] += 1
                        if frames["data_unmatched"] <= 3:
                            print("DATA frame did not match quote/trade parser; inspect schema locally.", flush=True)
                    for row in rows:
                        line=json.dumps(row,ensure_ascii=False)+"\n"
                        bytes_written+=len(line.encode("utf-8"))
                        out.write(line)
                        counts[(row["symbol"],row["event"])]+=1
                        if counts[(row["symbol"],row["event"])]==1 and (not boards or len(counts)<=6):
                            print(f"Received {row['event']}: {row['symbol']}",flush=True)
                            fields=("s","t","bids","asks") if row["event"]=="quote" else ("s","t","p","q","v")
                            print("Market sample:",json.dumps({k:row["data"].get(k) for k in fields},ensure_ascii=False),flush=True)
                    if time.monotonic()>=next_status:
                        out.flush()
                        save_status("receiving_stockinfo" if counts else "subscribed_no_data")
                        print(f"Events={sum(counts.values())}; symbols={len({s for s,k in counts})}; MB={bytes_written/1e6:.1f}",flush=True)
                        next_status=time.monotonic()+15
                    if bytes_written>=max_mb*1024*1024:
                        print("Local file-size cap reached; stopping safely.",flush=True)
                        break
    finally:
        save_status("stopped" if sum(counts.values()) else "stopped_no_data")
        print("Subscription explicitly acknowledged:", "yes" if subscribed else "not verified")
        print("Frame counts:", dict(frames))
        received=sorted({s for s,k in counts})
        print(f"Received symbols: {len(received)}/{len(symbols)}; both streams: {sum(bool(counts[(s,'quote')] and counts[(s,'trade')]) for s in received)}")
        for sym in (received[:20] if boards else symbols):
            print(f"{sym}: quote={counts[(sym, 'quote')]} trade={counts[(sym, 'trade')]}")
        if path.exists():
            if path.stat().st_size:
                print("Raw file:", path.relative_to(ROOT))
            else:
                path.unlink()
    if boards:
        if not any(counts[(s,"quote")] and counts[(s,"trade")] for s in symbols):
            print("No symbol has both streams yet; whole-board capture not verified.")
            return 1
        print("Board capture received actual events; coverage is partial unless verified.")
        return 0
    if not all(counts[(s, "quote")] and counts[(s, "trade")] for s in symbols):
        print("Incomplete quote/trade capture. Try during market hours; check scope/schema.")
        return 1
    print("Quote and trade events received for all symbols. Verify schema and units before import.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="SSI V3 direct market data streaming")
    scope=parser.add_mutually_exclusive_group()
    scope.add_argument("--symbols", nargs="+")
    scope.add_argument("--boards", nargs="+", choices=["HOSE","HNX","UPCOM"])
    scope.add_argument("--all-market", action="store_true")
    parser.add_argument("--max-mb",type=int,default=512)
    parser.add_argument("--minutes", type=float, default=5)
    args = parser.parse_args()
    boards=["HOSE","HNX","UPCOM"] if args.all_market else args.boards
    if boards:
        from scripts.ssi_market_history import select_catalog
        catalog=pd.read_parquet(ROOT/"data/processed/ssi_securities.parquet")
        symbols=select_catalog(catalog,boards)
    else:
        symbols=sorted(set(s.strip().upper() for s in (args.symbols or ["HPG","VPB","ACB"])))
    from src.data.equity_universe import equity_symbols
    catalog_path=ROOT/"data/processed/ssi_securities.parquet"
    if not catalog_path.exists():parser.error("Run ssi_v3_sync.py --catalog first")
    allowed=set(equity_symbols(pd.read_parquet(catalog_path)))
    excluded=set(symbols)-allowed
    if excluded:parser.error("Outside stock scope: "+", ".join(sorted(excluded)))
    if not symbols or any(not re.fullmatch(r"[A-Z0-9]{1,12}",s) for s in symbols):parser.error("Invalid symbols")
    if not boards and len(symbols)>100:parser.error("Use --boards or --all-market for large scope")
    if not 1<=args.max_mb<=4096:parser.error("--max-mb must be 1..4096")
    if not math.isfinite(args.minutes) or not 0 < args.minutes <= 360:
        parser.error("--minutes must be between 0 and 360")
    try:
        client = SSIReadOnlyClient()
        client.authenticate()
        print("SSI Market Data token received. No OTP or Client ID.", flush=True)
        return asyncio.run(capture(client._token, symbols, args.minutes, boards, args.max_mb))
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
