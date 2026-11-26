"""Regression checks for the fixed banking-blue ExitPlan dashboard."""
from src.app.theme import BLUE_ACCENT, palette, theme_css, hero_svg
from src.app.charts import apply_palette
from src.app.components import cards_html


def test_light_palette_pale_blue_sidebar_and_sky_blue_canvas():
    colors = palette("Sáng")
    assert colors["sidebar"] == "#EAF3FC"
    assert colors["bg"] == "#F0F6FD"
    assert colors["surface"] == "#FFFFFF"
    assert colors["accent"] == BLUE_ACCENT
    css = theme_css("Sáng")
    assert "#EAF3FC" in css
    assert "#173454" in css
    assert '__SIDEBRANDTITLE__' not in css
    assert '__SIDETOGLABEL__' not in css


def test_dark_sidebar_remains_navy_and_brand_contrast():
    colors = palette("Tối")
    css = theme_css("Tối")
    assert colors["sidebar"] == "#091A31"
    assert "#F5FAFF" in css
    # Navigation SVGs are URL-encoded: the stroke color uses %23 for #.
    assert "stroke%3D%27%23ECF5FF%27" in css
    assert "color:#EDF6FF !important" in css
    assert '__NAVTEXT__' not in css
    assert '__NAVACTIVE__' not in css


def test_dark_palette_uses_blue_background_for_plots_and_tables():
    colors = palette("Tối")
    assert colors["bg"] == "#0C192C"
    assert colors["sidebar"] == "#091A31"
    assert colors["surface"] == colors["plot"] == "#192B43"
    assert colors["accent"] == "#69B2FF"
    css = theme_css("Tối")
    assert "#274361" in css  # dark table header
    assert "#173D44" in css  # dark mint scorecard
    assert "__MINT_BG__" not in css
    assert "__BLUE_BG__" not in css


def test_cards_have_four_independent_pastel_tones_and_icons():
    html = cards_html([
        {"label": "Tổng tài sản", "value": "1"},
        {"label": "Số mã", "value": "2"},
        {"label": "ADV", "value": "3"},
        {"label": "Chi phí", "value": "4"},
    ])
    for tone in ("mint", "violet", "blue", "amber"):
        assert f"ep-card--{tone}" in html
    assert html.count('<svg') == 4


def test_plotly_palette_matches_finance_scorecard_colors():
    colors = apply_palette("Sáng", BLUE_ACCENT)
    assert colors["accent"] == BLUE_ACCENT
    assert colors["secondary"] == "#4CB99A"
    assert colors["tertiary"] == "#9280DD"


def test_hero_recolored_to_blue_and_keeps_semantic_description():
    svg = hero_svg(BLUE_ACCENT, "Sáng")
    assert 'viewBox="0 0 510 252"' in svg
    assert "danh mục cổ phiếu" in svg
    assert "#D6EAFF" in svg
    assert "#FFDAD1" not in svg

def test_multiselect_tags_and_native_widgets_use_blue_not_red():
    css=theme_css("Sáng")
    assert '[data-testid="stMultiSelect"] [data-baseweb="tag"]' in css
    assert '#2E83E6' in css
    assert '#FFFFFF' in css
    assert '__CHIP_BLUE__' not in css

    dark_css=theme_css("Tối")
    assert '#348BEB' in dark_css
    assert '#192B43' in dark_css
    assert '__INPUT_BG__' not in dark_css


def test_nav_icon_and_sidebar_light_favicon_configuration():
    from pathlib import Path
    source=(Path(__file__).resolve().parents[1]/'src/app/app.py').read_text(encoding='utf-8')
    assert 'page_icon=None' in source
    assert '<svg viewBox="0 0 32 32"' in source
    assert 'from textwrap import dedent' in source
    css=theme_css("Sáng")
    assert '#EAF3FC' in css
    assert '#173454' in css


def test_dark_widget_surfaces_and_code_are_consistent():
    css=theme_css("Tối")
    assert '[data-testid="stCodeBlock"] pre' in css
    assert '[data-testid="stSelectbox"] [data-baseweb="select"]' in css
    assert '[data-testid="stMultiSelect"] [data-baseweb="select"]' in css
    assert '[data-testid="stAlert"] p' in css
    assert '#192B43' in css
    assert '#EAF3FF' in css
    assert '#348BEB' in css


def test_browser_title_describes_exitplan_not_generic_dashboard():
    from pathlib import Path
    source=(Path(__file__).resolve().parents[1]/'src/app/app.py').read_text(encoding='utf-8')
    assert "page_title='ExitPlan | Kế hoạch bán'" in source
    assert 'page_icon=None' in source


def test_dark_dropdown_portal_and_selected_value_are_legible():
    css=theme_css("Tối")
    assert 'body [data-baseweb="popover"] > div' in css
    assert 'body [data-testid="stSelectboxVirtualDropdown"]' in css
    assert 'body ul[role="listbox"]' in css
    assert '[data-testid="stSelectbox"] [data-baseweb="select"] span' in css
    assert 'background-color:#192B43 !important' in css
    assert 'color:#EAF3FF !important' in css
    assert 'background-color:#294765 !important' in css


