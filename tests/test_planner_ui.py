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
        dict(symbol="HPG",name="Hòa Phát",board="HOSE",lotSize=100,source="ssi_fastconnect_v3"),
        dict(symbol="FPT",name="FPT",board="HOSE",lotSize=100,source="ssi_fastconnect_v3"),
    ]).to_parquet(folder/"ssi_securities.parquet",index=False)
    return tmp_path

def _app(root,mode,with_books=False):
    return AppTest.from_string(
        "from pathlib import Path\n"
        "import streamlit as st\n"
        "import pandas as pd\n"
        "from src.app.pages import planner, page_header\n"
        "from src.app.theme import theme_css, palette\n"
        f"mode={mode!r}\n"
        f"root=Path({str(root)!r})\n"
        "st.markdown(theme_css(mode),unsafe_allow_html=True)\n"
        "page_header('planner',palette(mode)['accent'],mode)\n"
        f"with_books={with_books!r}\n"
        "books=None\n"
        "if with_books:\n"
        "    books=pd.DataFrame([dict(symbol=s,ts_vn=pd.Timestamp(t,tz='Asia/Ho_Chi_Minh'),closePrice=20000,bidPrice1=19950,bidVol1=10000,bidPrice2=19900,bidVol2=10000,bidPrice3=19850,bidVol3=10000,lotSize=100,data_kind='live') for s,t in [('ACB','2026-11-27 10:00:00'),('HPG','2026-11-27 10:00:00'),('FPT','2026-11-27 10:00:30')]])\n"
        "planner(root,{'books':books,'err':'internal/path.parquet','use_ssi':False},palette(mode))\n",
        default_timeout=15).run()

@pytest.mark.parametrize("mode",["Sáng","Tối"])
def test_planner_native_controls_without_market_data(test_catalog,mode):
    at=_app(test_catalog,mode)
    assert not at.exception
    assert at.button(key="ep_calculate_plan").disabled
    assert any("Dữ liệu thị trường chưa sẵn sàng." in w.value and "ep-planner-notice warning" in w.value for w in at.markdown)
    assert all("internal/path.parquet" not in w.value for w in at.markdown)
    at.selectbox(key="ep_stock_board").select("HOSE").run()
    assert not at.exception
    assert at.selectbox(key="ep_stock_autocomplete").disabled
    assert not at.selectbox(key="ep_stock_autocomplete").options
    assert at.button(key="ep_add_stock").disabled
    # An existing holding may remain when the saved data becomes unavailable.
    at.session_state["ep_draft_holdings"]={"ACB":100}
    at.run()
    assert not at.exception
    assert at.selectbox(key="ep_stock_autocomplete").disabled
    at.number_input(key="ep_qty_ACB").set_value(1257).run()
    assert not at.exception
    assert at.session_state["ep_draft_holdings"]["ACB"]==1257
    assert any("Thiếu sổ lệnh: ACB." in w.value for w in at.markdown)
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


@pytest.mark.parametrize("mode",["Sáng","Tối"])
def test_planner_native_controls_with_compatible_books(test_catalog,mode):
    at=_app(test_catalog,mode,with_books=True)
    assert not at.exception
    at.selectbox(key="ep_stock_board").select("HOSE").run()
    assert not at.exception
    assert not at.selectbox(key="ep_stock_autocomplete").disabled
    at.selectbox(key="ep_stock_autocomplete").select("ACB").run()
    assert not at.exception
    assert dict(at.session_state["ep_draft_holdings"])=={}
    assert any("ep-stock-preview" in w.value and "Ngân hàng Á Châu" in w.value and "19.950" in w.value for w in at.markdown)
    assert not at.button(key="ep_add_stock").disabled
    at.number_input(key="ep_stock_preview_qty").set_value(250).run()
    assert dict(at.session_state["ep_draft_holdings"])=={}
    at.button(key="ep_add_stock").click().run()
    assert not at.exception
    assert dict(at.session_state["ep_draft_holdings"])=={"ACB":250}
    assert at.number_input(key="ep_qty_ACB").value==250
    assert len(at.selectbox(key="ep_stock_autocomplete").options)==1
    assert at.selectbox(key="ep_stock_autocomplete").options[0].startswith("HPG")
    assert not at.button(key="ep_calculate_plan").disabled
    at.number_input(key="ep_qty_ACB").set_value(50).run()
    assert not at.exception
    assert at.button(key="ep_calculate_plan").disabled
    assert any("Không có lô 100 CP nào có thể bán" in w.value for w in at.markdown)
    at.number_input(key="ep_qty_ACB").set_value(1257).run()
    assert not at.exception
    assert at.session_state["ep_draft_holdings"]["ACB"]==1257
    assert not at.button(key="ep_calculate_plan").disabled
    at.selectbox(key="ep_stock_autocomplete").select("HPG").run()
    assert not at.exception
    assert dict(at.session_state["ep_draft_holdings"])=={"ACB":1257}
    assert at.number_input(key="ep_stock_preview_qty").value==100
    at.button(key="ep_add_stock").click().run()
    assert not at.exception
    assert dict(at.session_state["ep_draft_holdings"])=={"ACB":1257,"HPG":100}
    assert at.selectbox(key="ep_stock_autocomplete").disabled
    at.button(key="ep_remove_HPG").click().run()
    assert not at.exception
    assert dict(at.session_state["ep_draft_holdings"])=={"ACB":1257}
    assert not at.selectbox(key="ep_stock_autocomplete").disabled
