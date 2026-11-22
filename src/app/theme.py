"""Giao diện glass pastel lấy cảm hứng tổ chức code dashboard mẫu; không dùng hình ảnh ngoài."""
from html import escape

PEACH_ACCENT='#E6A69B'
FONT_FAMILY="'Be Vietnam Pro',sans-serif"

def hex_rgb(h): return tuple(int(h[i:i+2],16) for i in (1,3,5))
def mix(a,b,f):return '#'+''.join(f'{round(x*(1-f)+y*f):02x}' for x,y in zip(hex_rgb(a),hex_rgb(b)))
def rgba(hexcolor,alpha):return f'rgba({",".join(map(str,hex_rgb(hexcolor)))},{alpha})'

def palette(mode, accent=PEACH_ACCENT):
    """Một bộ màu hồng đào pastel cố định, nền tối thực sự cho mọi biểu đồ."""
    dark = mode == 'Tối'
    return {
        'bg': '#261B23' if dark else '#FFF8F5',
        'surface': '#392832' if dark else '#FFFEFD',
        'sidebar': '#2C1E29' if dark else '#FFF2EE',
        'text': '#FFF0EB' if dark else '#443B42',
        'muted': '#D7B8BC' if dark else '#806D75',
        'border': '#6B4A59' if dark else '#ECDDD7',
        'accent': PEACH_ACCENT,
        'positive': '#9ACBB2' if dark else '#238B71',
        'negative': '#F8A4A3' if dark else '#BF5B62',
        'plot': '#392832' if dark else '#FFFEFD',
    }

