"""Community-documented SSI iBoard history adapter (NOT official FastConnect).
Read-only, access-respecting requests; no bypass of access controls.
"""
from datetime import datetime
import time
import pandas as pd
import requests

URL = 'https://iboard-api.ssi.com.vn/statistics/company/ssmi/stock-info'
COLUMNS = ['symbol','tradingDate','open','high','low','close','volume','closePriceAdjusted','totalMatchVol','refPrice']

class SSIDataError(RuntimeError):
    pass

def fetch_symbol(session, symbol, start, end, page_size=50, max_pages=10, delay=0.8):
    rows=[]
    for page in range(1,max_pages+1):
        resp=session.get(URL,params={'symbol':symbol,'page':page,'pageSize':page_size,
                          'fromDate':start.strftime('%d/%m/%Y'),
                          'toDate':end.strftime('%d/%m/%Y')},timeout=20)
        if resp.status_code!=200:
            detail=' '.join(resp.text[:350].split())
            raise SSIDataError(f'{symbol} HTTP {resp.status_code}: {detail}')
        if 'json' not in resp.headers.get('Content-Type','').lower():
            raise SSIDataError(f'{symbol}: phản hồi không phải JSON')
        try: body=resp.json()
        except ValueError as exc: raise SSIDataError(f'{symbol}: JSON lỗi') from exc
        if body.get('code')!='SUCCESS' or not isinstance(body.get('data'),list):
            raise SSIDataError(f'{symbol}: {str(body.get("message") or body)[:240]}')
        page_rows=body['data'];rows.extend(page_rows)
        total=(body.get('paging') or {}).get('total')
        if not page_rows or len(page_rows)<page_size or (isinstance(total,int) and len(rows)>=total):break
        if page<max_pages:time.sleep(delay)
    return rows

def normalize_history(records,source='ssi_iboard_community_doc'):
    if not records:return pd.DataFrame()
    frame=pd.DataFrame([{k:r.get(k) for k in COLUMNS} for r in records])
    frame['symbol']=frame['symbol'].astype(str).str.strip().str.upper()
    frame['tradingDate']=pd.to_datetime(frame['tradingDate'],format='%d/%m/%Y',errors='coerce')
    numeric=['open','high','low','close','volume','closePriceAdjusted','totalMatchVol','refPrice']
    for name in numeric:frame[name]=pd.to_numeric(frame[name],errors='coerce')
    frame=frame.dropna(subset=['tradingDate','close','volume'])
    frame=frame[(frame['close']>0)&(frame['volume']>=0)&frame['symbol'].str.fullmatch(r'[A-Z0-9]{1,10}')]
    frame=frame.drop_duplicates(['symbol','tradingDate'],keep='last').sort_values(['symbol','tradingDate']).reset_index(drop=True)
    frame['data_kind']='historical'
    frame['source']=source
    return frame

def liquidity_from_history(history,window=20):
    """ADV over last `window` distinct trading sessions; no proxy from order book.
    sigma: sample standard deviation of close-to-close pct returns. NULL if insufficient.
    """
    output=[]
    for symbol,group in history.groupby('symbol'):
        g=group.sort_values('tradingDate').tail(window)
        vol=pd.to_numeric(g['volume'],errors='coerce')
        prices=pd.to_numeric(g['close'],errors='coerce')
        n=int(vol.notna().sum())
        output.append(dict(symbol=symbol,adv=float(vol.mean()) if n>=window else float('nan'),
          sigma=float(prices.pct_change().std()) if n>=window else float('nan'),
          n_sessions=n,data_kind='historical',source='ssi_iboard_community_doc',adv_window=window))
    return pd.DataFrame(output)
