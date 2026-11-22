"""Fetch SSI iBoard community-documented DAILY OHLCV; separate from live order book."""
import argparse
import sys
from datetime import datetime,date,timedelta
from pathlib import Path
import time
import requests
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from src.ingest.ssi_iboard import SSIDataError,fetch_symbol,normalize_history,liquidity_from_history

def parse_date(value):
    try:return datetime.strptime(value,'%d/%m/%Y').date()
    except ValueError as exc:raise argparse.ArgumentTypeError('Ngày phải có dạng DD/MM/YYYY') from exc

def main():
    cli=argparse.ArgumentParser(description='SSI iBoard community endpoint: history only, no order book')
    cli.add_argument('--symbols',nargs='+',default=['HPG','VPB','ACB'])
    cli.add_argument('--from-date',type=parse_date,default=date.today()-timedelta(days=75))
    cli.add_argument('--to-date',type=parse_date,default=date.today())
    cli.add_argument('--pages',type=int,default=10)
    args=cli.parse_args()
    if args.from_date>args.to_date:cli.error('from-date phải <= to-date')
    session=requests.Session();session.headers.update({'Accept':'application/json','User-Agent':'ExitPlan-Academic-Research/0.2'})
    all_rows=[];errors=[]
    for raw in args.symbols:
        sym=raw.strip().upper()
        if not sym.isalnum():errors.append(f'{raw}: mã không hợp lệ');continue
        try:
            rows=fetch_symbol(session,sym,args.from_date,args.to_date,max_pages=max(1,min(args.pages,20)))
            all_rows.extend(rows);print(f'{sym}: nhận {len(rows)} bản ghi')
        except (requests.RequestException,SSIDataError) as exc:
            msg=str(exc);print('Lỗi:',msg);errors.append(msg)
            if 'HTTP 403' in msg or 'HTTP 429' in msg:
                print('Dừng: quyền truy cập/băng thông giới hạn; không vượt cơ chế bảo vệ.')
                break
        time.sleep(0.8)
    history=normalize_history(all_rows)
    if history.empty:
        print('Không lấy được lịch sử hợp lệ. Không sửa hoặc tạo file dữ liệu hiện có.')
        return 1
    raw=ROOT/'data/raw';raw.mkdir(parents=True,exist_ok=True)
    processed=ROOT/'data/processed';processed.mkdir(parents=True,exist_ok=True)
    stats_dir=ROOT/'outputs/tables';stats_dir.mkdir(parents=True,exist_ok=True)
    history.to_csv(raw/'ssi_iboard_ohlcv.csv',index=False,encoding='utf-8-sig')
    history.to_parquet(processed/'ssi_history.parquet',index=False)
    stats=liquidity_from_history(history)
    stats.to_parquet(stats_dir/'ssi_liquidity_stats.parquet',index=False)
    print(f'OK: {len(history)} dòng, {history.symbol.nunique()} mã; đã tạo SSI history + ADV. Lưu ý KHÔNG có bidPrice/bidVol từ API này.')
    for error in errors:print('Chưa thành công:',error)
    return 0
if __name__=='__main__':sys.exit(main())
