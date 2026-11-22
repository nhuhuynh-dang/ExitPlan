from datetime import date
import pandas as pd
import pytest
from src.ingest.ssi_iboard import fetch_symbol,normalize_history,liquidity_from_history,SSIDataError
class FakeResp:
    status_code=200
    headers={'Content-Type':'application/json'}
    text=''
    def json(self):return {'code':'SUCCESS','data':[{'symbol':'HPG','tradingDate':'03/11/2026','close':'28000','volume':'10000'}], 'paging':{'total':1}}
class FakeSession:
    def __init__(self):self.params=None
    def get(self,url,params,timeout):self.params=params;return FakeResp()
def test_fetch_date_params_and_page():
    s=FakeSession();r=fetch_symbol(s,'HPG',date(2026,11,1),date(2026,11,20))
    assert len(r)==1
    assert s.params['fromDate']=='01/11/2026' and s.params['toDate']=='20/11/2026'
def test_history_normalization_and_no_book():
    frame=normalize_history([{'symbol':'HPG','tradingDate':'03/11/2026','close':'28000','volume':'10000'}])
    assert frame['close'].iloc[0]==28000
    assert 'bidPrice1' not in frame
    assert frame['data_kind'].iloc[0]=='historical'
def test_adv_requires_20_sessions():
    rows=[{'symbol':'HPG','tradingDate':f'{i+1:02d}/10/2026','close':str(20000+i),'volume':'10000'} for i in range(20)]
    h=normalize_history(rows)
    stats=liquidity_from_history(h)
    assert stats['adv'].iloc[0]==10000
    assert stats['n_sessions'].iloc[0]==20
    assert pd.isna(liquidity_from_history(h.iloc[:19])['adv'].iloc[0])
