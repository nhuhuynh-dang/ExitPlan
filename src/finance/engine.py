"""Hàm tài chính thuần: chi phí và thanh lý trên ảnh chụp ba mức bid."""
from dataclasses import dataclass
import math

LOT = 100
@dataclass(frozen=True)
class Quote:
    symbol: str
    last: float
    bids: tuple
    ask1: float | None = None
    volume: float | None = None
    kind: str = 'synthetic'
    updated_at: str = ''

def quote_from_row(row):
    s=str(row['symbol']).strip().upper()
    last=float(row['closePrice'])
    if not s or not math.isfinite(last) or last<=0:
        raise ValueError(f'{s}: giá hoặc mã không hợp lệ')
    bids=[]
    for i in range(1,4):
        try:
            p=float(row[f'bidPrice{i}']); v=float(row[f'bidVol{i}'])
        except (KeyError,TypeError,ValueError):
            continue  # ATO/ATC hoặc thiếu dữ liệu: không coi là mức giá khả dụng
        if math.isfinite(p) and math.isfinite(v) and p>0 and v>0:
            bids.append((p,int(v)))
    bids.sort(reverse=True)
    if len({p for p,v in bids})!=len(bids):
        raise ValueError(f'{s}: mức bid bị trùng')
    ask=row.get('askPrice1')
    try: ask=float(ask) if ask is not None and math.isfinite(float(ask)) else None
    except (TypeError,ValueError): ask=None
    vol=row.get('totalTradingVolume')
    try: vol=float(vol) if vol is not None else None
    except (TypeError,ValueError): vol=None
    return Quote(s,last,tuple(bids),ask,vol,str(row.get('data_kind','synthetic')),str(row.get('ts_vn','')))

def sell_preview(q:Quote, qty:int, fee_rate:float, tax_rate:float):
    if qty<0 or fee_rate<0 or tax_rate<0 or fee_rate+tax_rate>=1:
        raise ValueError('Số lượng/phí/thuế không hợp lệ')
    left=int(qty); gross=0.; covered=0
    for price,volume in q.bids:
        k=min(left,volume)
        gross+=k*price; covered+=k; left-=k
        if left<=0:break
    fee=gross*fee_rate; tax=gross*tax_rate
    # lower bound: no further executable bid assumed; upper is optimistic last price for uncovered.
    optimistic=max(0,left)*q.last*(1-fee_rate-tax_rate)
    return dict(qty=qty,covered=covered,uncovered=left,gross=gross,
                fee=fee,tax=tax,net=gross-fee-tax,
                avg_price=gross/covered if covered else None,
                cost=max(0,covered*q.last-gross),
                bound_low=gross-fee-tax, bound_high=gross-fee-tax+optimistic)

def hhi(values):
    total=sum(values)
    return sum((v/total)**2 for v in values) if total>0 else 0.
