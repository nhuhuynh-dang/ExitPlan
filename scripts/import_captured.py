"""Import NDJSON stockInfo đã thu được. Không gọi NEO API.
py scripts/import_captured.py --input data/raw/stockinfo.jsonl --kind live
"""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.ingest.pipeline import ingest_jsonl,write_status

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True)
    ap.add_argument('--kind',choices=['live','historical','synthetic'],default='live')
    ap.add_argument('--append',action='store_true')
    args=ap.parse_args()
    result=ingest_jsonl(args.input,ROOT/'data/processed/book_snapshots.parquet',
                        ROOT/'outputs/tables/data_quality.csv',data_kind=args.kind,append=args.append)
    write_status(ROOT/'outputs/tables/recorder_status.json',state='import_complete',
                 data_kind=args.kind,channel='stockInfo',last_update_vn=result['last'],
                 records=result['rows'],sessions=result['sessions'],
                 message='Đã nhập từ dữ liệu ghi trước đó; KHÔNG xác nhận kết nối WS hiện tại.')
    print(json.dumps(result,ensure_ascii=False,indent=2))
