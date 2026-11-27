"""Kiểm chứng offline trên snapshot đã ghi. Không gọi mạng, không bịa kết quả thực hiện lệnh."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from src.finance.engine import quote_from_row,sell_preview
from src.analytics.planner import calculate


def replay_plans(books,holdings,target,lamb=.5,fee=0.,tax=0.,min_assets=None):
    """Tái tối ưu hóa mỗi snapshot đầy đủ. KHÔNG đo độ chính xác giá khớp thực tế.

    Một timestamp phải có đủ tất cả các mã với bid hợp lệ; không forward fill ngầm.
    """
    if books is None or books.empty:raise ValueError('Không có dữ liệu snapshot')
    rows=[]; reasons={'incomplete_snapshot':0,'failed_optimization':0}
    syms=set(holdings)
    for ts,g in books.sort_values('ts_vn').groupby('ts_vn'):
        latest=g.drop_duplicates('symbol',keep='last')
        if not syms.issubset(set(latest['symbol'])):
            reasons['incomplete_snapshot']+=1;continue
        try:
            q={r['symbol']:quote_from_row(r) for _,r in latest.iterrows() if r['symbol'] in syms}
            if any(not q[s].bids for s in syms):
                reasons['incomplete_snapshot']+=1;continue
            p=calculate(holdings,q,target,lamb,fee,tax)['B']
            rows.append({'snapshot_ts':pd.Timestamp(ts).isoformat(),'plan_id':'B','net':p['net'],
                         'hhi':p['hhi'],'cost':p['cost'],'shortfall':p['shortfall'],
                         'satisfied':p['satisfied'],'data_kind':latest['data_kind'].iloc[0]})
        except (ValueError,RuntimeError):
            reasons['failed_optimization']+=1
    result=pd.DataFrame(rows)
    return result,reasons


def replay_summary(df):
    if df.empty:return {'n':0,'status':'insufficient'}
    # ISO timestamps from replay_plans may include fractional seconds or omit them.
    # Count trading dates in Vietnam, not UTC; normalize any legacy naive times locally.
    def local_date(value):
        ts=pd.Timestamp(value)
        ts=ts.tz_localize('Asia/Ho_Chi_Minh') if ts.tzinfo is None else ts.tz_convert('Asia/Ho_Chi_Minh')
        return ts.date()
    n_sessions=df['snapshot_ts'].map(local_date).nunique()
    return {'n':int(len(df)),'n_sessions':int(n_sessions),
            'target_success_pct':float(df['satisfied'].mean()*100),
            'net_range_vnd':float(df['net'].max()-df['net'].min()),
            'net_cv_pct':float(df['net'].std(ddof=0)/df['net'].mean()*100) if df['net'].mean()>0 else None,
            'hhi_range':float(df['hhi'].max()-df['hhi'].min()),
            'warning':'Độ ổn định mô phỏng, KHÔNG phải kiểm chứng tỷ lệ khớp lệnh thực tế.'}


def invariant_check(plans, holdings, fee_rate, tax_rate, lot=100):
    failures=[]
    for key,p in plans.items():
        details=p['details']
        if any(d['sold']>holdings[d['symbol']] or d['sold']<0 or d['sold']%lot for d in details):
            failures.append(f'{key}: bán vượt vị thế / sai lô')
        if any(d['uncovered']!=0 for d in details):failures.append(f'{key}: vượt sổ lệnh 3 mức')
        if abs(p['net']+p['fee']+p['tax']-p['gross'])>max(.01,p['gross']*1e-10):
            failures.append(f'{key}: gross/net không khớp')
        if not (0<=p['hhi']<=1):failures.append(f'{key}: HHI ngoài [0,1]')
        if p['satisfied']!=(p['net']>=p['target']-.01):failures.append(f'{key}: cờ đạt mục tiêu sai')
    return failures
