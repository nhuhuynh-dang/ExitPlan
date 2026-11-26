"""Phát lại snapshot thật/giả lập với danh mục và phí được cung cấp.
py scripts/validate_recorded.py --holdings HPG:5000 VPB:4000 --target 100000000
"""
import argparse,json,sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.data.repository import normalize_book
from src.analytics.validation import replay_plans,replay_summary
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input',default=None)
    p.add_argument('--interval-seconds',type=int,default=60)
    p.add_argument('--holdings',nargs='+',required=True)
    p.add_argument('--target',type=float,required=True)
    p.add_argument('--lambda-weight',type=float,default=.5)
    p.add_argument('--fee',type=float,default=0.)
    p.add_argument('--tax',type=float,default=0.)
    a=p.parse_args()
    holdings={}
    for item in a.holdings:
        name,qty=item.split(':',1);holdings[name.upper()]=int(qty)
    if a.interval_seconds < 1:p.error('--interval-seconds must be positive')
    ssi=ROOT/'data/processed/ssi_book_snapshots.parquet'
    input_path=ROOT/a.input if a.input else (ssi if ssi.is_file() else ROOT/'data/processed/book_snapshots.parquet')
    data=normalize_book(pd.read_parquet(input_path))
    if data.empty or data['data_kind'].nunique()!=1:
        p.error('Thiếu dữ liệu hoặc trộn loại dữ liệu')
    is_ssi='source' in data and set(data['source'])=={'ssi_fastconnect_v3_ws'}
    if is_ssi:
        from src.data.equity_universe import equity_symbols
        allowed=set(equity_symbols(pd.read_parquet(ROOT/'data/processed/ssi_securities.parquet')))
        unsupported=set(holdings)-allowed
        if unsupported:p.error('Mã ngoài phạm vi cổ phiếu: '+', '.join(sorted(unsupported)))
        data=data[data.symbol.isin(allowed)]
    # Use the earliest actual aligned snapshot per interval, not a fabricated timestamp.
    selected=data[['ts_vn']].drop_duplicates().sort_values('ts_vn')
    selected=selected.groupby(selected['ts_vn'].dt.floor(f'{a.interval_seconds}s')).first()
    sample=data[data['ts_vn'].isin(selected['ts_vn'])]
    df,reasons=replay_plans(sample,holdings,a.target,a.lambda_weight,a.fee,a.tax)
    if df.empty:
        print('Không có kết quả replay hợp lệ. Giữ nguyên kết quả cũ.')
        sys.exit(1)
    suffix='_ssi' if is_ssi else ''
    df['source']='ssi_fastconnect_v3_ws' if is_ssi else 'saved_book'
    df['target_net']=a.target;df['fee_rate']=a.fee;df['tax_rate']=a.tax
    df['lambda_weight']=a.lambda_weight;df['interval_seconds']=a.interval_seconds
    path=ROOT/f'outputs/tables/validation_replay{suffix}.csv';path.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(path,index=False,encoding='utf-8-sig')
    summary={'statistics':replay_summary(df),'skipped':reasons,'sample_interval_seconds':a.interval_seconds,
             'source_kinds':sorted(data['data_kind'].unique().tolist()),'input':str(input_path.name)}
    (ROOT/f'outputs/tables/validation_replay{suffix}_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
