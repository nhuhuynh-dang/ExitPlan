"""Entry point: python -m streamlit run src/app/app.py"""
import sys
from pathlib import Path
from textwrap import dedent
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import streamlit as st
from src.app.theme import BLUE_ACCENT, theme_css, palette
from src.app.pages import render_page, NAV, PAGE_HELP

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
    # Công tắc gạt thật: nút tròn trượt trái/phải, chứa icon đơn sắc.
    # Giữ dưới dòng Việt Nam và giữ trạng thái khi đổi trang.
    if 'ep_dark_mode' not in st.session_state:
        st.session_state['ep_dark_mode']=False
    current_dark=bool(st.session_state['ep_dark_mode'])
    dark_mode=st.toggle(
        'Chế độ tối' if current_dark else 'Chế độ sáng',
        key='ep_dark_mode',
    )
    mode='Tối' if dark_mode else 'Sáng'
    # Dùng nút điều hướng thay radio: không còn chấm tròn, mỗi mục có icon SVG riêng.
    if st.session_state.get('ep_navigation') not in NAV:
        st.session_state['ep_navigation']='overview'
    for nav_key,nav_label in NAV.items():
        title=nav_label.split('  ',1)[-1]
        active=st.session_state['ep_navigation']==nav_key
        if st.button(
            title,
            key='ep_nav_'+nav_key,
            type='primary' if active else 'secondary',
            use_container_width=True,
        ):
            st.session_state['ep_navigation']=nav_key
            st.rerun()
    page=st.session_state['ep_navigation']
    st.caption(PAGE_HELP[page])
    st.divider()
    accent=BLUE_ACCENT
    font='Be Vietnam Pro'
    size_pt=12
    st.caption('Dữ liệu từ file đã lưu. Không đọc tài khoản hoặc gửi lệnh.')

st.markdown(theme_css(mode),unsafe_allow_html=True)
config=dict(mode=mode,accent=accent,font=font,size_pt=size_pt,theme=palette(mode,accent))
render_page(page,ROOT,config)
st.divider()
st.caption('Công cụ phân tích học thuật, không phải khuyến nghị đầu tư.')
