import json
import pandas as pd
import pytest
from src.ingest.pipeline import normalize_event,ingest_jsonl

MSG={'channel':'stockInfo','data':{'symbol':'HPG','closePrice':29800,'bidPrice1':'29750.0','bidVol1':293000,
' bidPrice2':29700,'bidPrice2':29700,'bidVol2':208800,'bidPrice3':29650,'bidVol3':25900,
'askPrice1':'ATO','totalTradingVolume':5736600}}

def test_normalize_example():
    rows,stats=normalize_event(MSG,'2026-11-18T09:31:05+07:00','live')
    assert stats['accepted']==1
    assert rows[0]['bidPrice1']==29750
    assert rows[0]['askPrice1'] is None
    assert rows[0]['ts_vn'].hour==9
    assert rows[0]['timestamp_semantics']=='received_at_vn'

def test_no_fake_bid_or_cross_channel():
    rows,s=normalize_event({'channel':'stockInfo','data':{'symbol':'HPG','closePrice':10000,'bidPrice1':'ATO','bidVol1':100}},'2026-11-18 10:00')
    assert rows and s['no_executable_bid']==1
    assert normalize_event({'channel':'marketInfo','symbol':'VNINDEX','closePrice':1})[0]==[]

def test_invalid_negative_and_nan():
    msg={'symbol':'AAA','closePrice':100,'bidPrice1':99,'bidVol1':-100}
    rows,stats=normalize_event(msg)
    assert not rows and stats['invalid_bid_volume']==1
    assert not normalize_event({'symbol':'AAA','closePrice':float('nan')})[0]

def test_import_requires_timestamp(tmp_path):
    inp=tmp_path/'in.jsonl'
    inp.write_text(json.dumps(MSG)+'\n')
    with pytest.raises(ValueError,match='Không có snapshot'):
        ingest_jsonl(inp,tmp_path/'book.parquet',tmp_path/'quality.csv',data_kind='historical')

def test_import_if_parquet_available(tmp_path):
    pytest.importorskip('pyarrow')
    inp=tmp_path/'in.jsonl'
    wrapper={'received_at':'2026-11-18T09:31:05+07:00','message':MSG}
    inp.write_text(json.dumps(wrapper)+'\n'+json.dumps(wrapper)+'\n')
    result=ingest_jsonl(inp,tmp_path/'book.parquet',tmp_path/'quality.csv',data_kind='live')
    assert result['rows']==1 and result['stats']['duplicate_rows']==1
    assert pd.read_parquet(tmp_path/'book.parquet').iloc[0]['symbol']=='HPG'