def theme_css(mode,accent=PEACH_ACCENT,font=None,size_pt=12):
    accent=PEACH_ACCENT
    p=palette(mode); f=FONT_FAMILY; size=12
    css="""
<style>
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
html, body, .stApp {font-family:__FONT__}
.stApp [data-testid="stMarkdownContainer"], .stApp input, .stApp textarea {font-family:__FONT__}
html{font-size:16px} .stApp{font-size:__SIZE__pt}
/* Quan trọng: không ghi đè font icon nội bộ của Streamlit bằng font giao diện */
[data-testid="stIconMaterial"], .material-symbols-rounded, .material-symbols-outlined {font-family:'Material Symbols Rounded' !important;font-weight:normal !important;font-style:normal !important;letter-spacing:normal !important;white-space:nowrap;font-feature-settings:'liga' !important}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at 83% 1%,__GLOW__ 0%,transparent 35%),radial-gradient(ellipse at 8% 65%,__GLOW2__ 0%,transparent 32%),__BG__;color:__TEXT__}
[data-testid="stSidebar"]{background:__SIDEBAR__;border-right:1px solid __BORDER__}
[data-testid="stSidebar"]{min-width:270px;max-width:310px}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding-top:1.45rem;padding-left:.65rem;padding-right:.65rem}
[data-testid="stSidebar"] [role="radiogroup"]{gap:6px}
[data-testid="stSidebar"] [role="radiogroup"] label{border:1px solid transparent;border-radius:12px;padding:9px 10px;min-height:46px;cursor:pointer;transition:background .15s,border-color .15s;align-items:center}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:__GLOW__}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:__GLOW__;border-color:__BORDER__}
[data-testid="stSidebar"] [role="radiogroup"] label p{font-size:.90rem;line-height:1.4;font-weight:550;margin:0;overflow-wrap:normal;word-break:normal}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{font-weight:750}
.ep-brand{display:flex;align-items:center;gap:11px;padding:6px 0 12px}
 .ep-brand-mark{display:grid;place-items:center;height:43px;width:43px;border-radius:14px;background:__ACCENT__;color:#462934;font-size:24px;font-weight:850;flex-shrink:0}
.ep-brand-title{font-size:1.43rem;font-weight:850;color:__TEXT__;line-height:1.2}
.ep-brand-sub{font-size:.67rem;letter-spacing:.07em;color:__MUTED__;margin-top:4px}
[data-testid="stSidebar"] [data-testid="stExpander"]{border:1px solid __BORDER__;border-radius:12px;background:__GLASS__}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{font-size:.85rem}
[data-testid="stSidebar"] [data-testid="stSelectbox"] , [data-testid="stSidebar"] [data-testid="stSlider"]{max-width:100%}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"], [data-testid="stSidebar"] label, [data-testid="stSidebar"] p{color:__TEXT__}
.block-container{max-width:1560px;padding:2.2rem 2rem 3rem !important;margin-left:auto;margin-right:auto}
[data-testid="stMain"] h1,[data-testid="stMain"] h2,[data-testid="stMain"] h3{color:__TEXT__}
[data-testid="stMain"] h3{border-left:4px solid __ACCENT__;padding-left:.72rem;margin-top:1.1rem;font-weight:750}
[data-testid="stMetric"],div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"]{border-radius:17px}
[data-testid="stMetric"]{border:1px solid __BORDER__;border-left:4px solid __ACCENT__;background:__SURFACE__;padding:15px 18px;box-shadow:0 8px 28px rgba(0,0,0,.035)}
[data-testid="stMetricLabel"]{color:__MUTED__} [data-testid="stMetricValue"]{color:__TEXT__;font-variant-numeric:tabular-nums}
[data-testid="stVerticalBlockBorderWrapper"]{background:__GLASS__;border-radius:18px}
div[data-testid="stTabs"] button {border-radius:20px;padding:.4rem 1.1rem;color:__TEXT__}
div[data-testid="stTabs"] button[aria-selected="true"]{background:__GLOW__;border-bottom:2px solid __ACCENT__}
[data-testid="stSegmentedControl"]{border-radius:28px}
.stButton > button, .stDownloadButton > button {border-radius:12px;border:1px solid __BORDER__;font-weight:600}
.stButton > button[kind="primary"]{background:__ACCENT__;color:__BUTTONTEXT__;border:0}
[data-testid="stDataFrame"], [data-testid="stDataEditor"]{border-radius:13px;overflow:hidden;background:__SURFACE__;border:1px solid __BORDER__}
[data-testid="stDataFrame"] canvas, [data-testid="stDataEditor"] canvas{background:__SURFACE__}
[data-testid="stDataFrame"] [role="grid"], [data-testid="stDataEditor"] [role="grid"]{background:__SURFACE__;color:__TEXT__}
[data-testid="stDataFrame"] [role="columnheader"], [data-testid="stDataEditor"] [role="columnheader"]{background:__SIDEBAR__;color:__TEXT__}
[data-testid="stDataFrame"] * , [data-testid="stDataEditor"] * {font-variant-numeric:tabular-nums}
[data-testid="stMarkdownContainer"] .ep-card{background:__SURFACE__;border:1px solid __BORDER__;border-radius:18px;padding:17px 18px;min-height:116px;box-shadow:0 9px 24px rgba(0,0,0,.025)}
.ep-eyebrow{font-size:.69rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:__ACCENT__;margin:0 0 9px}
.ep-hero{position:relative;overflow:hidden;background:__SURFACE__;border:1px solid __BORDER__;border-radius:24px;padding:27px 32px;margin-bottom:21px;min-height:165px}
.ep-hero-heading{display:flex;gap:15px;align-items:center;margin-bottom:11px;position:relative;z-index:1}
.ep-hero-icon{width:51px;height:51px;min-width:51px;border-radius:15px;display:grid;place-items:center;background:__GLOW__;border:1px solid __BORDER__;color:__ACCENT__}
.ep-hero-icon svg{width:26px;height:26px}
.ep-hero-heading .ep-eyebrow{margin-bottom:6px}
.ep-hero h1{font-size:clamp(1.5rem,2.8vw,2.3rem);line-height:1.3;margin:0 0 9px;font-weight:800;color:__TEXT__}
.ep-hero p{font-size:.92rem;max-width:67%;color:__MUTED__;margin:0;line-height:1.65}
.ep-hero .art{position:absolute;right:.45rem;top:0;width:39%;height:100%;opacity:1;pointer-events:none;display:flex;align-items:center;justify-content:flex-end}
.ep-hero .art svg{display:block;width:100%;height:100%;max-height:255px;object-fit:contain}
.ep-hero{min-height:204px}
.ep-hero>p{position:relative;z-index:1;max-width:60%}
.ep-badge{display:inline-block;border:1px solid __BORDER__;background:__GLOW__;border-radius:999px;padding:5px 10px;font-size:.74rem;font-weight:650;color:__TEXT__;margin-right:6px}
.ep-badge.warn{background:__WARNBG__;border-color:__WARNBORDER__}
.ep-kpi-label{color:__MUTED__;font-size:.80rem;margin-bottom:11px}
.ep-kpi-value{color:__TEXT__;font-size:1.65rem;font-weight:800;letter-spacing:-.025em;font-variant-numeric:tabular-nums}
.ep-kpi-note{color:__MUTED__;font-size:.72rem;margin-top:7px}
.ep-verdict{background:__GLASS__;border:1px solid __BORDER__;border-left:4px solid __ACCENT__;border-radius:15px;padding:17px 20px;margin:15px 0;color:__TEXT__}
.ep-guide{background:__GLASS__;border:1px dashed __BORDER__;border-radius:14px;padding:12px 17px;margin:12px 0;color:__MUTED__;font-size:.88rem}
.ep-table-wrap{width:100%;overflow:auto;border:1px solid __BORDER__;border-radius:14px;margin:12px 0}
.ep-table{border-collapse:collapse;width:100%;font-size:.90rem;color:__TEXT__;background:__SURFACE__}
.ep-table th{font-size:.81rem;background:__SIDEBAR__;color:__TEXT__;text-align:left;white-space:nowrap}
.ep-table td,.ep-table th{padding:12px 13px;border-bottom:1px solid __BORDER__}
.ep-table tr:last-child td{border-bottom:none}
.ep-table tbody tr:hover{background:__GLOW__}
.ep-table td.numeric,.ep-table th.numeric{text-align:right;font-variant-numeric:tabular-nums}
.ep-method{border:1px solid __BORDER__;background:__SURFACE__;border-radius:17px;padding:20px;min-height:175px}
/* Các nút điều khiển Streamlit phải dùng font icon gốc, không hiện tên icon thành chữ */
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"] {font-family:'Material Symbols Rounded' !important}
@media(max-width:960px){[data-testid="stSidebar"]{min-width:240px;max-width:270px}.block-container{padding:1.4rem 1.1rem 2rem !important}}
@media(max-width:720px){.block-container{padding:1rem !important}.ep-hero{padding:19px}.ep-hero p{max-width:100%}.ep-hero .art{opacity:.16;width:70%}}
</style>"""
    rep={'__FONT__':f,'__SIZE__':str(size),'__GLOW__':rgba(accent,.13 if mode=='Tối' else .14),
         '__GLOW2__':rgba('#E9A19A',.09 if mode=='Tối' else .08),'__BG__':p['bg'],'__SIDEBAR__':p['sidebar'],
         '__BORDER__':p['border'],'__TEXT__':p['text'],'__ACCENT__':accent,'__SURFACE__':p['surface'],
         '__MUTED__':p['muted'],'__GLASS__':rgba(p['surface'],.78),
         '__BUTTONTEXT__':'#33252D','__WARNBG__':rgba('#E9A950',.17),'__WARNBORDER__':rgba('#E9A950',.45)}
    # Vùng sidebar dùng icon nét mảnh, tương tự mẫu tham khảo (không dùng emoji).
    # Data URI được dựng từ SVG cố định; không phụ thuộc font icon tải từ mạng.
    from urllib.parse import quote
    svg_paths = [
        '<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/>',
        '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
        '<path d="M12 3v18M5 7l-3 5h6L5 7Zm14 0-3 5h6l-3-5ZM3 21h18M5 7h14"/>',
        '<path d="M3 3v18h18M7 16v-4M12 16V7M17 16V9"/>',
        '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5M3 12c0 1.7 4 3 9 3s9-1.3 9-3"/>',
        '<path d="M3 17l6-6 4 3 8-9M16 5h5v5"/>',
        '<path d="m12 22 8-4V7l-8-4-8 4v11l8 4ZM9 12l2 2 4-4"/>',
        '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
        '<path d="M12 3v12m-5-5 5 5 5-5M5 17v4h14v-4"/>',
    ]
    nav_keys=[
        'overview','planner','compare','liquidity','data',
        'ssi_history','validation','methods','downloads'
    ]
    nav_icons=[]
    icon_color='#F9E8E4' if mode=='Tối' else '#5C4E58'
    for key,paths in zip(nav_keys,svg_paths):
        svg=("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' "
             "fill='none' stroke='"+icon_color+"' stroke-width='1.8' "
             "stroke-linecap='round' stroke-linejoin='round'>"+paths+"</svg>")
        uri="data:image/svg+xml,"+quote(svg,safe='')
        nav_icons.append(
            f'[data-testid="stSidebar"] .st-key-ep_nav_{key} button::before'
            +'{content:"";display:inline-block;flex:0 0 21px;width:21px;height:21px;'
              'background-image:url("'+uri+'");background-size:contain;'
              'background-repeat:no-repeat;background-position:center;}'
        )
    extra_css = """
/* Ẩn hành động Deploy và menu không cần thiết; giữ nút mở/đóng sidebar. */
.stAppDeployButton, [data-testid="stAppDeployButton"],
[data-testid="stToolbar"], [data-testid="stToolbarActions"],
header[data-testid="stHeader"] [data-testid="stToolbar"],
#MainMenu, footer {display:none !important;}
header[data-testid="stHeader"] {background:transparent !important;box-shadow:none !important;}
/* Sidebar hồng mận trầm khi tối, hồng kem khi sáng. */
[data-testid="stSidebar"] {background:__NAVY__ !important;border-right:1px solid __BORDER__ !important;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .ep-brand-title,
[data-testid="stSidebar"] [role="radiogroup"] label p {color:__SIDETEXT__ !important;}
[data-testid="stSidebar"] .ep-brand-sub,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color:__SIDEMUTED__ !important;}
[data-testid="stSidebar"] [role="radiogroup"] {gap:5px;}
[data-testid="stSidebar"] [role="radiogroup"] label {
    display:flex !important;align-items:center !important;gap:11px !important;
    padding:11px 13px !important;min-height:47px !important;
    border-radius:13px !important;border:1px solid transparent !important;
    background:transparent !important;transition:background .16s,border-color .16s;
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child:not([data-testid="stMarkdownContainer"]) {display:none !important;}
[data-testid="stSidebar"] [role="radiogroup"] input[type="radio"] {position:absolute !important;opacity:0 !important;width:1px !important;height:1px !important;}
[data-testid="stSidebar"] [role="radiogroup"] label [data-baseweb="radio"] {display:none !important;}
[data-testid="stSidebar"] [role="radiogroup"] label > div:has(> input[type="radio"]) {display:none !important;}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {background:rgba(230,166,155,.12) !important;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background:rgba(230,166,155,.22) !important;
    border-color:#E6A69B !important;
    box-shadow:inset 3px 0 0 #E6A69B;
}
[data-testid="stSidebar"] [role="radiogroup"] label p {font-weight:600 !important;font-size:.91rem;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {color:__SIDEACTIVE__ !important;font-weight:750 !important;}
[data-testid="stSidebar"] [data-testid="stToggle"] {padding:10px 11px;border:1px solid __BORDER__;border-radius:13px;background:__TOGGLEBG__;}
[data-testid="stSidebar"] .ep-brand-mark {background:#E6A69B;color:#462934;}
/* Dark Mode giữ toàn bộ bề mặt ở dải màu hồng đào / mận trầm. */
[data-testid="stAlert"] {border-radius:14px;border-color:__BORDER__ !important;background:__ALERTBG__ !important;}
[data-testid="stAlert"][data-baseweb] {color:__TEXT__ !important;}
[data-testid="stToggle"] [role="switch"][aria-checked="true"] {background:#D79A9D !important;}
[data-testid="stSidebar"] [data-testid="stToggle"] [role="switch"][aria-checked="true"] {background:#D79A9D !important;}

/* Nút, ô nhập và các thẻ áp dụng đúng theme cho cả Sáng và Tối. */
.stButton button, .stDownloadButton button,
[data-testid="stSelectbox"] > div, [data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input, [data-testid="stMultiSelect"] > div,
[data-testid="stExpander"], [data-testid="stVerticalBlockBorderWrapper"] {
    background-color:__SURFACE__ !important;color:__TEXT__ !important;
    border-color:__BORDER__ !important;
}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {color:__TEXT__ !important;}
[data-testid="stMetric"], .ep-panel, .ep-card {box-shadow:0 10px 28px rgba(0,0,0,.06);}
[data-testid="stMarkdownContainer"] .ep-card {min-height:116px;}
/* Bảng dữ liệu đọc-only: nền tối cả hàng, đầu bảng và hover. */
.ep-table-wrap {background:__SURFACE__ !important;border:1px solid __BORDER__ !important;border-radius:16px !important;overflow:auto !important;}
.ep-table {background:__SURFACE__ !important;border-collapse:separate !important;border-spacing:0 !important;width:100%;}
.ep-table th {background:__TABLE_HEAD__ !important;color:__TEXT__ !important;font-size:.79rem;font-weight:750 !important;}
.ep-table td {background:__SURFACE__ !important;color:__TEXT__ !important;line-height:1.5;}
.ep-table tbody tr:nth-child(even) td {background:__TABLE_ALT__ !important;}
.ep-table tbody tr:hover td {background:__TABLE_HOVER__ !important;}
.ep-table td:first-child {font-weight:650;}
.ep-pill {display:inline-block;padding:5px 10px;border-radius:100px;font-size:.75rem;font-weight:750;white-space:nowrap;}
.ep-pill.ok {background:__GOOD_BG__;color:__GOOD_TEXT__;}
.ep-pill.warn {background:__WARN_BG__;color:__WARN_TEXT__;}
.ep-pill.neutral {background:__CHIP_BG__;color:__CHIP_TEXT__;}
.ep-panel {padding:18px 20px;background:__SURFACE__;border:1px solid __BORDER__;border-radius:19px;margin:12px 0 16px;}
.ep-panel-title {font-size:1.04rem;font-weight:750;color:__TEXT__;margin:0 0 5px;}
.ep-panel-desc {font-size:.8rem;color:__MUTED__;margin-bottom:15px;}
.ep-info-row {padding:12px 0;display:flex;align-items:center;justify-content:space-between;gap:13px;border-bottom:1px solid __BORDER__;font-size:.84rem;}
.ep-info-row:last-child {border-bottom:0;}
.ep-info-key {color:__MUTED__;}
.ep-info-val {color:__TEXT__;font-weight:650;text-align:right;overflow-wrap:anywhere;}
/* Ngăn các bảng kỹ thuật và JSON trắng chói trong dark mode. */
[data-testid="stJson"], [data-testid="stJson"] pre,
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    background:__SURFACE__ !important;color:__TEXT__ !important;
    border-color:__BORDER__ !important;border-radius:14px !important;
}
[data-testid="stJson"] * {color:__TEXT__ !important;}
[data-testid="stDataFrame"] [role="grid"],[data-testid="stDataEditor"] [role="grid"] {background:__SURFACE__ !important;}
[data-testid="stDataFrame"] canvas,[data-testid="stDataEditor"] canvas {background:__SURFACE__ !important;}
/* Diện tích biểu đồ Plotly dùng nền do chart.layout cấp, thẻ ngoài theo theme. */
[data-testid="stPlotlyChart"] {border:1px solid __BORDER__;border-radius:17px;overflow:hidden;background:__SURFACE__ !important;padding:8px;}
/* Thẻ thiết lập hệ thống dễ đọc, đồng bộ bảng màu ExitPlan. */
.ep-setting-row{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:14px 0;border-bottom:1px solid __BORDER__;}
.ep-setting-row:last-child{border-bottom:none;}
.ep-setting-name{color:__TEXT__;font-weight:700;font-size:.89rem;}
.ep-setting-description{color:__MUTED__;font-size:.77rem;margin-top:5px;}
.ep-setting-row .ep-pill{flex-shrink:0;}
@media (max-width:950px) {.ep-panel{padding:15px}.ep-table{font-size:.82rem;}}
@media (max-width:580px) {.ep-setting-row{align-items:flex-start;flex-direction:column;gap:8px;}}
""".replace("__NAVY__", p['sidebar'])
    extra_css=extra_css.replace('__SIDETEXT__','#F5EFF1' if mode=='Tối' else '#443B42')
    extra_css=extra_css.replace('__SIDEMUTED__','#AEBCCB' if mode=='Tối' else '#806D75')
    extra_css=extra_css.replace('__SIDEACTIVE__','#FFE5DD' if mode=='Tối' else '#9B514B')
    extra_css=extra_css.replace('__TOGGLEBG__','#4D313D' if mode=='Tối' else '#FFEAE3')
    extra_css=extra_css.replace('__ALERTBG__','#49313B' if mode=='Tối' else '#FFF1EB')
    theme_values = {
        '__TABLE_HEAD__': '#533640' if mode=='Tối' else '#F8E9E3',
        '__TABLE_ALT__': '#412C36' if mode=='Tối' else '#FFFAF8',
        '__TABLE_HOVER__': '#60404D' if mode=='Tối' else '#FCEFEA',
        '__GOOD_BG__': '#29463B' if mode=='Tối' else '#DDF5ED',
        '__GOOD_TEXT__': '#B3E3C7' if mode=='Tối' else '#166C58',
        '__WARN_BG__': '#65413A' if mode=='Tối' else '#FFF1E3',
        '__WARN_TEXT__': '#FFD4BD' if mode=='Tối' else '#A75A33',
        '__CHIP_BG__': '#5B3546' if mode=='Tối' else '#F5E3F0',
        '__CHIP_TEXT__': '#F7C9D3' if mode=='Tối' else '#815475',
    }
    # Sidebar button navigation; stable st-key selectors instead of fragile radio DOM selectors.
    nav_button_css = """
[data-testid="stSidebar"] div[class*="st-key-ep_nav_"] {margin-bottom:5px;}
[data-testid="stSidebar"] div[class*="st-key-ep_nav_"] button {
    display:grid !important;grid-template-columns:21px minmax(0,1fr) !important;
    align-items:center !important;justify-content:stretch !important;justify-items:start !important;
    gap:12px !important;width:100% !important;min-height:47px !important;
    text-align:left !important;border-radius:13px !important;
    border:1px solid transparent !important;padding:11px 13px !important;
    background:transparent !important;color:__NAVTEXT__ !important;
    box-shadow:none !important;transition:background .15s,border-color .15s !important;
}
[data-testid="stSidebar"] div[class*="st-key-ep_nav_"] button::before {
    grid-column:1 !important;grid-row:1;align-self:center;margin:0 !important;
}
[data-testid="stSidebar"] div[class*="st-key-ep_nav_"] button > div,
[data-testid="stSidebar"] div[class*="st-key-ep_nav_"] button [data-testid="stMarkdownContainer"] {
    grid-column:2 !important;grid-row:1;min-width:0;width:100% !important;
    justify-self:stretch !important;justify-content:flex-start !important;text-align:left !important;
}
[data-testid="stSidebar"] div[class*="st-key-ep_nav_"] button p {
    color:inherit !important;font-size:.90rem !important;font-weight:650 !important;
    text-align:left !important;white-space:normal !important;line-height:1.42 !important;
    width:100% !important;margin:0 !important;
}
[data-testid="stSidebar"] div[class*="st-key-ep_nav_"] button:hover {
    background:rgba(230,166,155,.15) !important;
}
[data-testid="stSidebar"] div[class*="st-key-ep_nav_"] button[kind="primary"] {
    background:rgba(230,166,155,.22) !important;border:1px solid #E6A69B !important;
    color:__NAVACTIVE__ !important;box-shadow:inset 3px 0 0 #E6A69B !important;
}
[data-testid="stSidebar"] div[class*="st-key-ep_nav_"] button[kind="primary"] p {
    font-weight:800 !important;
}
.ep-method-grid {
    display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
    gap:22px;padding:4px 0 8px;margin:8px 0 26px;
}
.ep-method-grid .ep-method {min-height:190px;margin:0;padding:22px 23px;display:block;}
.ep-method-grid .ep-method h3 {margin:0 0 13px;font-size:1.14rem;line-height:1.4;}
.ep-method-grid .ep-method p {margin:0;line-height:1.8;font-size:.91rem;}
@media(max-width:850px) {.ep-method-grid {grid-template-columns:1fr;gap:16px;}}
""".replace("__NAVTEXT__", '#F5EFF1' if mode=='Tối' else '#443B42')
    nav_button_css=nav_button_css.replace("__NAVACTIVE__", '#FFE5DD' if mode=='Tối' else '#9B514B')
    extra_css+=nav_button_css
    for key,value in theme_values.items():
        extra_css=extra_css.replace(key,value)
    css=css.replace('</style>', extra_css+'\n'.join(nav_icons)+'</style>')
    for a,b in rep.items():css=css.replace(a,b)
    return css

