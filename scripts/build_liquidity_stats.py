"""Tạo bảng thống kê thanh khoản từ Parquet ghi trước đó (không tải dữ liệu)."""
from pathlib import Path
import argparse,sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.data.repository import normalize_book
from src.analytics.liquidity import liquidity_statistics
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--min-sessions',type=int,default=5)
    a=p.parse_args()
    books=normalize_book(pd.read_parquet(ROOT/'data/processed/book_snapshots.parquet'))
    stats=liquidity_statistics(books,a.min_sessions)
    out=ROOT/'outputs/tables/liquidity_stats.parquet';out.parent.mkdir(parents=True,exist_ok=True)
    stats.to_parquet(out,index=False)
    print(stats.to_string(index=False))
    print('ADV chỉ mang tính proxy của các ảnh chụp cuối mỗi ngày, không bảo đảm dữ liệu đầy đủ đến đóng cửa.')
