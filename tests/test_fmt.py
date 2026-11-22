from src.app import fmt

def test_vietnamese_num():
    assert fmt.num(1234567.89,2)=='1.234.567,89'
    assert fmt.num(-9876.5,1)=='−9.876,5'
    assert fmt.num(None)=='–'

def test_vnd_and_shares():
    assert fmt.vnd(1200000)=='1.200.000 ₫'
    assert fmt.shares(1500)=='1.500 CP'
    assert fmt.pct(.125,1)=='12,5%'
    assert fmt.rank(3)=='#3'
    assert fmt.bps(.0005)=='0,0005'
