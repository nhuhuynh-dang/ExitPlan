"""MILP rời rạc tính ngoài UI. Mô phỏng ba mức bid; không đặt lệnh.
A: min liquidity cost; B: weighted normalized cost + concentration proxy;
C: min concentration proxy; P: sale-share proximity to proportional benchmark.
HHI thật được báo sau nghiệm; proxy của MILP chỉ chính xác theo mục tiêu thiết kế.
"""
import math
import numpy as np
import pandas as pd
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import lil_matrix
from src.finance.engine import sell_preview, hhi, LOT

STRATEGIES={'A':'Chi phí thấp nhất','B':'Cân bằng','C':'Giảm tập trung','P':'Bán theo tỷ trọng'}

def _candidates(holdings,quotes,fee,tax,lot):
    rows=[]
    for sym,held in holdings.items():
        q=quotes[sym]; depth=sum(v for p,v in q.bids)
        max_qty=min((int(held)//lot)*lot,(int(depth)//lot)*lot)
        for qty in range(0,max_qty+1,lot):
            p=sell_preview(q,qty,fee,tax)
            rows.append(dict(symbol=sym,qty=qty,net=p['net'],gross=p['gross'],cost=p['cost'],
                             fee=p['fee'],tax=p['tax'],remaining=(held-qty)*q.last,held=held,last=q.last))
    return rows

def _solve(candidates,holdings,quotes,target,strategy,lamb,fee,tax,lot,time_limit=16):
    syms=list(holdings)
    by={s:[i for i,c in enumerate(candidates) if c['symbol']==s] for s in syms}
    if any(not a for a in by.values()): raise ValueError('Không có ứng viên cho một hoặc nhiều mã')
    total_value=sum(holdings[s]*quotes[s].last for s in syms)
    max_cash=sum(max(candidates[i]['net'] for i in idx) for idx in by.values())
    achievable=max_cash>=target-0.01
    scale=max(total_value,1.)
    proportional_fraction=min(1.,target/max(total_value,1.))
    max_lot=max((r['net'] for r in candidates if r['qty']==lot),default=0)
    vals=[]
    for r in candidates:
        cost=r['cost']/scale
        conc=(r['remaining']/scale)**2
        prop=(r['qty']/max(r['held'],1)-proportional_fraction)**2
        if not achievable: v=-r['net']/scale
        elif strategy=='A':v=cost + 0.0001*r['net']/scale
        elif strategy=='B':v=(1-lamb)*cost*15 + lamb*conc + 0.0001*r['net']/scale
        elif strategy=='C':v=conc + 0.0001*r['net']/scale
        else:v=prop + 0.0001*r['net']/scale
        vals.append(v)
    n=len(candidates); rows=len(syms)+(2 if achievable else 0)
    mat=lil_matrix((rows,n),dtype=float)
    lower=np.ones(rows); upper=np.ones(rows)
    for j,s in enumerate(syms):mat[j,by[s]]=1
    if achievable:
        mat[len(syms),:]=[r['net']/scale for r in candidates]
        mat[len(syms)+1,:]=[r['net']/scale for r in candidates]
        lower[len(syms)]=target/scale-1e-10; upper[len(syms)]=np.inf
        lower[len(syms)+1]=-np.inf; upper[len(syms)+1]=(target+max_lot+0.01)/scale
    res=milp(np.array(vals)+1e-12*np.arange(n),integrality=np.ones(n),bounds=Bounds(np.zeros(n),np.ones(n)),
             constraints=LinearConstraint(mat.tocsr(),lower,upper),options={'time_limit':time_limit,'mip_rel_gap':1e-4})
    if res.x is None or not res.success:
        raise RuntimeError('MILP chưa tìm được nghiệm hợp lệ. Hãy giảm số mã/lượng nắm giữ hoặc thử lại.')
    selected={s:candidates[max(by[s],key=lambda i:res.x[i])] for s in syms}
    details=[]
    for s in syms:
        c=selected[s]; q=quotes[s]; p=sell_preview(q,int(c['qty']),fee,tax)
        details.append(dict(symbol=s,held=holdings[s],sold=c['qty'],remaining=holdings[s]-c['qty'],
                            last=q.last,before_value=holdings[s]*q.last,after_value=(holdings[s]-c['qty'])*q.last,
                            net=p['net'],gross=p['gross'],liquidity_cost=p['cost'],fee=p['fee'],tax=p['tax'],
                            uncovered=p['uncovered'],visible_depth=sum(v for _,v in q.bids),
                            avg_price=p['avg_price']))
    net=sum(d['net'] for d in details); after=[d['after_value'] for d in details]
    return dict(id=strategy,label=STRATEGIES[strategy],net=net,target=target,satisfied=net>=target-0.01,
                shortfall=max(0,target-net),cost=sum(d['liquidity_cost'] for d in details),
                gross=sum(d['gross'] for d in details),fee=sum(d['fee'] for d in details),
                tax=sum(d['tax'] for d in details),uncovered=sum(d['uncovered'] for d in details),
                hhi=hhi(after),max_weight=max(after)/sum(after) if sum(after)>0 else 0,
                cost_bps=(sum(d['liquidity_cost'] for d in details)/sum(d['gross'] for d in details)*10000
                          if sum(d['gross'] for d in details)>0 else 0),details=details,
                status='optimal',achievable=achievable)

def calculate(holdings,quotes,target_net,lamb=0.5,fee_rate=0.0015,tax_rate=0.001,lot=LOT):
    if not holdings or any(s not in quotes or not quotes[s].bids for s in holdings):
        raise ValueError('Mọi mã trong danh mục phải có dữ liệu bid hợp lệ')
    if target_net<=0 or not math.isfinite(target_net):raise ValueError('Mục tiêu phải dương')
    if not 0<=lamb<=1:raise ValueError('λ phải thuộc 0–1')
    if fee_rate<0 or tax_rate<0 or fee_rate+tax_rate>=1:raise ValueError('Phí/thuế không hợp lệ')
    if len(holdings)>12:raise ValueError('Bản nguyên mẫu hỗ trợ tối đa 12 mã để giới hạn bài toán MILP')
    if any(int(v)!=v or v<0 for v in holdings.values()):raise ValueError('Số cổ phiếu phải nguyên không âm')
    candidates=_candidates(holdings,quotes,fee_rate,tax_rate,lot)
    plans={}
    for sid in STRATEGIES:
        plans[sid]=_solve(candidates,holdings,quotes,target_net,sid,lamb,fee_rate,tax_rate,lot)
    return plans

def summaries(plans):
    return pd.DataFrame([dict(phuong_an=k,ten=p['label'],net=p['net'],liquidity_cost=p['cost'],
                              cost_bps=p['cost_bps'],uncovered=p['uncovered'],hhi=p['hhi'],
                              max_weight=p['max_weight'],satisfied=p['satisfied']) for k,p in plans.items()])

def frontier(holdings,quotes,target,fee,tax,points=(0.,.2,.4,.6,.8,1.)):
    variants=_candidates(holdings,quotes,fee,tax,LOT)
    rows=[]
    for lam in points:
        p=_solve(variants,holdings,quotes,target,'B',lam,fee,tax,LOT)
        rows.append(dict(lamb=lam,net=p['net'],cost=p['cost'],hhi=p['hhi'],
                         max_weight=p['max_weight'],satisfied=p['satisfied']))
    return pd.DataFrame(rows)
