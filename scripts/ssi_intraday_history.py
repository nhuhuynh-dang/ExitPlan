"""Download official SSI 1-minute candles (not historical order books).
Docs: https://developers.ssi.com.vn/en/docs/api-reference/data-ohlc
Run from project root. Checkpoint per symbol/date; never modify daily or WS files.
"""
from datetime import timedelta
import argparse
import json
import time
from pathlib import Path
import sys
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.ssi_v3_sync import parse_date, _save_parquet, _save_csv
from src.ingest.ssi_fastconnect_v3 import SSIReadOnlyClient, SSIResponseError, SSIAuthError
from src.analytics.ssi_history_stats import expected_sessions

SOURCE = "ssi_fastconnect_v3"
TZ = "Asia/Ho_Chi_Minh"
FIELDS = ["open", "high", "low", "close", "volume"]


def normalize_minutes(records, symbol, day):
    """Preserve minute timestamps; reject date-only or conflicting duplicate rows."""
    rows = []
    for record in records:
        if not isinstance(record, dict) or str(record.get("symbol", "")).upper() != symbol:
            raise SSIResponseError("Unexpected symbol or malformed candle")
        raw = str(record.get("tradingDate", ""))
        if not re.search(r"[T ]\d{2}:\d{2}", raw):
            raise SSIResponseError("SSI tradingDate has no intraday time; cannot reconstruct minute candles")
        ts = pd.Timestamp(raw)
        ts = ts.tz_localize(TZ) if ts.tzinfo is None else ts.tz_convert(TZ)
        if ts.date() != day or ts.second or ts.microsecond or ts.nanosecond:
            raise SSIResponseError("Unexpected candle date or non-minute timestamp")
        rows.append(dict(symbol=symbol, ts_vn=ts, tradingDate=str(day),
                         **{k: record.get(k) for k in FIELDS},
                         source=SOURCE, data_kind="historical_intraday", timeframe="1m",
                         price_unit="as_returned_by_ssi_api", volume_unit="as_returned_by_ssi_api"))
    if not rows:
        return pd.DataFrame()
    d = pd.DataFrame(rows)
    d[FIELDS] = d[FIELDS].apply(pd.to_numeric, errors="coerce")
    good = (np.isfinite(d[FIELDS]).all(axis=1)
            & (d[["open", "high", "low", "close"]] > 0).all(axis=1)
            & (d.volume >= 0)
            & (d.high >= d[["open", "close", "low"]].max(axis=1))
            & (d.low <= d[["open", "close"]].min(axis=1)))
    if not good.all():
        raise SSIResponseError("Invalid OHLCV values; day not published")
    d = d.drop_duplicates()
    if d.duplicated(["symbol", "ts_vn"]).any():
        raise SSIResponseError("Conflicting candles at the same minute")
    return d.sort_values("ts_vn").reset_index(drop=True)


