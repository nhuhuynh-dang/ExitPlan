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
    p.add_argument('--input',default='data/processed/book_snapshots.parquet')
    p.add_argument('--holdings',nargs='+',required=True)
    p.add_argument('--target',type=float,required=True)
    p.add_argument('--lambda-weight',type=float,default=.5)
    p.add_argument('--fee',type=float,default=0.)
    p.add_argument('--tax',type=float,default=0.)
    a=p.parse_args()
    holdings={}
    for item in a.holdings:
        name,qty=item.split(':',1);holdings[name.upper()]=int(qty)
    data=normalize_book(pd.read_parquet(ROOT/a.input))
    df,reasons=replay_plans(data,holdings,a.target,a.lambda_weight,a.fee,a.tax)
    path=ROOT/'outputs/tables/validation_replay.csv';path.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(path,index=False,encoding='utf-8-sig')
    summary={'statistics':replay_summary(df),'skipped':reasons,
             'source_kinds':sorted(data['data_kind'].unique().tolist())}
    (ROOT/'outputs/tables/validation_replay_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
