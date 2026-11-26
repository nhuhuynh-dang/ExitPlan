"""Import raw SSI V3 captures into a separate verified-input dataset.
Example (ONLY after checking live units against SSI iBoard):
py scripts/import_ssi_ws.py --symbols HPG VPB ACB --quote-price-factor 1000 --trade-price-factor 1 --volume-factor 1 --history-volume-factor 1
"""
import argparse
import json
import math
import os
from pathlib import Path
import sys
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ingest.ssi_books import build_snapshots

def main():
    p=argparse.ArgumentParser(description="Normalize SSI captures during common continuous-session windows")
    p.add_argument("--input", nargs="+", help="JSONL files; default: all data/raw/ssi_ws/*.jsonl")
    scope=p.add_mutually_exclusive_group(required=True)
    scope.add_argument("--symbols",nargs="+")
    scope.add_argument("--all-market",action="store_true")
    scope.add_argument("--boards",nargs="+",choices=["HOSE","HNX","UPCOM"])
    p.add_argument("--stock-types",nargs="+",help="Verified SSI stockType codes, optional")
    p.add_argument("--interval-seconds",type=int,default=None)
    p.add_argument("--quote-price-factor", type=float, required=True)
    p.add_argument("--trade-price-factor", type=float, required=True)
    p.add_argument("--volume-factor", type=float, required=True)
    p.add_argument("--history-volume-factor", type=float, required=True, help="Confirmed daily OHLCV volume to shares multiplier")
    a=p.parse_args()
    if not math.isfinite(a.history_volume_factor) or a.history_volume_factor <= 0:
        p.error("Invalid history volume factor")
    market=bool(a.all_market or a.boards)
    from scripts.ssi_market_history import select_catalog
    if market:
        catalog=pd.read_parquet(ROOT/"data/processed/ssi_securities.parquet")
        symbols=select_catalog(catalog,a.boards or ["HOSE","HNX","UPCOM"],a.stock_types)
    else:
        symbols=sorted(set(s.strip().upper() for s in a.symbols))
    interval=a.interval_seconds or (30 if market else 5)
    if interval<1:p.error("Invalid interval")
    paths=[Path(x) for x in a.input] if a.input else sorted((ROOT/"data/raw/ssi_ws").glob("*.jsonl"))
    if market and not a.input and paths:
        paths=paths[-1:]
        print("Market mode: latest capture only; use --input to specify a different file.")
    if market and sum(p.stat().st_size for p in paths)>128*1024*1024:
        p.error("Market import limited to 128 MiB per run; record smaller files or import selected symbols.")
    wanted=set(symbols)
    if not paths:
        print("Chưa có file JSONL SSI. Không tạo snapshot giả.")
        return 1
    events=[]
    bad=0
    try:
        for path in paths:
            with path.open(encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        r=json.loads(line)
                        if not isinstance(r,dict): raise ValueError("invalid record")
                        if r.get("symbol") in wanted:events.append(r)
                    except ValueError:
                        bad+=1
        frame,stats=build_snapshots(events,symbols,quote_price_factor=a.quote_price_factor,
                                    trade_price_factor=a.trade_price_factor,volume_factor=a.volume_factor,
                                    require_all=not market,interval=interval)
        stats["invalid_json"]=bad
        print(json.dumps(stats,ensure_ascii=False,indent=2))
        if frame.empty:
            print("Không có nhóm snapshot đủ điều kiện. Giữ nguyên toàn bộ dữ liệu đã lưu.")
            return 1
        frame["history_volume_factor"]=a.history_volume_factor
        if market:
            meta=catalog.drop_duplicates("symbol",keep=False).set_index("symbol")
            frame["board"]=frame.symbol.map(meta.board)
            if "stockType" in meta:frame["stockType"]=frame.symbol.map(meta.stockType)
            if "lotSize" in meta:frame["lotSize"]=frame.symbol.map(meta.lotSize)
            frame=frame[frame.board.notna()]
            if frame.empty:raise ValueError("No uniquely mapped exchange symbols")
        out=ROOT/"data/processed/ssi_book_snapshots.parquet"
        # Archive earlier SSI snapshot file before replacing it with the new import.
        if out.exists():
            old=pd.read_parquet(out)
            if set(old.source)!={"ssi_fastconnect_v3_ws"} or set(old.data_kind)!={"live"}:
                raise ValueError("Existing snapshot source mismatch")
            if set(old.history_volume_factor)!={a.history_volume_factor}:
                raise ValueError("History volume factors differ; use a separate dataset")
            # Avoid switching units silently.
            for key,value in (("quote_price_factor",a.quote_price_factor),("trade_price_factor",a.trade_price_factor),("volume_factor",a.volume_factor)):
                if key not in old or set(old[key])!={value}:
                    raise ValueError("Existing snapshot factor missing or differs; archive old SSI file first")
        for key,value in (("quote_price_factor",a.quote_price_factor),("trade_price_factor",a.trade_price_factor),("volume_factor",a.volume_factor)):
            frame[key]=value
        # Output is a separate SSI dataset for this import, not merged with older samples.
        if out.exists():
            import shutil
            from datetime import datetime
            backup=out.with_name("ssi_book_backup_"+datetime.now().strftime("%Y%m%d_%H%M%S_%f")+".parquet")
            shutil.copy2(out,backup)
        out.parent.mkdir(parents=True,exist_ok=True)
        tmp=out.with_suffix(".parquet.tmp")
        frame.to_parquet(tmp,index=False)
        os.replace(tmp,out)
        report=ROOT/"outputs/tables/ssi_ws_quality.json"
        report.parent.mkdir(parents=True,exist_ok=True)
        report.write_text(json.dumps(dict(stats,source="ssi_fastconnect_v3_ws",data_kind="live",
          symbols=symbols,mode="market" if market else "portfolio",interval_seconds=interval,observed_symbols=int(frame.symbol.nunique()),quote_price_factor=a.quote_price_factor,trade_price_factor=a.trade_price_factor,
          volume_factor=a.volume_factor,history_volume_factor=a.history_volume_factor,rows=len(frame),first=str(frame.ts_vn.min()),
          last=str(frame.ts_vn.max())),ensure_ascii=False,indent=2),encoding="utf-8")
        print(f"Đã lưu {len(frame)} dòng SSI, {frame.ts_vn.nunique()} nhóm snapshot đồng bộ.")
        print("Không ghi đè book_snapshots.parquet hoặc OHLCV.")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as e:
        print("Import chưa thành công:",type(e).__name__,str(e))
        return 1

if __name__=="__main__":
    raise SystemExit(main())
