"""The overview counts only book symbols with verified daily liquidity metrics."""
import pandas as pd
from src.app.pages import _overview_history_kpi


def test_overview_history_kpi_counts_only_complete_finite_ssi_book_symbols():
    def row(sym,**kwargs):
        return dict(dict(symbol=sym,adv=1000.,sigma=.02,quality_status="complete",
                         source="ssi_fastconnect_v3",data_kind="historical"),**kwargs)
    stats=pd.DataFrame([row("HPG"),row("HPG"),row("ACB",quality_status="stale"),
                        row("VPB",sigma=float("nan")),row("TCB",adv=float("inf")),
                        row("VIC",source="other"),row("FPT")])
    data=dict(use_ssi=True,liquidity=stats,liquidity_err=None)
    card=_overview_history_kpi(data,["HPG","ACB","VPB","TCB","VIC"])
    assert card["value"]=="1" and "1/5" in card["note"]
    assert _overview_history_kpi(data,["ACB"])["value"]=="0"


def test_overview_history_kpi_unavailable_not_zero():
    assert _overview_history_kpi(dict(use_ssi=False),["HPG"])["value"]=="–"
    assert _overview_history_kpi(dict(use_ssi=True,liquidity=None),["HPG"])["value"]=="–"
    assert _overview_history_kpi(dict(use_ssi=True,liquidity_err="read error"),["HPG"])["value"]=="–"
