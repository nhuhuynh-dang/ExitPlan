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
        'bg': '#1C2635' if dark else '#FFF8F5',
        'surface': '#263345' if dark else '#FFFEFD',
        'sidebar': '#101F35' if dark else '#FFF2EE',
        'text': '#F8F1F0' if dark else '#443B42',
        'muted': '#C5BBC3' if dark else '#806D75',
        'border': '#425167' if dark else '#ECDDD7',
        'accent': PEACH_ACCENT,
        'positive': '#7FD5C0' if dark else '#238B71',
        'negative': '#F0A5AC' if dark else '#BF5B62',
        'plot': '#263345' if dark else '#FFFEFD',
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
.ep-brand-mark{display:grid;place-items:center;height:43px;width:43px;border-radius:14px;background:__ACCENT__;color:#132437;font-size:24px;font-weight:850;flex-shrink:0}
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
.ep-hero .art{position:absolute;right:1rem;top:0;width:32%;height:100%;opacity:.35;pointer-events:none}
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
@media(max-width:720px){.block-container{padding:1rem !important}.ep-hero{padding:19px}.ep-hero p{max-width:100%}.ep-hero .art{opacity:.08;width:65%}}
</style>"""
    rep={'__FONT__':f,'__SIZE__':str(size),'__GLOW__':rgba(accent,.13 if mode=='Tối' else .14),
         '__GLOW2__':rgba('#F0B6A7',.08),'__BG__':p['bg'],'__SIDEBAR__':p['sidebar'],
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
    nav_icons = []
    icon_color='#F9E8E4' if mode=='Tối' else '#5C4E58'
    for i, paths in enumerate(svg_paths, start=1):
        svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' "
               "fill='none' stroke='" + icon_color + "' stroke-width='1.8' "
               "stroke-linecap='round' stroke-linejoin='round'>" + paths + "</svg>")
        uri = "data:image/svg+xml," + quote(svg, safe='')
        nav_icons.append(
            f'[data-testid="stSidebar"] [role="radiogroup"] > label:nth-of-type({i})::before, '
            f'[data-testid="stSidebar"] [role="radiogroup"] > div:nth-child({i}) > label::before'
            + '{content:"";display:block;flex:0 0 21px;width:21px;height:21px;'
              'background-image:url("' + uri + '");background-size:contain;'
              'background-repeat:no-repeat;background-position:center;}'
        )
    extra_css = """
/* Ẩn hành động Deploy và menu không cần thiết; giữ nút mở/đóng sidebar. */
.stAppDeployButton, [data-testid="stAppDeployButton"],
[data-testid="stToolbar"], [data-testid="stToolbarActions"],
header[data-testid="stHeader"] [data-testid="stToolbar"],
#MainMenu, footer {display:none !important;}
header[data-testid="stHeader"] {background:transparent !important;box-shadow:none !important;}
/* Sidebar xanh than, icon trắng nét mảnh; trạng thái chọn hồng đào pastel. */
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
[data-testid="stSidebar"] .ep-brand-mark {background:#E6A69B;color:#233449;}
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
    extra_css=extra_css.replace('__TOGGLEBG__','#223850' if mode=='Tối' else '#FFEAE3')
    theme_values = {
        '__TABLE_HEAD__': '#344358' if mode=='Tối' else '#F8E9E3',
        '__TABLE_ALT__': '#2C3A4E' if mode=='Tối' else '#FFFAF8',
        '__TABLE_HOVER__': '#3A455A' if mode=='Tối' else '#FCEFEA',
        '__GOOD_BG__': '#183F3B' if mode=='Tối' else '#DDF5ED',
        '__GOOD_TEXT__': '#A6E6D2' if mode=='Tối' else '#166C58',
        '__WARN_BG__': '#573A39' if mode=='Tối' else '#FFF1E3',
        '__WARN_TEXT__': '#FFCCB0' if mode=='Tối' else '#A75A33',
        '__CHIP_BG__': '#4C3B4C' if mode=='Tối' else '#F5E3F0',
        '__CHIP_TEXT__': '#F8CEDF' if mode=='Tối' else '#815475',
    }
    for key,value in theme_values.items():
        extra_css=extra_css.replace(key,value)
    css=css.replace('</style>', extra_css+'\n'.join(nav_icons)+'</style>')
    for a,b in rep.items():css=css.replace(a,b)
    return css

def hero_svg(accent):
    """SVG inline vẽ nến, thanh danh mục và các mức sổ lệnh."""
    return f'''<svg viewBox="0 0 420 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Minh họa tài chính">
      <g fill="none" stroke="{accent}" stroke-width="3" stroke-linecap="round">
      <path d="M15 174H403" opacity=".35"/><path d="M32 138V82M76 152V74M120 129V54M164 118V42M208 103V26" />
      </g><g fill="{accent}" opacity=".74"><rect x="21" y="100" width="22" height="34" rx="4"/><rect x="65" y="89" width="22" height="42" rx="4"/><rect x="109" y="70" width="22" height="45" rx="4"/><rect x="153" y="55" width="22" height="47" rx="4"/><rect x="197" y="39" width="22" height="46" rx="4"/></g>
      <g fill="{accent}" opacity=".35"><rect x="267" y="48" width="120" height="12" rx="5"/><rect x="267" y="75" width="93" height="12" rx="5"/><rect x="267" y="102" width="61" height="12" rx="5"/><rect x="267" y="129" width="108" height="12" rx="5"/></g></svg>'''
