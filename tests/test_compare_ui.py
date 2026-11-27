"""Presentation-only regression checks for results and comparison."""
import pytest
from src.app.components import html_table
from src.app.theme import compare_css
from src.app import charts
import plotly.graph_objects as go


def test_selected_row_is_optional_and_keeps_escaped_values():
    rows=[["A",100,"Đạt"],["B",200,"Chưa chạy"]]
    plain=html_table(["Phương án","Tiền ròng","Trạng thái"],rows,numeric=(1,),pills={2:{"Đạt":"ok","Chưa chạy":"neutral"}})
    highlighted=html_table(["Phương án","Tiền ròng","Trạng thái"],rows,numeric=(1,),pills={2:{"Đạt":"ok","Chưa chạy":"neutral"}},highlight_row=1)
    assert highlighted.replace(' class="ep-table-selected"','')==plain
    assert '<tr class="ep-table-selected"><td>B</td>' in highlighted
    assert '<span class="ep-pill neutral">Chưa chạy</span>' in plain
    assert "&lt;script&gt;" in html_table(["A"],[["<script>"]],highlight_row=0)


@pytest.mark.parametrize("mode",["Sáng","Tối"])
def test_comparison_style_keeps_trace_data(mode):
    t=charts.apply_palette(mode,"#2563EB")
    f=go.Figure(go.Scatter(x=[1,2],y=[.5,.33],hovertemplate="%{y:.4f}"))
    before=f.data[0].to_plotly_json()
    charts.compare_style(f,t)
    assert f.data[0].to_plotly_json()==before
    css=compare_css(mode)
    assert "__C_" not in css
    assert "ep-table-selected" in css and "ep_stock_preview_actions" in css
