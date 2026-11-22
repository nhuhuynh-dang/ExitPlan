import pytest
from src.finance.engine import Quote,sell_preview,hhi
from src.analytics.planner import calculate,summaries

Q={'AAA':Quote('AAA',10000,((9950,1000),(9900,1000),(9850,1000))),
   'BBB':Quote('BBB',12000,((11950,1000),(11900,1000),(11850,1000)))}

def test_sell_preview_and_bounds():
    r=sell_preview(Q['AAA'],3500,.001,.001)
    assert r['covered']==3000 and r['uncovered']==500
    assert r['bound_low']<r['bound_high']
    assert abs(r['net']-(9950+9900+9850)*1000*.998)<1e-6

def test_hhi():
    assert hhi([100,100])==.5
    assert hhi([0,0])==0

def test_optimizer():
    plans=calculate({'AAA':2000,'BBB':2000},Q,20_000_000,.5,0,0)
    assert set(plans)=={'A','B','C','P'}
    for p in plans.values():
        assert p['satisfied']
        assert all(0<=r['sold']<=r['held'] and r['sold']%100==0 for r in p['details'])
        assert abs(p['net']+p['fee']+p['tax']-p['gross'])<1e-5

def test_infeasible_and_missing():
    p=calculate({'AAA':2000},Q,1_000_000_000)['B']
    assert not p['satisfied'] and p['shortfall']>0
    with pytest.raises(ValueError):calculate({'ZZZ':1000},Q,10000)
