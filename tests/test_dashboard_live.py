"""Offline tests: no SSI credentials or network access required."""
from datetime import datetime, timedelta, timezone
import pandas as pd
import pytest
from src.ingest import ssi_dashboard_live as live
from src.app.live import status_label
from src.app.pages import _keep_recorded_plan
from src.finance.engine import quote_from_row

VN=timezone(timedelta(hours=7))


def test_market_window_uses_continuous_sessions_and_verified_calendar():
    assert live.market_window_seconds("2026-11-30 09:30")==7200
    assert live.market_window_seconds("2026-11-30 14:29")==60
    for stamp in ("2026-11-28 10:00","2026-11-30 12:00","2026-11-30 14:30",
                  "2026-11-24 10:00","2027-01-04 10:00"):
        assert live.market_window_seconds(stamp)==0


def test_fresh_event_required_for_receiving_badge():
    now=datetime(2026,11,30,10,0,tzinfo=VN)
    info=dict(state="receiving_stockinfo",active=True,last_event_vn=now.isoformat())
    assert status_label(info,now)[1]=="success"
    assert status_label(info,now+timedelta(seconds=21))[1]=="warning"
    assert status_label(dict(info,active=False),now)[1]=="warning"
    assert status_label(dict(state="outside_hours",rest_verified=True),now)[1]!="success"


def test_stored_unit_settings_not_guessed(tmp_path):
    path=tmp_path/"snap.parquet"
    df=pd.DataFrame([dict(source="ssi_fastconnect_v3_ws",data_kind="live",
                          quote_price_factor=1.,trade_price_factor=1.,volume_factor=1.,history_volume_factor=1.)])
    df.to_parquet(path,index=False)
    assert live.stored_factors(path)=={key:1. for key in live.FACTORS}
    pd.concat([df,df.assign(volume_factor=100.)]).to_parquet(path,index=False)
    with pytest.raises(ValueError):live.stored_factors(path)


def test_pinned_plan_remains_when_newer_snapshot_is_appended():
    row=dict(symbol="HPG",ts_vn=pd.Timestamp("2026-11-27 10:00",tz="Asia/Ho_Chi_Minh"),
             closePrice=20000,bidPrice1=19950,bidPrice2=19900,bidPrice3=19850,
             bidVol1=1000,bidVol2=1000,bidVol3=1000,data_kind="live")
    previous=("ssi","old",("live",),1);current=("ssi","new",("live",),2)
    state={"ep_params":{"data_kind":"live","snapshot_at":str(row["ts_vn"])},
           "ep_plan_quotes":{"HPG":quote_from_row(row)}}
    new=dict(row,ts_vn=row["ts_vn"]+pd.Timedelta(days=3),closePrice=21000)
    data={"use_ssi":True,"books":pd.DataFrame([row,new])}
    assert _keep_recorded_plan(data,previous,current,state)
    assert not _keep_recorded_plan(dict(data,books=pd.DataFrame([new])),previous,current,state)
    assert not _keep_recorded_plan(dict(data,books=pd.DataFrame([dict(row,bidVol1=2000),new])),previous,current,state)
    assert not _keep_recorded_plan(data,previous,("other","new",("live",),2),state)


def test_worker_authenticates_without_opening_socket_outside_hours(tmp_path,monkeypatch):
    monkeypatch.setenv("SSI_API_KEY","test")
    monkeypatch.setenv("SSI_API_SECRET","test")
    class Client:
        def __init__(self):self.session=self
        def authenticate(self):pass
        def close(self):pass
    monkeypatch.setattr(live,"SSIReadOnlyClient",Client)
    monkeypatch.setattr(live,"market_window_seconds",lambda now:0)
    worker=live.DashboardLive(tmp_path)
    worker._run()
    result=worker.snapshot()
    assert result["state"]=="outside_hours" and result["rest_verified"]
    assert not result["active"] and result["published_batches"]==0


def test_worker_uses_explicit_file_and_append(tmp_path,monkeypatch):
    monkeypatch.setenv("SSI_API_KEY","test")
    monkeypatch.setenv("SSI_API_SECRET","test")
    class Client:
        def __init__(self):self.session=self;self._token="test"
        def authenticate(self):pass
        def close(self):pass
    monkeypatch.setattr(live,"SSIReadOnlyClient",Client)
    monkeypatch.setattr(live,"market_window_seconds",lambda now:120)
    monkeypatch.setattr(live,"stored_factors",lambda path:{k:1. for k in live.FACTORS})
    monkeypatch.setattr(live,"select_catalog",lambda catalog,boards:["HPG"])
    monkeypatch.setattr(live.pd,"read_parquet",lambda *a,**k:pd.DataFrame({"ts_vn":[pd.Timestamp("2026-11-30 10:00",tz="Asia/Ho_Chi_Minh")]}))
    worker=live.DashboardLive(tmp_path)
    async def fake_capture(*args,**kwargs):
        p=kwargs["output_path"];p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text("{}\n",encoding="utf-8")
        kwargs["on_status"]({"state":"receiving_stockinfo","records":1,"last_event_vn":datetime.now(VN).isoformat()})
        return 0
    monkeypatch.setattr(live,"capture",fake_capture)
    def fake_import(argv,backup):
        assert "--append" in argv and "--all-market" in argv and backup
        from pathlib import Path
        assert Path(argv[argv.index("--input")+1]).is_file()
        worker.stop()
        return 0
    monkeypatch.setattr(live,"import_capture",fake_import)
    worker._run()
    assert worker.snapshot()["published_batches"]==1
    assert worker.snapshot()["state"]=="stopped"