def hero_svg(accent=PEACH_ACCENT, mode='Sáng'):
    """Minh họa vector ExitPlan: màn hình danh mục, kế hoạch bán, tiền và thanh khoản."""
    dark=mode=='Tối'
    screen='#50303E' if dark else '#FFFCFA'
    inner='#382631' if dark else '#FFF8F5'
    frame='#DBA7A3' if dark else '#A77E84'
    ink='#FFE5DC' if dark else '#7B6570'
    line='#EAAEA2'
    pale='#E6B3AE' if dark else '#F9D5CE'
    mint='#8DC5B6'
    light='#FAE9E4' if dark else '#FFFFFF'
    template="""<svg viewBox="0 0 510 252" xmlns="http://www.w3.org/2000/svg"
       role="img" aria-label="Minh họa ExitPlan: danh mục cổ phiếu, biểu đồ thanh khoản và kế hoạch bán">
      <defs>
        <linearGradient id="epLaptop" x1="0" y1="0" x2="0.9" y2="1">
          <stop offset="0" stop-color="__SCREEN__"/><stop offset="1" stop-color="__INNER__"/>
        </linearGradient>
        <linearGradient id="epPeach" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#FFDAD1"/><stop offset="1" stop-color="#E5A49E"/>
        </linearGradient>
        <linearGradient id="epBase" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#F2C1B8"/><stop offset="1" stop-color="#C98E8F"/>
        </linearGradient>
        <filter id="epShadow" x="-25%" y="-30%" width="155%" height="170%">
          <feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="#9B7071" flood-opacity=".18"/>
        </filter>
      </defs>
      <ellipse cx="252" cy="229" rx="216" ry="14" fill="__PALE__" opacity=".28"/>
      <!-- Phiếu phân tích thanh khoản -->
      <g transform="translate(45 35) rotate(-7 62 51)" filter="url(#epShadow)">
        <rect width="114" height="96" rx="15" fill="__INNER__" stroke="__PALE__" stroke-width="2"/>
        <path d="M21 75H96" stroke="__INK__" stroke-opacity=".25" stroke-width="1.5"/>
        <rect x="22" y="54" width="12" height="21" rx="3" fill="__PALE__"/>
        <rect x="42" y="44" width="12" height="31" rx="3" fill="#E9ADA4"/>
        <rect x="62" y="29" width="12" height="46" rx="3" fill="#E7A6A1"/>
        <rect x="82" y="17" width="12" height="58" rx="3" fill="#C98E92"/>
        <circle cx="22" cy="20" r="4" fill="#8EC2B5"/>
      </g>
      <!-- Laptop: danh mục và nến giá -->
      <g filter="url(#epShadow)">
        <path d="M186 49Q187 32 206 31L419 30Q439 30 437 48L416 198Q414 210 399 210H165Q149 210 152 196Z"
              fill="__FRAME__" stroke="__FRAME__" stroke-width="4"/>
        <path d="M198 51Q200 44 208 44L415 43Q423 43 422 51L403 188Q402 196 394 196H173Q167 196 169 187Z"
              fill="url(#epLaptop)"/>
        <circle cx="308" cy="37" r="2" fill="__LIGHT__" opacity=".76"/>
        <path d="M148 211H439L454 223Q454 230 443 231H128Q116 229 122 223Z"
              fill="url(#epBase)" stroke="#D3A5A0" stroke-width="2"/>
        <path d="M255 213H337L330 219H261Z" fill="#C88F90" opacity=".65"/>
        <path d="M181 174H404M181 144H408M184 113H412" stroke="__INK__" stroke-width="1"
              stroke-opacity=".12" stroke-dasharray="4 6"/>
        <path d="M189 183C226 176 251 168 277 153S340 105 389 71"
              fill="none" stroke="#E6A8A0" stroke-width="3" stroke-linecap="round" opacity=".82"/>
        <!-- Nến -->
        <g stroke-width="2.4" stroke-linecap="round">
          <path d="M208 159V123M242 158V108M276 142V100M310 129V86M344 114V70M378 96V54"
                stroke="__INK__" stroke-opacity=".55"/>
        </g>
        <g>
          <rect x="203" y="135" width="10" height="17" rx="2" fill="#EBA8A0"/>
          <rect x="237" y="120" width="10" height="24" rx="2" fill="__MINT__"/>
          <rect x="271" y="113" width="10" height="20" rx="2" fill="#EBA8A0"/>
          <rect x="305" y="99" width="10" height="21" rx="2" fill="__MINT__"/>
          <rect x="339" y="84" width="10" height="22" rx="2" fill="__MINT__"/>
          <rect x="373" y="67" width="10" height="23" rx="2" fill="#EBA8A0"/>
        </g>
      </g>
      <!-- Tiền thanh khoản -->
      <g filter="url(#epShadow)">
        <ellipse cx="72" cy="202" rx="31" ry="10" fill="#D99590"/>
        <rect x="41" y="180" width="62" height="22" fill="#F0B3A6"/>
        <ellipse cx="72" cy="180" rx="31" ry="9" fill="#FFDCD1" stroke="#DA9A96" stroke-width="2"/>
        <path d="M43 190Q72 207 101 190" fill="none" stroke="#CB8988" stroke-width="2"/>
        <ellipse cx="131" cy="215" rx="25" ry="8" fill="#D99590"/>
        <rect x="106" y="190" width="50" height="25" fill="#E4A29A"/>
        <ellipse cx="131" cy="190" rx="25" ry="8" fill="#FFDCD1" stroke="#D79B97" stroke-width="2"/>
        <path d="M108 203Q131 214 154 203" fill="none" stroke="#C98986" stroke-width="2"/>
      </g>
      <!-- Phân bổ danh mục -->
      <g transform="translate(119 166)" filter="url(#epShadow)">
        <circle r="41" fill="#F8D6CD" stroke="#FFEFEB" stroke-width="3"/>
        <path d="M0 0V-40A40 40 0 0 1 38 12Z" fill="#E7A79E"/>
        <path d="M0 0 38 12A40 40 0 0 1 -6 39Z" fill="#B9D8CF"/>
        <path d="M0 0 -6 39A40 40 0 0 1 0 -40Z" fill="#F0BDB3"/>
        <circle r="13" fill="__INNER__"/>
      </g>
      <!-- Checklist chiến lược bán -->
      <g transform="translate(381 124) rotate(5 54 58)" filter="url(#epShadow)">
        <rect width="119" height="98" rx="16" fill="__LIGHT__" stroke="__PALE__" stroke-width="3"/>
        <rect x="14" y="19" width="21" height="21" rx="6" fill="#F9DED6"/>
        <path d="m19 28 5 5 8-10" fill="none" stroke="#A66E79" stroke-width="3" stroke-linecap="round"/>
        <rect x="46" y="24" width="55" height="9" rx="4.5" fill="__PALE__" opacity=".8"/>
        <rect x="14" y="54" width="21" height="21" rx="6" fill="#F9DED6"/>
        <path d="m19 63 5 5 8-10" fill="none" stroke="#A66E79" stroke-width="3" stroke-linecap="round"/>
        <rect x="46" y="59" width="44" height="9" rx="4.5" fill="__PALE__" opacity=".8"/>
      </g>
      <!-- Điểm nhấn lá mềm -->
      <g transform="translate(464 24)" fill="#EDB4A8" opacity=".83">
        <path d="M1 75C6 47 17 26 27 8" fill="none" stroke="#CE9394" stroke-width="2.5"/>
        <ellipse cx="29" cy="10" rx="8" ry="17" transform="rotate(23 29 10)"/>
        <ellipse cx="15" cy="35" rx="7" ry="15" transform="rotate(-32 15 35)"/>
        <ellipse cx="36" cy="43" rx="8" ry="15" transform="rotate(55 36 43)"/>
        <ellipse cx="3" cy="63" rx="7" ry="13" transform="rotate(-35 3 63)"/>
      </g>
    </svg>"""
    for key,value in {
        '__SCREEN__':screen,'__INNER__':inner,'__FRAME__':frame,
        '__INK__':ink,'__PALE__':pale,'__MINT__':mint,'__LIGHT__':light
    }.items():
        template=template.replace(key,value)
    return template
