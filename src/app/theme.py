"""Giao diện glass pastel lấy cảm hứng tổ chức code dashboard mẫu; không dùng hình ảnh ngoài."""
from html import escape

BLUE_ACCENT='#2E83E6'
FONT_FAMILY="'Be Vietnam Pro',sans-serif"

def hex_rgb(h): return tuple(int(h[i:i+2],16) for i in (1,3,5))
def mix(a,b,f):return '#'+''.join(f'{round(x*(1-f)+y*f):02x}' for x,y in zip(hex_rgb(a),hex_rgb(b)))
def rgba(hexcolor,alpha):return f'rgba({",".join(map(str,hex_rgb(hexcolor)))},{alpha})'

def palette(mode, accent=BLUE_ACCENT):
    """Bảng màu xanh dương chuyên nghiệp, dịu ở chế độ sáng và rõ ở tối."""
    dark=mode=='Tối'
    return {
        'bg': '#0C192C' if dark else '#F0F6FD',
        'surface': '#192B43' if dark else '#FFFFFF',
        'sidebar': '#091A31' if dark else '#EAF3FC',
        'text': '#EAF3FF' if dark else '#16304F',
        'muted': '#ACBFDA' if dark else '#607A9D',
        'border': '#344A67' if dark else '#D6E4F2',
        'accent': '#69B2FF' if dark else BLUE_ACCENT,
        'positive': '#71D5B6' if dark else '#1FA587',
        'negative': '#FF98A3' if dark else '#CE6775',
        'plot': '#192B43' if dark else '#FFFFFF',
    }

def theme_css(mode,accent=BLUE_ACCENT,font=None,size_pt=12):
    p=palette(mode); accent=p['accent']; f=FONT_FAMILY; size=12
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
 .ep-brand-mark{display:grid;place-items:center;height:43px;width:43px;border-radius:14px;background:__ACCENT__;color:#FFFFFF;font-size:24px;font-weight:850;flex-shrink:0}
.ep-brand-mark svg{width:29px;height:29px;display:block;stroke:#FFFFFF;}
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
[data-testid="stDataFrame"] [role="columnheader"], [data-testid="stDataEditor"] [role="columnheader"]{background:__SURFACE__;color:__TEXT__}
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
         '__GLOW2__':rgba('#9C8CEB',.11 if mode=='Tối' else .08),'__BG__':p['bg'],'__SIDEBAR__':p['sidebar'],
         '__BORDER__':p['border'],'__TEXT__':p['text'],'__ACCENT__':accent,'__SURFACE__':p['surface'],
         '__MUTED__':p['muted'],'__GLASS__':rgba(p['surface'],.78),
         '__BUTTONTEXT__':'#FFFFFF','__WARNBG__':rgba('#F2B653',.15),'__WARNBORDER__':rgba('#F2B653',.40)}
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
    icon_color='#ECF5FF' if mode=='Tối' else '#23486D'
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
/* Hide only Deploy and unneeded menus; NEVER hide the entire Streamlit toolbar.
   The collapsed sidebar's expand control can live inside the toolbar/header. */
.stAppDeployButton, [data-testid="stAppDeployButton"],
#MainMenu, footer {display:none !important;}
header[data-testid="stHeader"] {
    background:transparent !important;box-shadow:none !important;
    visibility:visible !important;pointer-events:none;
}
header[data-testid="stHeader"] button,
header[data-testid="stHeader"] [data-testid="stToolbar"],
header[data-testid="stHeader"] [data-testid="stToolbarActions"] {
    pointer-events:auto;
}
/* Native controls: both left-pointing collapse and right-pointing expand. */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    display:flex !important;visibility:visible !important;opacity:1 !important;
    position:fixed !important;top:14px !important;left:14px !important;
    z-index:999991 !important;pointer-events:auto !important;
}
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button {
    display:inline-flex !important;visibility:visible !important;opacity:1 !important;
    justify-content:center !important;align-items:center !important;
    width:40px !important;height:40px !important;border-radius:12px !important;
    border:1px solid __BORDER__ !important;
    background:__SIDEBAR__ !important;color:__TEXT__ !important;
    box-shadow:0 3px 13px rgba(13,42,80,.13) !important;cursor:pointer !important;
}
[data-testid="stSidebarCollapsedControl"] button svg,
[data-testid="collapsedControl"] button svg {color:__TEXT__ !important;fill:__TEXT__ !important;}
[data-testid="stSidebarCollapsedControl"] button:hover,
[data-testid="collapsedControl"] button:hover {
    border-color:__ACCENT__ !important;box-shadow:0 5px 15px rgba(29,88,160,.22) !important;
}
/* ExitPlan giữ sidebar mở cố định trên desktop. Không hiển thị nút « thu gọn.
   Trên màn hình nhỏ giữ nút gốc để người dùng vẫn điều hướng được.
   Nút mở lại của Streamlit chỉ dùng để khôi phục phiên từng bị thu gọn. */
