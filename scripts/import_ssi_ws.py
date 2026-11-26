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
    p=argparse.ArgumentParser(description="Normalize SSI captures for HOSE continuous-session simulation")
    p.add_argument("--input", nargs="+", help="JSONL files; default: all data/raw/ssi_ws/*.jsonl")
    p.add_argument("--symbols", nargs="+", required=True)
    p.add_argument("--quote-price-factor", type=float, required=True)
    p.add_argument("--trade-price-factor", type=float, required=True)
    p.add_argument("--volume-factor", type=float, required=True)
    p.add_argument("--history-volume-factor", type=float, required=True, help="Confirmed daily OHLCV volume to shares multiplier")
    a=p.parse_args()
    if not math.isfinite(a.history_volume_factor) or a.history_volume_factor <= 0:
        p.error("Invalid history volume factor")
    symbols=sorted(set(s.strip().upper() for s in a.symbols))
    paths=[Path(x) for x in a.input] if a.input else sorted((ROOT/"data/raw/ssi_ws").glob("*.jsonl"))
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
                        events.append(r)
                    except ValueError:
                        bad+=1
        frame,stats=build_snapshots(events,symbols,quote_price_factor=a.quote_price_factor,
                                    trade_price_factor=a.trade_price_factor,volume_factor=a.volume_factor)
        stats["invalid_json"]=bad
        print(json.dumps(stats,ensure_ascii=False,indent=2))
        if frame.empty:
            print("Không có nhóm snapshot đủ điều kiện. Giữ nguyên toàn bộ dữ liệu đã lưu.")
            return 1
        frame["history_volume_factor"]=a.history_volume_factor
        out=ROOT/"data/processed/ssi_book_snapshots.parquet"
        out.parent.mkdir(parents=True,exist_ok=True)
        tmp=out.with_suffix(".parquet.tmp")
        frame.to_parquet(tmp,index=False)
        os.replace(tmp,out)
        report=ROOT/"outputs/tables/ssi_ws_quality.json"
        report.parent.mkdir(parents=True,exist_ok=True)
        report.write_text(json.dumps(dict(stats,source="ssi_fastconnect_v3_ws",data_kind="live",
          symbols=symbols,quote_price_factor=a.quote_price_factor,trade_price_factor=a.trade_price_factor,
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
