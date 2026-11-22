import pandas as pd
from src.analytics.validation import replay_plans,replay_summary,invariant_check
from src.analytics.planner import calculate
from src.finance.engine import Quote

def test_replay_does_not_forward_fill():
    frame=[]
    for stamp,syms in [('2026-11-18 09:30',['AAA','BBB']),('2026-11-18 09:31',['AAA'])]:
        for sym in syms:
            frame.append({'ts_vn':pd.Timestamp(stamp,tz='Asia/Ho_Chi_Minh'),'symbol':sym,'closePrice':10000,
                'bidPrice1':9950,'bidVol1':10000,'bidPrice2':9900,'bidVol2':10000,
                'bidPrice3':9850,'bidVol3':10000,'data_kind':'synthetic'})
    df,errors=replay_plans(pd.DataFrame(frame),{'AAA':1000,'BBB':1000},1e7)
    assert len(df)==1
    assert errors['incomplete_snapshot']==1
    assert replay_summary(df)['n_sessions']==1

def test_invariants():
    q={'AAA':Quote('AAA',10000,((9950,10000),(9900,1000),(9850,1000))),
       'BBB':Quote('BBB',12000,((11950,10000),(11900,1000),(11850,1000)))}
    h={'AAA':1000,'BBB':1000}
    p=calculate(h,q,10_000_000)
    assert invariant_check(p,h,0,.0)==[]

def test_liquidity_does_not_fabricate_adv():
    from src.analytics.liquidity import liquidity_statistics
    df=pd.DataFrame([dict(symbol='AAA',ts_vn=pd.Timestamp(f'2026-11-{i:02d} 10:00',tz='Asia/Ho_Chi_Minh'),
                          totalTradingVolume=1000*i,closePrice=10000+i,data_kind='synthetic') for i in (10,11,12)])
    row=liquidity_statistics(df).iloc[0]
    assert row['n_sessions']==3
    assert pd.isna(row['adv'])