@media (min-width: 769px) {
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebar"] button[aria-label="Collapse sidebar"],
    [data-testid="stSidebar"] button[aria-label="Close sidebar"] {
        display:none !important;
        visibility:hidden !important;
    }
}
/* Một công tắc Sáng/Tối duy nhất với icon ☀️ hoặc 🌙 theo trạng thái. */
[data-testid="stSidebar"] [data-testid="stToggle"] label {
    display:flex !important;
    align-items:center !important;
    gap:9px !important;
    cursor:pointer !important;
}

/* Sidebar xanh navy ở cả hai chế độ, nội dung đổi Sáng/Tối. */
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
[data-testid="stSidebar"] [role="radiogroup"] label:hover {background:rgba(46,131,230,.12) !important;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background:rgba(46,131,230,.22) !important;
    border-color:#2E83E6 !important;
    box-shadow:inset 3px 0 0 #2E83E6;
}
[data-testid="stSidebar"] [role="radiogroup"] label p {font-weight:600 !important;font-size:.91rem;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {color:__SIDEACTIVE__ !important;font-weight:750 !important;}
[data-testid="stSidebar"] [data-testid="stToggle"] {padding:10px 11px;border:1px solid __BORDER__;border-radius:13px;background:__TOGGLEBG__;}
[data-testid="stSidebar"] .ep-brand-mark {background:#2E83E6;color:#FFFFFF;}
/* Blue mode: đồng bộ ô thông báo và toggle. */
[data-testid="stAlert"] {border-radius:14px;border-color:__BORDER__ !important;background:__ALERTBG__ !important;}
[data-testid="stAlert"][data-baseweb] {color:__TEXT__ !important;}
[data-testid="stToggle"] [role="switch"][aria-checked="true"] {background:#4298ED !important;}
[data-testid="stSidebar"] [data-testid="stToggle"] [role="switch"][aria-checked="true"] {background:#4298ED !important;}

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
    extra_css=extra_css.replace('__SIDETEXT__','#ECF4FF' if mode=='Tối' else '#173454')
    extra_css=extra_css.replace('__SIDEMUTED__','#ABC0DC' if mode=='Tối' else '#6A819C')
    extra_css=extra_css.replace('__SIDEACTIVE__','#FFFFFF')
    extra_css=extra_css.replace('__TOGGLEBG__','#163A61' if mode=='Tối' else '#D9E9FB')
    extra_css=extra_css.replace('__ALERTBG__','#1A3553' if mode=='Tối' else '#E9F3FF')
    theme_values = {
        '__TABLE_HEAD__': '#274361' if mode=='Tối' else '#EBF2FB',
        '__TABLE_ALT__': '#213550' if mode=='Tối' else '#F8FBFF',
        '__TABLE_HOVER__': '#2A4B70' if mode=='Tối' else '#EAF4FF',
        '__GOOD_BG__': '#194D49' if mode=='Tối' else '#DDF6EF',
        '__GOOD_TEXT__': '#A4E8D3' if mode=='Tối' else '#14755E',
        '__WARN_BG__': '#58432C' if mode=='Tối' else '#FFF0D9',
        '__WARN_TEXT__': '#FFD996' if mode=='Tối' else '#A76512',
        '__CHIP_BG__': '#293D68' if mode=='Tối' else '#E5EEFF',
        '__CHIP_TEXT__': '#B8CEFF' if mode=='Tối' else '#365FAC',
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
    background:rgba(72,151,235,.19) !important;
}
[data-testid="stSidebar"] div[class*="st-key-ep_nav_"] button[kind="primary"] {
    background:linear-gradient(100deg,#226BD0,#319CF0) !important;border:1px solid #58B5FC !important;
    color:__NAVACTIVE__ !important;box-shadow:inset 3px 0 0 #9BDCFF !important;
}
[data-testid="stSidebar"] div[class*="st-key-ep_nav_"] button[kind="primary"] p {
    font-weight:800 !important;
}
[data-testid="stSidebar"] div[class*="st-key-ep_nav_"] button[kind="primary"]::before {
    filter:brightness(0) invert(1) !important;
}
.ep-method-grid {
    display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
    gap:22px;padding:4px 0 8px;margin:8px 0 26px;
}
.ep-method-grid .ep-method {min-height:190px;margin:0;padding:22px 23px;display:block;}
.ep-method-grid .ep-method h3 {margin:0 0 13px;font-size:1.14rem;line-height:1.4;}
.ep-method-grid .ep-method p {margin:0;line-height:1.8;font-size:.91rem;}
@media(max-width:850px) {.ep-method-grid {grid-template-columns:1fr;gap:16px;}}
""".replace("__NAVTEXT__", '#EDF6FF' if mode=='Tối' else '#173454')
    nav_button_css=nav_button_css.replace("__NAVACTIVE__", '#FFFFFF')
    extra_css+=nav_button_css
    # Banking Insights: colored KPI scorecards, subtle panels, coordinated tables and charts.
    theme_values.update({
        '__MINT_BG__': '#173D44' if mode=='Tối' else '#EFFAF7',
        '__MINT_BORDER__': '#326968' if mode=='Tối' else '#C9EDE4',
        '__MINT_ACCENT__': '#78DDC4' if mode=='Tối' else '#36B392',
        '__MINT_ICON__': '#26555A' if mode=='Tối' else '#DCF6EE',
        '__VIOLET_BG__': '#312B4E' if mode=='Tối' else '#F7F3FE',
        '__VIOLET_BORDER__': '#554774' if mode=='Tối' else '#E4DBFA',
        '__VIOLET_ACCENT__': '#BBA6FF' if mode=='Tối' else '#9475DD',
        '__VIOLET_ICON__': '#443862' if mode=='Tối' else '#ECE4FC',
        '__BLUE_BG__': '#173958' if mode=='Tối' else '#F0F6FF',
        '__BLUE_BORDER__': '#315B7D' if mode=='Tối' else '#D5E6FE',
        '__BLUE_ACCENT__': '#82BEFF' if mode=='Tối' else '#4A93EF',
        '__BLUE_ICON__': '#264B6D' if mode=='Tối' else '#E1EEFF',
        '__AMBER_BG__': '#413828' if mode=='Tối' else '#FFF9EF',
        '__AMBER_BORDER__': '#665538' if mode=='Tối' else '#F4E3C6',
        '__AMBER_ACCENT__': '#F1C474' if mode=='Tối' else '#DA9C39',
        '__AMBER_ICON__': '#57492F' if mode=='Tối' else '#FFF0D6',
        '__HERO_BG__': '#193A5C' if mode=='Tối' else '#F0F7FF',
        '__HERO_GLOW__': '#28476B' if mode=='Tối' else '#DDEEFF',
        '__PANEL_TINT__': '#1D3552' if mode=='Tối' else '#F3F9FF',
    })
    finance_css="""
/* Navy finance dashboard: four pastel KPI tones with individual outline icons. */
.stApp [data-testid="stSidebar"] .ep-brand-title{color:__SIDEBRANDTITLE__ !important;}
.stApp [data-testid="stSidebar"] .ep-brand-sub{color:__SIDEBRANDSUB__ !important;}
.stApp [data-testid="stSidebar"] .ep-brand-mark{
    background:linear-gradient(145deg,#2067C3,#39A1F6) !important;color:#FFF !important;
}
[data-testid="stSidebar"] [data-testid="stToggle"] [data-testid="stWidgetLabel"] p {color:__SIDETOGLABEL__ !important;}
.ep-kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:14px;margin:16px 0 24px;}
[data-testid="stMarkdownContainer"] .ep-kpi-grid .ep-card{
    display:flex;align-items:center;gap:14px;min-height:125px;
    padding:17px 16px !important;border:1px solid var(--ep-card-border) !important;
    border-top:3px solid var(--ep-card-color) !important;
    background:var(--ep-card-bg) !important;border-radius:18px !important;
    box-shadow:0 10px 25px rgba(21,57,103,.045) !important;
}
.ep-card--mint{--ep-card-bg:__MINT_BG__;--ep-card-border:__MINT_BORDER__;--ep-card-color:__MINT_ACCENT__;--ep-icon-bg:__MINT_ICON__;}
.ep-card--violet{--ep-card-bg:__VIOLET_BG__;--ep-card-border:__VIOLET_BORDER__;--ep-card-color:__VIOLET_ACCENT__;--ep-icon-bg:__VIOLET_ICON__;}
.ep-card--blue{--ep-card-bg:__BLUE_BG__;--ep-card-border:__BLUE_BORDER__;--ep-card-color:__BLUE_ACCENT__;--ep-icon-bg:__BLUE_ICON__;}
.ep-card--amber{--ep-card-bg:__AMBER_BG__;--ep-card-border:__AMBER_BORDER__;--ep-card-color:__AMBER_ACCENT__;--ep-icon-bg:__AMBER_ICON__;}
.ep-card-icon{display:grid;place-items:center;width:47px;height:47px;min-width:47px;
    border-radius:15px;background:var(--ep-icon-bg);color:var(--ep-card-color);}
.ep-card-icon svg{width:25px;height:25px;}
.ep-card-copy{flex:1;min-width:0;}
.ep-kpi-value{font-size:1.61rem;line-height:1.27;font-weight:850;color:__TEXT__ !important;overflow-wrap:anywhere;}
.ep-kpi-label{font-size:.85rem;line-height:1.35;font-weight:750;color:__TEXT__ !important;margin:5px 0 0;}
.ep-kpi-note{font-size:.73rem;line-height:1.4;color:__MUTED__ !important;margin-top:5px;}
.ep-hero{background:linear-gradient(102deg,__SURFACE__ 0%,__HERO_BG__ 62%,__HERO_GLOW__ 100%) !important;
    border:1px solid __BORDER__ !important;box-shadow:0 12px 30px rgba(25,74,127,.055);}
.ep-hero-icon{color:__ACCENT__ !important;background:__BLUE_ICON__ !important;border-color:__BLUE_BORDER__ !important;}
.ep-hero .ep-eyebrow{color:__ACCENT__ !important;}
.ep-panel{background:linear-gradient(116deg,__SURFACE__ 0%,__PANEL_TINT__ 160%) !important;
    border-color:__BORDER__ !important;box-shadow:0 12px 28px rgba(21,57,103,.035);}
.ep-panel-title{color:__TEXT__ !important;display:flex;gap:10px;align-items:center;}
.ep-panel-title::before{content:"";width:8px;height:18px;border-radius:8px;background:__ACCENT__;}
.ep-method-grid .ep-method {border-top:3px solid __ACCENT__ !important;box-shadow:0 8px 20px rgba(23,62,112,.045);}
.ep-method-grid .ep-method:nth-child(4n+1){border-top-color:__MINT_ACCENT__ !important;background:__MINT_BG__ !important;}
.ep-method-grid .ep-method:nth-child(4n+2){border-top-color:__BLUE_ACCENT__ !important;background:__BLUE_BG__ !important;}
.ep-method-grid .ep-method:nth-child(4n+3){border-top-color:__VIOLET_ACCENT__ !important;background:__VIOLET_BG__ !important;}
.ep-method-grid .ep-method:nth-child(4n){border-top-color:__AMBER_ACCENT__ !important;background:__AMBER_BG__ !important;}
.ep-method-grid .ep-method h3{border-left:0 !important;padding-left:0 !important;color:__TEXT__ !important;}
.ep-method-grid .ep-method p{color:__TEXT__ !important;}
.ep-table-wrap{box-shadow:0 7px 22px rgba(18,52,102,.035);}
.ep-table th{font-weight:750 !important;}
.ep-badge{background:__BLUE_ICON__ !important;border-color:__BLUE_BORDER__ !important;color:__ACCENT__ !important;}
.ep-badge.warn{background:__WARN_BG__ !important;border-color:__AMBER_BORDER__ !important;color:__WARN_TEXT__ !important;}
[data-testid="stPlotlyChart"]{box-shadow:0 10px 28px rgba(20,54,99,.045) !important;}
@media(max-width:950px){.ep-kpi-grid{grid-template-columns:repeat(auto-fit,minmax(195px,1fr));}}
@media(max-width:640px){.ep-kpi-grid{grid-template-columns:1fr;}.ep-card-icon{width:43px;height:43px;min-width:43px;}}
"""
    finance_css=finance_css.replace('__SIDEBRANDTITLE__','#F5FAFF' if mode=='Tối' else '#173454')
    finance_css=finance_css.replace('__SIDEBRANDSUB__','#BBD1E8' if mode=='Tối' else '#66809E')
    finance_css=finance_css.replace('__SIDETOGLABEL__','#E9F4FF' if mode=='Tối' else '#173454')
    # Native Streamlit controls otherwise retain the default red pills, focus rings
    # or light backgrounds even after the custom dashboard palette switches.
    native_css="""
/* Native multiselect symbols (ACB/HPG/VPB): no more default Streamlit-red chips. */
[data-testid="stMultiSelect"] [data-baseweb="tag"],
[data-testid="stMultiSelect"] [data-baseweb="tag"] > div,
[data-testid="stMultiSelect"] [data-baseweb="tag"] > span {
    background:__CHIP_BLUE__ !important;color:#FFFFFF !important;border-radius:8px !important;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] span,
[data-testid="stMultiSelect"] [data-baseweb="tag"] svg,
[data-testid="stMultiSelect"] [data-baseweb="tag"] button,
[data-testid="stMultiSelect"] [data-baseweb="tag"] [role="button"] {
    color:#FFFFFF !important;fill:#FFFFFF !important;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] svg {stroke:#FFFFFF !important;}
[data-testid="stMultiSelect"] [data-baseweb="tag"]:hover {background:__CHIP_HOVER__ !important;}
/* Input boxes, dropdown menu and multi-select share the page's Sáng/Tối background. */
[data-testid="stMultiSelect"] [data-baseweb="select"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stDateInput"] [data-baseweb="input"] > div,
[data-testid="stTextInput"] [data-baseweb="input"] > div,
[data-testid="stNumberInput"] [data-baseweb="input"] > div {
    background:__INPUT_BG__ !important;color:__TEXT__ !important;
    border-color:__BORDER__ !important;
}
[data-testid="stMultiSelect"] input,
[data-testid="stSelectbox"] input,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input {
    color:__TEXT__ !important;
    -webkit-text-fill-color:__TEXT__;
}
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="menu"] {background:__INPUT_BG__ !important;color:__TEXT__ !important;}
[data-baseweb="popover"] [role="option"],
[data-baseweb="menu"] [role="option"] {color:__TEXT__ !important;}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="menu"] [role="option"]:hover {background:__HOVER_BG__ !important;}
[data-testid="stMultiSelect"] [data-baseweb="select"]:focus-within > div,
[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div,
[data-testid="stTextInput"] [data-baseweb="input"]:focus-within > div {
    border-color:__CHIP_BLUE__ !important;
    box-shadow:0 0 0 1px __CHIP_BLUE__ !important;
}
/* Keep the main labels readable; sidebar uses its independent foreground palette. */
[data-testid="stMain"] [data-testid="stWidgetLabel"] p {color:__TEXT__ !important;}
"""
    for old,new in {
        '__CHIP_BLUE__': '#348BEB' if mode=='Tối' else '#2E83E6',
        '__CHIP_HOVER__': '#4D9CEE' if mode=='Tối' else '#1D70C9',
        '__INPUT_BG__': '#192B43' if mode=='Tối' else '#FFFFFF',
        '__HOVER_BG__': '#294765' if mode=='Tối' else '#E6F1FE',
        '__TEXT__': p['text'], '__BORDER__': p['border'],
    }.items():
        native_css=native_css.replace(old,new)
    extra_css+=native_css
    # .streamlit/config.toml fixes Streamlit's built-in accent but its base is light.
    # In app-level Dark Mode, override the native widgets that Streamlit still renders
    # on a pale background, including selectboxes, multiselects and code examples.
    if mode=='Tối':
        dark_native_css="""
/* Native selection boxes: make the complete control navy, not just its outer wrapper. */
[data-testid="stSelectbox"] [data-baseweb="select"],
[data-testid="stMultiSelect"] [data-baseweb="select"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"] [data-baseweb="input"],
[data-testid="stMultiSelect"] [data-baseweb="select"] [data-baseweb="input"],
[data-testid="stSelectbox"] [data-baseweb="select"] [role="combobox"],
[data-testid="stMultiSelect"] [data-baseweb="select"] [role="combobox"],
[data-testid="stSelectbox"] [data-baseweb="select"] [aria-haspopup="listbox"],
[data-testid="stMultiSelect"] [data-baseweb="select"] [aria-haspopup="listbox"] {
    background-color:#192B43 !important;
    color:#EAF3FF !important;
    border-color:#344A67 !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] input,
[data-testid="stMultiSelect"] [data-baseweb="select"] input,
[data-testid="stSelectbox"] [data-baseweb="select"] [role="combobox"] *,
[data-testid="stMultiSelect"] [data-baseweb="select"] [role="combobox"] *,
[data-testid="stSelectbox"] [data-baseweb="select"] [aria-selected],
[data-testid="stMultiSelect"] [data-baseweb="select"] [aria-selected] {
    color:#EAF3FF !important;
    -webkit-text-fill-color:#EAF3FF !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] svg,
[data-testid="stMultiSelect"] [data-baseweb="select"] svg {fill:#BBD2EF !important;color:#BBD2EF !important;}
/* Keep selected ticker tags blue; they are independent of the dark input background. */
[data-testid="stMultiSelect"] [data-baseweb="tag"],
[data-testid="stMultiSelect"] [data-baseweb="tag"] > div,
[data-testid="stMultiSelect"] [data-baseweb="tag"] > span{
    background:#348BEB !important;color:#FFFFFF !important;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] span {
    color:#FFFFFF !important;-webkit-text-fill-color:#FFFFFF !important;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] svg {fill:#FFFFFF !important;stroke:#FFFFFF !important;}
/* Floating selectbox menu is rendered outside stMain in a portal. */
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] [role="option"],
[data-baseweb="menu"],
[data-baseweb="menu"] [role="option"]{
    background-color:#192B43 !important;color:#EAF3FF !important;
}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="menu"] [role="option"]:hover,
[data-baseweb="popover"] [aria-selected="true"],
[data-baseweb="menu"] [aria-selected="true"]{
    background-color:#294765 !important;color:#FFFFFF !important;
}
/* BaseWeb renders dropdown menus in a body-level portal, not inside stSelectbox.
   Style the portal root and actual UL/LI layers; older rules missed this layer. */
body [data-baseweb="popover"],
body [data-baseweb="popover"] > div,
body [data-baseweb="popover"] [data-baseweb="menu"],
body [data-baseweb="popover"] [role="listbox"],
body [data-baseweb="popover"] ul,
body [data-testid="stSelectboxVirtualDropdown"],
body [data-testid="stSelectboxVirtualDropdown"] > div,
body [data-testid="stSelectboxVirtualDropdown"] ul,
body [data-testid="stVirtualDropdown"],
body ul[role="listbox"]{
    background-color:#192B43 !important;color:#EAF3FF !important;
    border-color:#344A67 !important;
}
body [data-baseweb="popover"] li,
body [data-baseweb="popover"] [role="option"],
body [data-baseweb="menu"] li,
body [data-testid="stSelectboxVirtualDropdown"] li,
body [data-testid="stSelectboxVirtualDropdown"] [role="option"],
body ul[role="listbox"] li,
body ul[role="listbox"] [role="option"]{
    background-color:#192B43 !important;color:#EAF3FF !important;
    -webkit-text-fill-color:#EAF3FF !important;
}
body [data-baseweb="popover"] li *,
body [data-baseweb="popover"] [role="option"] *,
body [data-testid="stSelectboxVirtualDropdown"] li *,
body ul[role="listbox"] li *{
    color:#EAF3FF !important;
    -webkit-text-fill-color:#EAF3FF !important;
}
body [data-baseweb="popover"] li:hover,
body [data-baseweb="popover"] [role="option"]:hover,
body [data-baseweb="popover"] [aria-selected="true"],
body [data-baseweb="menu"] li:hover,
body [data-testid="stSelectboxVirtualDropdown"] li:hover,
body [data-testid="stSelectboxVirtualDropdown"] [aria-selected="true"],
body ul[role="listbox"] li:hover,
body ul[role="listbox"] [aria-selected="true"]{
    background-color:#294765 !important;color:#FFFFFF !important;
}
/* The visible selected value can live in a span/div rather than an input. */
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div{
    background-color:#192B43 !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] div,
[data-testid="stSelectbox"] [data-baseweb="select"] span,
[data-testid="stSelectbox"] [data-baseweb="select"] p,
[data-testid="stMultiSelect"] [data-baseweb="select"] input{
    color:#EAF3FF !important;
    -webkit-text-fill-color:#EAF3FF !important;
}

/* Streamlit st.code / Prism syntax-highlighter, copy button and code frame. */
[data-testid="stCodeBlock"],
[data-testid="stCodeBlock"] > div,
[data-testid="stCodeBlock"] pre,
[data-testid="stCodeBlock"] code,
[data-testid="stCodeBlock"] pre code,
.stCodeBlock,
.stCodeBlock pre,
.stCodeBlock code{
    background:#192B43 !important;color:#EAF3FF !important;
    border-color:#344A67 !important;
}
[data-testid="stCodeBlock"]{
    border:1px solid #344A67 !important;border-radius:13px !important;overflow:hidden !important;
}
[data-testid="stCodeBlock"] pre{
    border:0 !important;box-shadow:none !important;
}
[data-testid="stCodeBlock"] button,
[data-testid="stCodeBlock"] button:hover{
    background:#294765 !important;color:#EAF3FF !important;border:1px solid #426286 !important;
}
[data-testid="stCodeBlock"] button svg{color:#EAF3FF !important;fill:#EAF3FF !important;}
/* Command text must be readable even when Streamlit uses highlighted token spans. */
[data-testid="stCodeBlock"] .token {color:#B7D8FF !important;}
[data-testid="stCodeBlock"] .token.string,
[data-testid="stCodeBlock"] .token.attr-value {color:#8EE0C0 !important;}
[data-testid="stCodeBlock"] .token.keyword,
[data-testid="stCodeBlock"] .token.function {color:#C1AEFF !important;}
[data-testid="stCodeBlock"] .token.number,
[data-testid="stCodeBlock"] .token.operator {color:#FFD08A !important;}
/* Alert body and heading in the same dark palette (no dark-blue text on blue). */
[data-testid="stAlert"] {background:#1D3553 !important;border:1px solid #344A67 !important;}
[data-testid="stAlert"] p,
[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p{
    color:#EAF3FF !important;-webkit-text-fill-color:#EAF3FF !important;
}
"""
        extra_css+=dark_native_css
    for key,value in theme_values.items():
        finance_css=finance_css.replace(key,value)
    extra_css+=finance_css
    # Clickable pill is an ordinary, accessible Streamlit BUTTON.  The background
    # and thumb are drawn ON the button itself, not on fragile BaseWeb internals.
    # ::after is decorative (pointer-events:none), so the entire pill is clickable.
    sun_paths=(
        '<circle cx="12" cy="12" r="4"/>'
        '<path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42'
        'M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42"/>'
    )
    moon_paths='<path d="M20.985 12.486A9 9 0 0 1 11.514 3.015 9 9 0 1 0 20.985 12.486Z"/>'
    icon_paths=moon_paths if mode=='Tối' else sun_paths
    icon_svg=(
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' "
        "fill='none' stroke='#2369B4' stroke-width='1.9' "
        "stroke-linecap='round' stroke-linejoin='round'>"+icon_paths+"</svg>"
    )
    icon_uri="data:image/svg+xml,"+quote(icon_svg,safe='')
    pill_css="""
/* Compact blue switch from reference: one pill, no outer white rectangle. */
[data-testid="stSidebar"] .st-key-ep_theme_switch{
    width:106px !important;max-width:106px !important;
    margin:10px 0 20px !important;padding:0 !important;
    background:transparent !important;border:0 !important;
}
[data-testid="stSidebar"] .st-key-ep_theme_switch button {
    box-sizing:border-box !important;
    position:relative !important;display:block !important;
    width:106px !important;min-width:106px !important;max-width:106px !important;
    height:52px !important;min-height:52px !important;
    padding:0 !important;margin:0 !important;
    background:__EP_TRACK_BG__ !important;
    border:2px solid __EP_TRACK_BORDER__ !important;
    border-radius:999px !important;
    box-shadow:0 3px 10px rgba(20,72,143,.10) !important;
    cursor:pointer !important;overflow:hidden !important;
    transition:background .20s ease,border-color .20s ease !important;
}
[data-testid="stSidebar"] .st-key-ep_theme_switch button:hover {
    background:__EP_TRACK_HOVER__ !important;
    border-color:__EP_TRACK_BORDER_HOVER__ !important;
}
[data-testid="stSidebar"] .st-key-ep_theme_switch button:focus-visible {
    outline:2px solid __ACCENT__ !important;
    outline-offset:3px !important;
}
/* Keep an accessible name on the native button while visually hiding the label. */
[data-testid="stSidebar"] .st-key-ep_theme_switch button [data-testid="stMarkdownContainer"] {
    position:absolute !important;width:1px !important;height:1px !important;
    padding:0 !important;margin:-1px !important;overflow:hidden !important;
    clip-path:inset(50%) !important;white-space:nowrap !important;border:0 !important;
}
/* Thumb: SVG image is ON the button, not on Streamlit's version-dependent toggle. */
[data-testid="stSidebar"] .st-key-ep_theme_switch button::after {
    content:"" !important;display:block !important;
    position:absolute !important;left:__EP_THUMB_LEFT__ !important;top:50% !important;
    width:38px !important;height:38px !important;
    border-radius:50% !important;box-sizing:border-box !important;
    background-color:__EP_THUMB_BG__ !important;
    background-image:url("__EP_ICON_URI__") !important;
    background-position:center !important;background-repeat:no-repeat !important;
    background-size:21px 21px !important;
    box-shadow:0 2px 7px rgba(14,55,100,.16) !important;
    transform:translateY(-50%) !important;
    transition:left .22s ease,background-color .18s ease !important;
    pointer-events:none !important;
}
"""
    for old,new in {
        '__EP_TRACK_BG__':'#315A84' if mode=='Tối' else '#DDEBFF',
        '__EP_TRACK_BORDER__':'#76B9FF' if mode=='Tối' else '#2E83E6',
        '__EP_TRACK_HOVER__':'#376997' if mode=='Tối' else '#CDE3FF',
        '__EP_TRACK_BORDER_HOVER__':'#A5D2FF' if mode=='Tối' else '#1E74D6',
        '__EP_THUMB_BG__':'#F8FBFF',
        '__EP_THUMB_LEFT__':'60px' if mode=='Tối' else '5px',
        '__EP_ICON_URI__':icon_uri,
    }.items():
        pill_css=pill_css.replace(old,new)
    extra_css+=pill_css
    for key,value in theme_values.items():
        extra_css=extra_css.replace(key,value)
    css=css.replace('</style>', extra_css+'\n'.join(nav_icons)+'</style>')
    for a,b in rep.items():css=css.replace(a,b)
    return css

def hero_svg(accent=BLUE_ACCENT, mode='Sáng'):
    """Minh họa vector ExitPlan: màn hình danh mục, kế hoạch bán, tiền và thanh khoản."""
    dark=mode=='Tối'
    screen='#244260' if dark else '#FFFFFF'
    inner='#142E4B' if dark else '#F3F9FF'
    frame='#4F86C2' if dark else '#7A9FD0'
    ink='#C7E1FF' if dark else '#607D9F'
    line='#6AA8EC'
    pale='#7A9FC9' if dark else '#E0EDFC'
    mint='#65C8B2'
    light='#E7F3FF' if dark else '#FFFFFF'
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
    # Recolor the original vector into blue/teal/violet/gold without external assets.
    banking_vector_colors={
        '#FFDAD1':'#D6EAFF',
        '#E5A49E':'#68A9EC',
        '#F2C1B8':'#D7E9FA',
        '#C98E8F':'#709FCF',
        '#9B7071':'#4E78A7',
        '#E9ADA4':'#88B8E9',
        '#E7A6A1':'#63A2E3',
        '#C98E92':'#628FCE',
        '#8EC2B5':'#5CC7AC',
        '#D3A5A0':'#719ECF',
        '#C88F90':'#6D99C9',
        '#E6A8A0':'#4D9CE9',
        '#EBA8A0':'#62A9EB',
        '#D99590':'#D6A956',
        '#F0B3A6':'#ECC576',
        '#FFDCD1':'#FFE4AC',
        '#DA9A96':'#CEA34F',
        '#CB8988':'#B88F43',
        '#E4A29A':'#E6B762',
        '#D79B97':'#D1A350',
        '#C98986':'#BD9042',
        '#F8D6CD':'#CDE5FB',
        '#FFEFEB':'#EDF7FF',
        '#E7A79E':'#68A6E9',
        '#B9D8CF':'#65C6B0',
        '#F0BDB3':'#9C91E3',
        '#F9DED6':'#E7F3FF',
        '#A66E79':'#407EBB',
        '#EDB4A8':'#B7D5F4',
        '#CE9394':'#5A92CF',
    }
    for old,new in banking_vector_colors.items():
        template=template.replace(old,new)
    return template
