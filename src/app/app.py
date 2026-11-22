"""Entry point: python -m streamlit run src/app/app.py"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import streamlit as st
from src.app.theme import PEACH_ACCENT, theme_css, palette
from src.app.pages import render_page, NAV, PAGE_HELP

st.set_page_config(page_title='ExitPlan | Dashboard',page_icon='📊',layout='wide',initial_sidebar_state='expanded')

with st.sidebar:
    st.markdown('<div class="ep-brand"><div class="ep-brand-mark">E</div><div><div class="ep-brand-title">ExitPlan</div><div class="ep-brand-sub">SMART PORTFOLIO EXIT</div></div></div>', unsafe_allow_html=True)
    st.caption('SMART PORTFOLIO EXIT · VIỆT NAM')
    nav_options=list(NAV)
    page=st.radio('Điều hướng',nav_options,format_func=lambda s:NAV[s].split('  ',1)[-1],label_visibility='collapsed',key='ep_navigation')
    st.caption(PAGE_HELP[page])
    st.divider()
    dark_mode=st.toggle('🌙 Chế độ tối',value=False,key='ep_dark_mode')
    mode='Tối' if dark_mode else 'Sáng'
    accent=PEACH_ACCENT
    font='Be Vietnam Pro'
    size_pt=12
    st.caption('Dữ liệu từ file đã lưu. Không đọc tài khoản hoặc gửi lệnh.')

st.markdown(theme_css(mode),unsafe_allow_html=True)
config=dict(mode=mode,accent=accent,font=font,size_pt=size_pt,theme=palette(mode,accent))
render_page(page,ROOT,config)
st.divider()
st.caption('Công cụ phân tích học thuật, không phải khuyến nghị đầu tư.')