def test_validation_two_file_options_use_buttons_instead_of_dropdown():
    from pathlib import Path
    source=(Path(__file__).resolve().parents[1]/'src/app/pages.py').read_text(encoding='utf-8')
    assert 'if len(filenames)<=3:' in source
    assert "key='ep_validation_'+filename" in source
    assert "'validation_replay.csv':'Phát lại dữ liệu'" in source
    assert "'validation_sensitivity.csv':'Độ nhạy tham số'" in source
    assert "st.session_state[choice_key]=filename" in source


def test_sidebar_no_collapse_chevron_on_desktop_but_has_recovery():
    for mode in ("Sáng","Tối"):
        css=theme_css(mode)
        assert "@media (min-width: 769px)" in css
        assert '[data-testid="stSidebarCollapseButton"]' in css
        assert 'display:none !important' in css
        # A previously-collapsed sidebar can still be reopened; mobile retains
        # the built-in navigation controls.
        assert '[data-testid="stSidebarCollapsedControl"]' in css
        assert '[data-testid="stAppDeployButton"]' in css


def test_compact_switch_is_under_brand_and_clickable():
    from pathlib import Path
    source=(Path(__file__).resolve().parents[1]/'src/app/app.py').read_text(encoding='utf-8')
    subtitle=source.index("st.caption('SMART PORTFOLIO EXIT · VIỆT NAM')")
    switch=source.index("key='ep_theme_switch'")
    navigation=source.index("for nav_key,nav_label in NAV.items():")
    assert subtitle < switch < navigation
    assert "on_click=_switch_theme" in source
    assert "st.session_state['ep_dark_mode']=not st.session_state.get('ep_dark_mode',False)" in source
    assert "mode='Tối' if dark_mode else 'Sáng'" in source
    assert "ep_theme_row" not in source
    assert "ep_theme_bar" not in source
    assert "st.toggle(" not in source


def test_compact_pill_svg_is_on_clickable_button_not_native_track():
    light=theme_css('Sáng')
    dark=theme_css('Tối')
    for css in (light,dark):
        assert '.st-key-ep_theme_switch button::after' in css
        assert '.st-key-ep_theme_switch button {' in css
        assert 'width:106px !important' in css
        assert 'height:52px !important' in css
        assert 'width:38px !important' in css
        assert 'background-image:url("data:image/svg+xml,' in css
        assert 'background-size:21px 21px' in css
        assert 'pointer-events:none !important' in css
        assert '__EP_ICON_URI__' not in css
        assert '__EP_THUMB_LEFT__' not in css
        assert '.st-key-ep_dark_mode' not in css
        assert 'ep_theme_bar' not in css
        assert 'ep_theme_row' not in css
    assert 'left:5px !important' in light
    assert 'left:60px !important' in dark
    assert '%3Ccircle' in light
    assert '%3Ccircle' not in dark


def test_inactive_navigation_hover_has_no_filled_background():
    for mode in ("Sáng","Tối"):
        css=theme_css(mode)
        assert 'button[kind="secondary"]:hover,' in css
        assert 'button[kind="secondary"]:focus {' in css
        assert 'background:transparent !important;box-shadow:none !important;' in css
        assert 'button[kind="primary"] {' in css
        assert 'button:focus-visible {' in css
        assert 'background:rgba(72,151,235,.19) !important;' not in css

def test_investor_navigation_keeps_technical_pages_and_embedded_export():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    app=(root/'src/app/app.py').read_text(encoding='utf-8')
    pages=(root/'src/app/pages.py').read_text(encoding='utf-8')
    assert "primary_nav=('overview','planner','compare','liquidity','ssi_history')" in app
    assert "advanced_nav=('data','validation','methods')" in app
    assert "st.expander('Thông tin & hỗ trợ'" in app
    assert "on_click=_navigate,args=(nav_key,)" in app
    assert "st.expander('Xuất kết quả CSV'" in pages
    assert "downloads(root,data,t,show_source=False,include_liquidity=False)" in pages


def test_native_search_surface_and_text_contrast():
    for mode in ("Sáng","Tối"):
        css=theme_css(mode)
        p=palette(mode)
        assert 'caret-color:'+p['text']+' !important' in css
        assert '-webkit-text-fill-color:'+p['text']+' !important' in css
        assert 'input::placeholder' in css
        assert '.stApp [data-testid="stSelectbox"][data-testid="stSelectbox"] div' in css
        assert '.ep-table-wrap.ep-paged .ep-table th' in css
    assert 'background-color:#192B43 !important;color:#EAF3FF !important' in theme_css("Tối")

def test_investor_tables_do_not_use_light_canvas_or_technical_catalog():
    from pathlib import Path
    source=(Path(__file__).resolve().parents[1]/'src/app/pages.py').read_text(encoding='utf-8')
    assert 'st.dataframe(' not in source
    history=source[source.index('def ssi_history('):source.index('def data_page(')]
    assert 'st.code(' not in history
    assert 'cwUnderlyingSymbol' not in history
    assert "paged_table(shown.rename(columns=columns)" in history
    assert "history_stats_table(view,'ep_liq_hist_page')" in source
