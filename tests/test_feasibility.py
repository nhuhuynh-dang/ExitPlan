import pandas as pd
import pytest
from src.finance.engine import Quote
from src.analytics.feasibility import eligible_books,compatible_symbols,liquidation_capacity
from src.data.repository import portfolio_snapshot


def row(symbol,stamp,lot=100,valid=True):
    return dict(symbol=symbol,ts_vn=pd.Timestamp(stamp,tz='Asia/Ho_Chi_Minh'),
                closePrice=10000,bidPrice1=9900,bidVol1=200 if valid else 0,
                bidPrice2=9800,bidVol2=0,bidPrice3=9700,bidVol3=0,
                lotSize=lot,data_kind='live')


def test_compatible_candidates_require_one_timestamp_for_all_holdings():
    a='2026-11-27 10:00:00'
    b='2026-11-27 10:00:30'
    c='2026-11-27 10:01:00'
    books=eligible_books(pd.DataFrame([
        row('AAA',a),row('BBB',a),row('CCC',b),row('AAA',b),
        row('BBB',c),row('CCC',c),row('DDD',a),row('EEE',a,lot=10),
        row('FFF',a,valid=False)]))
    assert compatible_symbols(books,{})=={'AAA','BBB','CCC','DDD'}
    assert compatible_symbols(books,{'AAA':100})=={'BBB','CCC','DDD'}
    assert compatible_symbols(books,{'AAA':100,'BBB':100})=={'DDD'}
    assert compatible_symbols(books,{'AAA':100,'BBB':100,'CCC':100})==set()
    assert set(portfolio_snapshot(books,['AAA','BBB','DDD']).symbol)=={'AAA','BBB','DDD'}


def test_capacity_respects_odd_lots_depth_fees_and_remaining_holdings():
    quotes={'AAA':Quote('AAA',10000,((9900,120),(9800,110))),
            'BBB':Quote('BBB',20000,((19900,1000),))}
    result=liquidation_capacity({'AAA':350,'BBB':50},quotes,.0015,.001)
    assert result['value']==4500000
    assert result['sellable_shares']==200
    assert result['max_net']==pytest.approx((120*9900+80*9800)*.9975)
    assert liquidation_capacity({'BBB':50},quotes,0,0)['max_net']==0


def test_invalid_latest_duplicate_does_not_resurrect_previous_quote():
    stamp='2026-11-27 10:00:00'
    books=eligible_books(pd.DataFrame([row('AAA',stamp),row('AAA',stamp,valid=False)]))
    assert books.empty
    assert compatible_symbols(books,{})==set()