def fetch_day(client, symbol, day, page_size=500, wait=2, max_pages=100):
    """Follow server page size if it caps requests, stop on repeated pages."""
    records = []
    seen = set()
    date_text = day.strftime("%Y/%m/%d")
    for page in range(1, max_pages + 1):
        body = client._get("/api/v3/data/ohlc", {
            "symbol": symbol, "from": date_text + " 00:00:00",
            "to": date_text + " 23:59:59", "timeFrame": "1m",
            "pageIndex": page, "pageSize": page_size})
        part = body.get("data") if isinstance(body, dict) else None
        if not isinstance(part, list):
            raise SSIResponseError("SSI OHLC response missing data list")
        if not part:
            break
        if any(not isinstance(x, dict) for x in part):
            raise SSIResponseError("Malformed SSI candle")
        fingerprint = tuple(str(x.get("tradingDate")) for x in part)
        if fingerprint in seen:
            raise SSIResponseError("Repeated OHLC page")
        seen.add(fingerprint)
        records.extend(part)
        count = body.get("pageCount", body.get("pagesCount"))
        if count is not None and int(count) > 0 and page >= int(count):
            break
        actual_size = int(body.get("pageSize") or page_size)
        if count is None and len(part) < actual_size:
            break
        if page == max_pages:
            raise SSIResponseError("OHLC pagination limit reached; day not published")
        time.sleep(wait)
    return normalize_minutes(records, symbol, day)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", nargs="+", default=["HPG", "VPB", "ACB"])
    p.add_argument("--from-date", type=parse_date, required=True)
    p.add_argument("--to-date", type=parse_date, required=True)
    p.add_argument("--page-size", type=int, default=500)
    p.add_argument("--delay", type=float, default=2)
    a = p.parse_args(argv)
    symbols = sorted(set(s.strip().upper() for s in a.symbols))
    if (a.from_date > a.to_date or a.from_date.year != 2026 or a.to_date.year != 2026
            or a.to_date >= pd.Timestamp.now(tz=TZ).date()
            or not 1 <= a.page_size <= 500 or not 1 <= a.delay <= 60
            or any(not re.fullmatch(r"[A-Z0-9]{1,12}", s) for s in symbols)):
        p.error("Invalid dates/symbols/page size/delay; use completed 2026 sessions")
    dates = expected_sessions(a.to_date + timedelta(days=1), 1)
    if dates is None:
        p.error("Calendar unavailable")
    # Reuse the scheduled closures from the same calendar as daily metrics.
    from src.analytics.ssi_history_stats import HOLIDAYS_2026
    sessions = pd.bdate_range(a.from_date, a.to_date).difference(HOLIDAYS_2026)
    if not len(sessions):
        p.error("No scheduled sessions")
    tag = f"{a.from_date}_{a.to_date}_" + "_".join(symbols)
    cache = ROOT / "data/processed/ssi_intraday_cache" / tag
    cache.mkdir(parents=True, exist_ok=True)
    jobs = [(s, d.date(), cache / f"{s}_{d.date()}.parquet") for s in symbols for d in sessions]
    client = SSIReadOnlyClient()
    error = None
    try:
        for i, (sym, day, path) in enumerate(jobs, 1):
            if path.exists():
                continue
            try:
                frame = fetch_day(client, sym, day, a.page_size, a.delay)
            except (SSIAuthError, SSIResponseError, ValueError) as exc:
                error = f"{sym} {day}: {exc}"
                print("Stopped:", error, flush=True)
                break
            if frame.empty:
                print(f"[{i}/{len(jobs)}] {sym} {day}: no candles", flush=True)
            else:
                _save_parquet(frame, path)
                print(f"[{i}/{len(jobs)}] {sym} {day}: {len(frame)} candles", flush=True)
            time.sleep(a.delay)
    except KeyboardInterrupt:
        error = "Interrupted"
    finally:
        client.session.close()
        chunks = [pd.read_parquet(path) for _, _, path in jobs if path.exists()]
        remaining = [f"{s} {d}" for s, d, path in jobs if not path.exists()]
        report = dict(source=SOURCE, data_kind="historical_intraday", timeframe="1m",
                      expected_dates=[str(x.date()) for x in sessions], expected_symbol_days=len(jobs),
                      completed_symbol_days=len(chunks), missing_symbol_days=remaining,
                      stopped=error is not None, stop_reason=error)
        if chunks:
            combined = pd.concat(chunks, ignore_index=True).sort_values(["symbol", "ts_vn"])
            base = ROOT / "data/processed" / f"ssi_intraday_1m_{tag}"
            _save_parquet(combined, base.with_suffix(".parquet"))
            _save_csv(combined, base.with_suffix(".csv"))
            counts = combined.groupby(["symbol", "tradingDate"]).size()
            report.update(rows=len(combined), symbols=int(combined.symbol.nunique()),
                          trading_dates=int(combined.tradingDate.nunique()),
                          candles_by_symbol_day={f"{s} {d}": int(n) for (s,d),n in counts.items()},
                          parquet=str(base.with_suffix(".parquet").relative_to(ROOT)))
        out = ROOT / "outputs/tables" / f"ssi_intraday_quality_{tag}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(bool(remaining or error))


if __name__ == "__main__":
    raise SystemExit(main())
