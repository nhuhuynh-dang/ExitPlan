"""Presentation-only regression checks for ExitPlan overview."""
import pandas as pd
import pytest
from src.app import charts
from src.app.pages import _overview_kpis, _overview_status
from src.app.theme import overview_css

@pytest.mark.parametrize("mode",["Sáng","Tối"])
def test_overview_chart_keeps_normalized_values_and_hover(mode):
    df=pd.DataFrame({
        "symbol":["HPG","HPG","ACB","ACB"],
        "ts_vn":pd.to_datetime(["2026-11-27 10:00","2026-11-27 10:01"]*2),
        "closePrice":[20000,20100,19000,18900],
    })
    original=df.copy(deep=True)
    t=charts.apply_palette(mode,"#2563EB")
    before=charts.time_fig(df,t,normalize=True)
    after=charts.overview_time_fig(df,t)
    assert len(before.data)==len(after.data)==2
    for old,new in zip(before.data,after.data):
        assert list(old.x)==list(new.x)
        assert list(old.y)==list(new.y)
        assert old.hovertemplate==new.hovertemplate
    assert after.layout.shapes[0].y0==100
    assert after.layout.shapes[0].line.dash=="dash"
    assert after.layout.height>before.layout.height
    pd.testing.assert_frame_equal(df,original)

def test_overview_components_escape_and_preserve_values():
    html=_overview_kpis([{"label":"Mã hợp lệ","value":"461","note":"<script>"}])
    assert "461" in html and "Mã hợp lệ" in html
    assert "&lt;script&gt;" in html and "<script>" not in html
    status=_overview_status("Thời điểm","27/11/2026 14:29","schedule")
    assert "27/11/2026 14:29" in status
    assert "is-ok" in _overview_status("Trạng thái","Đã đọc file dữ liệu","check_circle",ok=True)

def test_overview_css_scoped_for_both_modes():
    for mode in ("Sáng","Tối"):
        css=overview_css(mode)
        assert ".st-key-ep_overview_chart" in css
        assert ".ep-overview-kpis" in css
        assert "@container" in css
        assert "__OV_" not in css
