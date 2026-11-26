"""Convert captured SSI V3 quote/trade events to synchronized HOSE snapshots.
Documented fields: quote.bids/asks [price, qty], trade.p/v, exchange time t.
No inferred units, no invented depth, no carry across sessions, no look-ahead.
"""
from collections import Counter
from datetime import time
import math
import pandas as pd

SOURCE = "ssi_fastconnect_v3_ws"

def timestamp(value):
    t = pd.Timestamp(value)
    if pd.isna(t):
        raise ValueError("missing timestamp")
    return t.tz_localize("Asia/Ho_Chi_Minh") if t.tzinfo is None else t.tz_convert("Asia/Ho_Chi_Minh")

def session(t):
    h = t.time()
    if t.weekday() >= 5:
        return None
    if time(9,15) <= h < time(11,30):
        return (t.date(), "AM")
    if time(13) <= h < time(14,30):
        return (t.date(), "PM")
    return None

def numeric(x, factor=1, integer=False):
    if isinstance(x, bool):
        raise ValueError("boolean numeric field")
    n = float(x) * factor
    if not math.isfinite(n) or n < 0 or (integer and not n.is_integer()):
        raise ValueError("invalid numeric field")
    return int(n) if integer else n

def depth(values, factor, volume_factor, reverse):
    if not isinstance(values, list) or len(values) < 3:
        raise ValueError("incomplete three-level book")
    result = []
    for pair in values[:3]:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError("unexpected level schema")
        p, v = numeric(pair[0], factor), numeric(pair[1], volume_factor, True)
        if p <= 0 or v <= 0:
            raise ValueError("non-executable level")
        result.append((p, v))
    prices = [p for p, _ in result]
    if prices != sorted(set(prices), reverse=reverse):
        raise ValueError("duplicate or unsorted levels")
    return result

def build_snapshots(events, symbols, *, quote_price_factor, trade_price_factor,
                    volume_factor, quote_age=5, trade_age=60, interval=5):
    """Replay received events in order; require all selected symbols within bounded age.
    HOSE continuous-session MVP only. Price/volume factors must be verified by operator.
    Each evaluation timestamp is actual receive time, not exchange execution time.
    Invalid updates invalidate the prior state rather than silently carrying it forward.
    """
    symbols = set(symbols)
    if not symbols or len(symbols) > 12:
        raise ValueError("choose 1-12 symbols")
    if any(not math.isfinite(x) or x <= 0 for x in (quote_price_factor, trade_price_factor, volume_factor, quote_age, trade_age, interval)):
        raise ValueError("invalid scale or age")
    stats = Counter()
    ordered = []
    for row in events:
        stats["input"] += 1
        try:
            if row["source"] != SOURCE or row["symbol"] not in symbols or row["event"] not in ("quote", "trade"):
                raise ValueError("unexpected source/symbol/event")
            recv = timestamp(row["received_at"])
            ordered.append((recv, row))
        except (KeyError, TypeError, ValueError):
            stats["invalid_envelope"] += 1
    ordered.sort(key=lambda x: x[0])
    state, output = {}, []
    last_eval = None
    for recv, row in ordered:
        sym, kind = row["symbol"], row["event"]
        key = (sym, kind)
        try:
            d = row["data"]
            if d["s"] != sym:
                raise ValueError("symbol mismatch")
            ex = timestamp(d["t"])
            if session(recv) is None or session(ex) != session(recv):
                raise ValueError("outside continuous session")
            lag = (recv - ex).total_seconds()
            if lag < -1 or lag > (quote_age if kind == "quote" else trade_age):
                raise ValueError("stale or future source time")
            old = state.get(key)
            if old is not None and ex < old[0]:
                stats["out_of_order"] += 1
                continue
            if kind == "quote":
                bids = depth(d["bids"], quote_price_factor, volume_factor, True)
                asks = depth(d["asks"], quote_price_factor, volume_factor, False)
                if bids[0][0] >= asks[0][0]:
                    raise ValueError("crossed book")
                values = {"bidPrice"+str(i): p for i,(p,v) in enumerate(bids,1)}
                values.update({"bidVol"+str(i): v for i,(p,v) in enumerate(bids,1)})
                values.update({"askPrice"+str(i): p for i,(p,v) in enumerate(asks,1)})
                values.update({"askVol"+str(i): v for i,(p,v) in enumerate(asks,1)})
            else:
                p = numeric(d["p"], trade_price_factor)
                if p <= 0:
                    raise ValueError("invalid last price")
                values = {"closePrice":p, "totalTradingVolume":numeric(d["v"],volume_factor,True)}
            state[key] = (ex, recv, values)
            stats["accepted_"+kind] += 1
        except (KeyError, TypeError, ValueError, OverflowError):
            state.pop(key, None)
            stats["invalid_"+kind] += 1
            continue
        if last_eval is not None and (recv-last_eval).total_seconds() < interval:
            continue
        batch = []
        for s in sorted(symbols):
            q, t = state.get((s,"quote")), state.get((s,"trade"))
            if not q or not t:
                break
            if any(session(x[0]) != session(recv) or session(x[1]) != session(recv)
                   or not -1 <= (recv-x[0]).total_seconds() <= age
                   or not 0 <= (recv-x[1]).total_seconds() <= age
                   for x,age in ((q,quote_age),(t,trade_age))):
                break
            # Reject thousand-fold price scaling mistakes; no automatic conversion.
            ratio = q[2]["bidPrice1"]/t[2]["closePrice"]
            if not .8 <= ratio <= 1.2:
                stats["price_scale_or_stale"] += 1
                break
            batch.append(dict(ts_vn=recv, symbol=s, data_kind="live", source=SOURCE,
                              quote_ts=q[0], trade_ts=t[0], quote_received_at=q[1],
                              trade_received_at=t[1], price_unit="VND", volume_unit="shares",
                              quote_age_seconds=(recv-q[0]).total_seconds(),
                              trade_age_seconds=(recv-t[0]).total_seconds(),
                              **q[2], **t[2]))
        if len(batch) == len(symbols):
            output.extend(batch)
            last_eval = recv
            stats["aligned_snapshots"] += 1
        else:
            stats["incomplete_alignment"] += 1
    return pd.DataFrame(output), dict(stats)
