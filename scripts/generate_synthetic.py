"""Chỉ sinh DỮ LIỆU GIẢ LẬP, không kết nối NEO API. python scripts/generate_synthetic.py"""
from pathlib import Path
import sys,json
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from src.finance.engine import quote_from_row
from src.analytics.planner import calculate,summaries,frontier
VN=ZoneInfo('Asia/Ho_Chi_Minh')


def run():
    out=ROOT/'data/processed';out.mkdir(parents=True,exist_ok=True)
    tables=ROOT/'outputs/tables';tables.mkdir(parents=True,exist_ok=True)
    # Deliberately constructed illustrative prices and depth; not market evidence.
    symbols={'HPG':(28000,24000),'VPB':(20000,17000),'ACB':(25000,21000),'FPT':(105000,9000)}
    dates=['2026-10-12','2026-10-13','2026-10-14','2026-10-15','2026-10-16']
    rows=[]
    for di,date in enumerate(dates):
        for step,hour in enumerate(['09:45:00','10:30:00','11:10:00','13:35:00','14:15:00']):
            ts=pd.Timestamp(f'{date} {hour}',tz='Asia/Ho_Chi_Minh')
            for j,(s,(price,vol)) in enumerate(symbols.items()):
                last=price+([0,50,-100,50,150][di])+([0,50,-50,0,50][step])*(j+1)
                depth=vol+di*1000+step*300
                rows.append(dict(ts_vn=ts,symbol=s,closePrice=last,totalTradingVolume=(di+1)*200000+step*17000+j*60000,
                    bidPrice1=last-50,bidVol1=depth,bidPrice2=last-100,bidVol2=int(depth*.73),
                    bidPrice3=last-150,bidVol3=int(depth*.48),askPrice1=last+50,askVol1=int(depth*.34),
                    refPrice=price,ceilingPrice=int(price*1.07),floorPrice=int(price*.93),data_kind='synthetic'))
    data=pd.DataFrame(rows)
    data.to_parquet(out/'book_snapshots.parquet',index=False)
    stats=pd.DataFrame([dict(symbol=s,adv=float([800000,1000000,620000,310000][i]),
                             sigma=float([.02,.018,.015,.024][i]),n_sessions=5,data_kind='synthetic')
                        for i,s in enumerate(symbols)])
    stats.to_parquet(tables/'liquidity_stats.parquet',index=False)
    quality=pd.DataFrame([dict(symbol=s,records=len(g),missing_bid=int(g[['bidPrice1','bidVol1']].isna().any(axis=1).sum()),
         duplicates=int(g.duplicated(subset=['ts_vn','symbol']).sum()),invalid_rows=0,
         missing_pct=0.,duplicate_pct=0.,invalid_pct=0.,data_kind='synthetic') for s,g in data.groupby('symbol')])
    quality.to_csv(tables/'data_quality.csv',index=False,encoding='utf-8-sig')
    last=data.sort_values('ts_vn').drop_duplicates('symbol',keep='last')
    quotes={r.symbol:quote_from_row(r._asdict()) for r in last.itertuples(index=False)}
    holdings={'HPG':5000,'VPB':4000,'ACB':3000}
    # Assumptions used only for synthetic showcase; TODO confirm actual fee/tax.
    assumptions={'fee_rate':0.0015,'tax_rate':0.001,'target':100_000_000,'lambda':0.5}
    plans=calculate(holdings,quotes,assumptions['target'],assumptions['lambda'],
                    assumptions['fee_rate'],assumptions['tax_rate'])
    plan_df=summaries(plans);plan_df['data_kind']='synthetic';plan_df.to_parquet(tables/'plans.parquet',index=False)
    fr=frontier(holdings,quotes,assumptions['target'],assumptions['fee_rate'],assumptions['tax_rate'])
    fr['data_kind']='synthetic';fr.to_parquet(tables/'frontier.parquet',index=False)
    sensitivity=[]
    for lam in [.0,.25,.5,.75,1.]:
        p=calculate(holdings,quotes,assumptions['target'],lam,assumptions['fee_rate'],assumptions['tax_rate'])['B']
        sensitivity.append(dict(variable='λ',value=lam,net=p['net'],cost=p['cost'],hhi=p['hhi'],data_kind='synthetic'))
    for fee in [0.,.001,.002,.003]:
        p=calculate(holdings,quotes,assumptions['target'],.5,fee,assumptions['tax_rate'])['B']
        sensitivity.append(dict(variable='Phí bán',value=fee,net=p['net'],cost=p['cost'],hhi=p['hhi'],data_kind='synthetic'))
    pd.DataFrame(sensitivity).to_csv(tables/'validation_sensitivity.csv',index=False,encoding='utf-8-sig')
    # A synthetic replay comparison is illustrative only, never an out-of-sample claim.
    replay=[]
    for ts,g in data[data['symbol'].isin(holdings)].groupby('ts_vn'):
        q={r.symbol:quote_from_row(r._asdict()) for r in g.itertuples(index=False)}
        p=calculate(holdings,q,assumptions['target'],.5,assumptions['fee_rate'],assumptions['tax_rate'])['B']
        replay.append(dict(snapshot_ts=ts.isoformat(),plan_id='B',net=p['net'],hhi=p['hhi'],
                           cost=p['cost'],data_kind='synthetic'))
    pd.DataFrame(replay).to_csv(tables/'validation_replay.csv',index=False,encoding='utf-8-sig')
    status={'state':'synthetic_only','data_kind':'synthetic','channel':'stockInfo',
        'last_update_vn':str(data['ts_vn'].max()),'records':len(data),
        'message':'GIẢ LẬP — không có kết nối WebSocket thật.'}
    (tables/'recorder_status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Đã tạo file GIẢ LẬP:',out/'book_snapshots.parquet',tables)

if __name__=='__main__':run()
