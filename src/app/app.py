"""Entry point: python -m streamlit run src/app/app.py"""
import sys
from pathlib import Path
from textwrap import dedent
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import streamlit as st
from src.app.theme import BLUE_ACCENT, theme_css, palette
from src.app.pages import render_page, NAV
from src.app.live import sidebar_live

st.set_page_config(page_title='ExitPlan | Kế hoạch bán',page_icon=None,layout='wide',initial_sidebar_state='expanded')

with st.sidebar:
    # Logo SVG nhỏ: danh mục (3 thanh) và mũi tên thoát vị thế.
    # Khác với favicon: tab trình duyệt dùng logo Streamlit mặc định.
    st.markdown(
        dedent("""
        <div class="ep-brand">
          <span class="ep-brand-mark" role="img" aria-label="Biểu tượng ExitPlan - danh mục và kế hoạch thanh lý">
            <svg viewBox="0 0 32 32" width="29" height="29" aria-hidden="true"
                 fill="none" stroke="currentColor" stroke-width="2.4"
                 stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 25V18M11 25V12M17 25V16" />
              <path d="M7 7h18v11" />
              <path d="m19 13 6 5 5-5" />
              <path d="M4 28h24" stroke-opacity=".75" />
            </svg>
          </span>
          <div>
            <div class="ep-brand-title">ExitPlan</div>
            <div class="ep-brand-sub">SMART PORTFOLIO EXIT</div>
          </div>
        </div>
        """),
        unsafe_allow_html=True,
    )
    st.caption('SMART PORTFOLIO EXIT · VIỆT NAM')
    # Pill điều khiển giao diện: bấm trực tiếp toàn bộ nút, KHÔNG overlay.
    # Bề mặt pill và nút tròn/icon được vẽ trên chính st.button (DOM ổn định hơn
    # cấu trúc track/thumb nội bộ của st.toggle giữa các bản Streamlit).
    def _switch_theme():
        st.session_state['ep_dark_mode']=not st.session_state.get('ep_dark_mode',False)

    dark_mode=bool(st.session_state.get('ep_dark_mode',False))
    st.button(
        'Chuyển sang giao diện sáng' if dark_mode else 'Chuyển sang giao diện tối',
        key='ep_theme_switch',
        on_click=_switch_theme,
        help='Nhấn để chuyển sang giao diện sáng' if dark_mode
             else 'Nhấn để chuyển sang giao diện tối',
    )
    mode='Tối' if dark_mode else 'Sáng'
    # Main navigation follows the investor workflow; technical pages stay available.
    primary_nav=('overview','planner','compare','liquidity','ssi_history')
    advanced_nav=('data','validation','methods')
    if st.session_state.get('ep_navigation')=='downloads':
        st.session_state['ep_navigation']='compare'
    if st.session_state.get('ep_navigation') not in primary_nav+advanced_nav:
        st.session_state['ep_navigation']='overview'

    def _navigate(key):
        st.session_state['ep_navigation']=key

    nav_icons={'overview':'home','planner':'calculate','compare':'balance','liquidity':'bar_chart','ssi_history':'show_chart','data':'database','validation':'verified','methods':'menu_book','downloads':'download'}

    def _nav_button(nav_key,nav_label):
        st.button(
            nav_label.split('  ',1)[-1],
            icon=':material/'+nav_icons[nav_key]+':',
            key='ep_nav_'+nav_key,
            type='primary' if st.session_state['ep_navigation']==nav_key else 'secondary',
            use_container_width=True,
            on_click=_navigate,args=(nav_key,),
        )

    for nav_key,nav_label in NAV.items():
        if nav_key in primary_nav:
            _nav_button(nav_key,nav_label)
    with st.expander('Thông tin & hỗ trợ',expanded=st.session_state['ep_navigation'] in advanced_nav):
        for nav_key in advanced_nav:
            _nav_button(nav_key,NAV[nav_key])
    page=st.session_state['ep_navigation']
    accent=BLUE_ACCENT
    font='Be Vietnam Pro'
    size_pt=12
    st.divider()
    sidebar_live(ROOT)
    st.caption('Không đặt lệnh thật')

st.markdown(theme_css(mode),unsafe_allow_html=True)
config=dict(mode=mode,accent=accent,font=font,size_pt=size_pt,theme=palette(mode,accent))
render_page(page,ROOT,config)
st.divider()
st.caption('Công cụ phân tích học thuật, không phải khuyến nghị đầu tư.')
