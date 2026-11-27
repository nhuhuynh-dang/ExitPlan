"""Resumable sequential download of official SSI daily history across exchanges.
Catalog is securities, not a verified list of active common shares. Optional exact stockType filter.
No synthetic data; stop on auth/network/rate-limit errors; checkpoint every successful symbol.
"""
import argparse
import json
from pathlib import Path
import sys
import time
import re
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.ssi_v3_sync import parse_date,_save_parquet,_save_csv
from src.ingest.ssi_fastconnect_v3 import SSIReadOnlyClient,SSIBadRequest,SSISymbolNotFound,SSIResponseError,SSIAuthError,normalize_ohlc,ALLOWED_BOARDS
from src.analytics.ssi_history_stats import asof_history_stats

def select_catalog(catalog,boards,stock_types=None):
    if not {"symbol","board","source"}.issubset(catalog.columns) or set(catalog.source)!={"ssi_fastconnect_v3"}:
        raise ValueError("Catalog must come from official SSI V3")
    from src.data.equity_universe import equity_catalog
    d=equity_catalog(catalog)
    d=d[d.board.isin(boards)].copy()
    if stock_types:
        if "stockType" not in d:raise ValueError("Refresh catalog with --catalog first")
        d=d[d.stockType.astype(str).isin(stock_types)]
    return sorted(set(s for s in d.symbol.astype(str) if re.fullmatch(r"[A-Z0-9]{1,12}",s)))

