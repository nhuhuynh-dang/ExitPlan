import pandas as pd
import pytest
from src.analytics.ssi_history_stats import expected_sessions,asof_history_stats
from scripts.ssi_market_history import ready_history_symbols


def bars(symbol,dates):
    return [dict(symbol=symbol,tradingDate=day,close=10000+i*10,volume=1000,
                 source="ssi_fastconnect_v3",data_kind="historical") for i,day in enumerate(dates)]


def test_calendar_excludes_november_24_and_national_day():
    dates=expected_sessions("2026-11-27")
    assert len(dates)==21
    assert dates[-1]==pd.Timestamp("2026-11-26")
    assert pd.Timestamp("2026-11-24") not in dates
    sept=expected_sessions("2026-09-04")
    assert not set(pd.to_datetime(["2026-08-31","2026-09-01","2026-09-02"])) & set(sept)
    assert expected_sessions("2027-11-27") is None


def test_strict_calendar_marks_stale_and_missing_without_imputation():
    days=expected_sessions("2026-11-27",24)
    rows=bars("FULL",days)+bars("STALE",days[:-1])+bars("GAP",days.delete(-5))
    stats=asof_history_stats(pd.DataFrame(rows),"2026-11-27",strict_calendar=True).set_index("symbol")
    assert stats.loc["FULL","quality_status"]=="complete"
    assert stats.loc["FULL","adv"]==1000
    assert pd.notna(stats.loc["FULL","sigma"])
    assert stats.loc["STALE","quality_status"]=="stale"
    assert stats.loc["GAP","quality_status"]=="missing_sessions"
    assert pd.isna(stats.loc["STALE","adv"])
    assert pd.isna(stats.loc["GAP","sigma"])
    assert ready_history_symbols(pd.DataFrame(rows),"2026-11-27",True)=={"FULL"}


def test_adv_can_be_valid_with_missing_first_close_but_sigma_cannot():
    days=expected_sessions("2026-11-27")
    data=pd.DataFrame(bars("HPG",days[1:])+bars("HPG",[pd.Timestamp("2026-11-27")]))
    s=asof_history_stats(data,"2026-11-27",strict_calendar=True).iloc[0]
    assert s.adv==1000
    assert pd.isna(s.sigma)
    assert s.missing_session_count==1
    assert s.asof_date=="2026-11-26"


def test_unknown_calendar_does_not_silently_assume_weekdays():
    d=pd.DataFrame(bars("HPG",pd.bdate_range(end="2027-11-25",periods=22)))
    s=asof_history_stats(d,"2027-11-26",strict_calendar=True).iloc[0]
    assert s.quality_status=="calendar_unavailable"
    assert pd.isna(s.adv) and pd.isna(s.sigma)
