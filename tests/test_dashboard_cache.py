"""File-version caching regression checks without calling SSI."""
import pandas as pd
from src.app import pages


def test_dashboard_cache_reuses_prepared_books_and_invalidates_on_write(tmp_path,monkeypatch):
    path=tmp_path/pages.SNAPSHOT
    path.parent.mkdir(parents=True)
    row=dict(symbol="HPG",ts_vn=pd.Timestamp("2026-11-27 10:00",tz="Asia/Ho_Chi_Minh"),
             closePrice=20000,bidPrice1=19950,bidPrice2=19900,bidPrice3=19850,
             bidVol1=1000,bidVol2=1000,bidVol3=1000,data_kind="synthetic")
    pd.DataFrame([row]).to_parquet(path,index=False)
    original=pages.normalize_book
    calls=[]
    def counted(frame):
        calls.append(len(frame))
        return original(frame)
    monkeypatch.setattr(pages,"normalize_book",counted)
    pages._load_market_files.clear()
    try:
        def load():
            return pages._load_market_files(str(tmp_path),{},pages._data_versions(tmp_path,{}))
        first=load()
        first["books"].loc[:,"closePrice"]=1
        second=load()
        assert second["books"].closePrice.tolist()==[20000]
        assert calls==[1]
        pd.DataFrame([row,dict(row,ts_vn=row["ts_vn"]+pd.Timedelta(minutes=1))]).to_parquet(path,index=False)
        assert len(load()["books"])==2
        assert calls==[1,2]
    finally:
        pages._load_market_files.clear()


def test_ssi_stats_cache_invalidates_when_history_changes(tmp_path,monkeypatch):
    from src.analytics import ssi_history_stats as analytics
    path=tmp_path/"data/processed/ssi_history.parquet"
    path.parent.mkdir(parents=True)
    asof=pd.Timestamp("2026-11-27").date()
    frame=pd.DataFrame([dict(symbol="HPG",tradingDate=d,close=20000+i*10,
                             volume=1000,source="ssi_fastconnect_v3",data_kind="historical")
                        for i,d in enumerate(analytics.expected_sessions(asof))])
    frame.to_parquet(path,index=False)
    original=analytics.asof_history_stats
    calls=[]
    def counted(*args,**kwargs):
        calls.append(1)
        return original(*args,**kwargs)
    monkeypatch.setattr(analytics,"asof_history_stats",counted)
    pages._cached_market_parquet.clear()
    pages._cached_ssi_stats.clear()
    try:
        assert pages._ssi_stats(tmp_path,asof,{"HPG"}).adv.iloc[0]==1000
        assert pages._ssi_stats(tmp_path,asof,{"HPG"}).adv.iloc[0]==1000
        assert len(calls)==1
        frame.assign(volume=12345).to_parquet(path,index=False)
        assert pages._ssi_stats(tmp_path,asof,{"HPG"}).adv.iloc[0]==12345
        assert len(calls)==2
    finally:
        pages._cached_market_parquet.clear()
        pages._cached_ssi_stats.clear()
