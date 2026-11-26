"""Native widget interaction checks. Fixtures stay in pytest's temporary directory.
AppTest validates Streamlit state, not rendered browser pixels.
"""
from pathlib import Path
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

@pytest.fixture
def test_catalog(tmp_path):
    folder=tmp_path/"data/processed"
    folder.mkdir(parents=True)
    pd.DataFrame([
        dict(symbol="ACB",name="Ngân hàng Á Châu",board="HOSE",lotSize=100,source="ssi_fastconnect_v3"),
        dict(symbol="SHS",name="Chứng khoán Sài Gòn Hà Nội",board="HNX",lotSize=100,source="ssi_fastconnect_v3"),
    ]).to_parquet(folder/"ssi_securities.parquet",index=False)
    return tmp_path

def _app(root,mode):
    return AppTest.from_string(
        "from pathlib import Path\n"
        "import streamlit as st\n"
        "from src.app.pages import planner, page_header\n"
        "from src.app.theme import theme_css, palette\n"
        f"mode={mode!r}\n"
        f"root=Path({str(root)!r})\n"
        "st.markdown(theme_css(mode),unsafe_allow_html=True)\n"
        "page_header('planner',palette(mode)['accent'],mode)\n"
        "planner(root,{'books':None,'err':'internal/path.parquet','use_ssi':False},palette(mode))\n",
        default_timeout=15).run()

@pytest.mark.parametrize("mode",["Sáng","Tối"])
def test_planner_native_controls_without_market_data(test_catalog,mode):
    at=_app(test_catalog,mode)
    assert not at.exception
    assert at.button(key="ep_calculate_plan").disabled
    assert any("Dữ liệu thị trường chưa sẵn sàng." in w.value for w in at.warning)
    assert all("internal/path.parquet" not in w.value for w in at.warning)
    at.selectbox(key="ep_stock_board").select("HOSE").run()
    assert not at.exception
    at.selectbox(key="ep_stock_autocomplete").select("ACB").run()
    assert not at.exception
    assert dict(at.session_state["ep_draft_holdings"])=={"ACB":0}
    at.number_input(key="ep_qty_ACB").set_value(1257).run()
    assert not at.exception
    assert at.session_state["ep_draft_holdings"]["ACB"]==1257
    at.number_input(key="ep_setting_target").set_value(50.0).run()
    at.number_input(key="ep_setting_fee").set_value(.15).run()
    at.number_input(key="ep_setting_tax").set_value(.10).run()
    at.slider(key="ep_setting_lamb").set_value(.75).run()
    assert not at.exception
    settings=at.session_state["ep_draft_settings"]
    assert settings["target"]==50.0 and settings["lamb"]==.75
    assert settings["fee"]==pytest.approx(.15) and settings["tax"]==pytest.approx(.10)
    assert at.button(key="ep_calculate_plan").disabled
    at.button(key="ep_remove_ACB").click().run()
    assert not at.exception
    assert dict(at.session_state["ep_draft_holdings"])=={}
    assert at.button(key="ep_calculate_plan").disabled