def ready_history_symbols(history, asof):
    """Require both point-in-time metrics; missing history never becomes zero."""
    if history is None or history.empty:
        return set()
    stats=asof_history_stats(history,asof)
    return set(stats.loc[stats.adv.notna() & stats.sigma.notna(),"symbol"])


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--boards",nargs="+",choices=ALLOWED_BOARDS,default=list(ALLOWED_BOARDS))
    p.add_argument("--stock-types",nargs="+",help="Exact SSI stockType codes; inspect catalog before filtering")
    p.add_argument("--from-date",type=parse_date,required=True)
    p.add_argument("--to-date",type=parse_date,required=True)
    p.add_argument("--missing-book-history",action="store_true",help="Only recorded SSI snapshot symbols missing ADV20 or Sigma20")
    p.add_argument("--dry-run",action="store_true",help="Report target symbols without API calls")
    p.add_argument("--limit",type=int,default=None,help="Max new requests by symbol this run")
    p.add_argument("--delay",type=float,default=1.0)
    p.add_argument("--retry-failed",action="store_true",help="Retry previously skipped no-data/HTTP400 symbols")
    a=p.parse_args()
    if a.from_date>a.to_date or not .5<=a.delay<=60 or (a.limit is not None and a.limit<1):p.error("Invalid range/limit/delay")
    catalog=pd.read_parquet(ROOT/"data/processed/ssi_securities.parquet")
    symbols=select_catalog(catalog,a.boards,a.stock_types)
    if not symbols:p.error("No matching securities")
    old=ROOT/"data/processed/ssi_history.parquet"
    prior=pd.read_parquet(old) if old.exists() else None
    if prior is not None and (set(prior.source)!={"ssi_fastconnect_v3"} or set(prior.data_kind)!={"historical"}):
        raise ValueError("Existing history source mismatch; not overwritten")
    universe=set(symbols)
    asof=None
    if a.missing_book_history:
        path=ROOT/"data/processed/ssi_book_snapshots.parquet"
        if not path.is_file():p.error("Import SSI book snapshots first")
        books=pd.read_parquet(path)
        if books.empty or set(books.source)!={"ssi_fastconnect_v3_ws"} or set(books.data_kind)!={"live"}:
            p.error("Expected nonempty recorded SSI snapshots")
        from src.ingest.ssi_books import timestamp
        asof=max(books.ts_vn.map(timestamp)).date()
        if a.to_date>=asof:p.error("For point-in-time history, --to-date must precede latest snapshot date")
        universe &= set(books.symbol)
        ready=ready_history_symbols(prior,asof) & universe
        symbols=sorted(universe-ready)
        print(f"Book symbols: {len(universe)}; ready ADV20+Sigma20: {len(ready)}; missing: {len(symbols)}; asof: {asof}",flush=True)
    if a.dry_run or not symbols:
        print("Targets:", " ".join(symbols) or "none")
        return 0
    print(f"Stock candidates: {len(symbols)}; common-stock scope, not a verified active trading list.",flush=True)
    cache=ROOT/"data/processed/ssi_market_cache"/f"{a.from_date}_{a.to_date}"
    if a.missing_book_history:cache=cache/"missing_book_history"
    cache.mkdir(parents=True,exist_ok=True)
    fail_path=cache/"skipped.json"
    skipped=json.loads(fail_path.read_text(encoding="utf-8")) if fail_path.exists() else {}
    def mark_failed(sym,reason):
        skipped[sym]=reason
        tmp=fail_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(skipped,ensure_ascii=False),encoding="utf-8")
        tmp.replace(fail_path)
    client=SSIReadOnlyClient()
    attempted=0; failed=[]; stopped=False; stop_reason=None
    try:
        client.authenticate()
        for i,sym in enumerate(symbols,1):
            part=cache/f"{sym}.parquet"
            if (part.exists() and not (a.missing_book_history and a.retry_failed)) or (sym in skipped and not a.retry_failed):continue
            if a.limit is not None and attempted>=a.limit:break
            attempted+=1
            try:
                rows=client.ohlc_daily(sym,a.from_date,a.to_date,wait=a.delay,max_pages=200)
                if not rows:
                    failed.append({"symbol":sym,"reason":"no_rows"});mark_failed(sym,"no_rows")
                else:
                    df=normalize_ohlc(rows)
                    df=df[df.tradingDate.dt.date.between(a.from_date,a.to_date)]
                    if df.empty:failed.append({"symbol":sym,"reason":"no_valid_dates"});mark_failed(sym,"no_valid_dates")
                    else:
                        if set(df.symbol)!={sym}:raise SSIResponseError("Unexpected symbol in OHLCV response")
                        _save_parquet(df,part)
                        print(f"[{i}/{len(symbols)}] {sym}: {len(df)} candles",flush=True)
            except SSISymbolNotFound as exc:
                failed.append({"symbol":sym,"reason":"404204"});mark_failed(sym,"404204")
                print(f"[{i}/{len(symbols)}] {sym}: {exc}; bỏ qua mã này.",flush=True)
            except SSIBadRequest as exc:
                failed.append({"symbol":sym,"reason":"HTTP400"});mark_failed(sym,"HTTP400")
                print(f"[{i}/{len(symbols)}] {sym}: {exc}",flush=True)
                if sum(f["reason"]=="HTTP400" for f in failed)>=10:
                    print("Repeated HTTP400 errors; stop and check SSI.")
                    stopped=True;break
            except (SSIResponseError,SSIAuthError) as exc:
                stop_reason={"symbol":sym,"reason":str(exc)}
                print(f"Stopped [{i}/{len(symbols)}] {sym}: {exc}",flush=True);stopped=True;break
            time.sleep(a.delay)
    except KeyboardInterrupt:
        print("Interrupted; saving progress.")
        stopped=True
    except SSIAuthError as exc:
        print(str(exc));stopped=True
    finally:
        client.session.close()
        chunks=[pd.read_parquet(cache/f"{s}.parquet") for s in symbols if (cache/f"{s}.parquet").is_file()]
        combined=prior
        completed=len(chunks)
        old=ROOT/"data/processed/ssi_history.parquet"
        if chunks:
            if old.exists():
                prior=pd.read_parquet(old)
                if set(prior.source)!={"ssi_fastconnect_v3"} or set(prior.data_kind)!={"historical"}:
                    raise ValueError("Existing history source mismatch; not overwritten")
                chunks.insert(0,prior)
            combined=pd.concat(chunks,ignore_index=True).drop_duplicates(["symbol","tradingDate"],keep="last").sort_values(["symbol","tradingDate"])
            _save_parquet(combined,old)
            from src.data.equity_universe import equity_symbols
            equity_history=combined[combined.symbol.isin(equity_symbols(catalog))]
            if not equity_history.empty:
                _save_parquet(asof_history_stats(equity_history),ROOT/"outputs/tables/ssi_liquidity_stats.parquet")
            _save_csv(combined,ROOT/"data/raw/ssi_fastconnect_v3_ohlcv.csv")
        report={"requested":len(symbols),"completed":completed,"attempted_this_run":attempted,"failures_this_run":failed,"remaining":len(symbols)-completed,"skipped_without_success":sum(s in skipped and not (cache/f"{s}.parquet").is_file() for s in symbols),"stopped":stopped,"stop_reason":stop_reason}
        if a.missing_book_history:
            ready_after=ready_history_symbols(combined,asof) & universe
            report.update(book_symbols=len(universe),ready_history=len(ready_after),
                missing_history=len(universe-ready_after),asof_date=str(asof),
                remaining_symbols=sorted(universe-ready_after))
        (cache/"progress.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps({k:v for k,v in report.items() if k not in ("failures_this_run","remaining_symbols")},ensure_ascii=False))
    return 0 if (report["missing_history"]==0 if a.missing_book_history else completed==len(symbols)) else 1

if __name__=="__main__":raise SystemExit(main())
