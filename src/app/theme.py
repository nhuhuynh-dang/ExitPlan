"""Giao diện glass pastel lấy cảm hứng tổ chức code dashboard mẫu; không dùng hình ảnh ngoài."""
from html import escape

PEACH_ACCENT='#E6A69B'
FONT_FAMILY="'Be Vietnam Pro',sans-serif"

def hex_rgb(h): return tuple(int(h[i:i+2],16) for i in (1,3,5))
def mix(a,b,f):return '#'+''.join(f'{round(x*(1-f)+y*f):02x}' for x,y in zip(hex_rgb(a),hex_rgb(b)))
def rgba(hexcolor,alpha):return f'rgba({",".join(map(str,hex_rgb(hexcolor)))},{alpha})'

def palette(mode,accent=PEACH_ACCENT):
    accent=PEACH_ACCENT
    dark=mode=='Tối'; base='#232B38' if dark else '#FFF8F5'
    return {'bg':mix(accent,base,.94 if dark else .97),'surface':mix(accent,'#333D4C' if dark else '#FFFFFF',.82 if dark else .96),
            'sidebar':mix(accent,'#293241' if dark else '#FBEDE8',.9),
            'text':'#F7EFF0' if dark else '#443B42','muted':'#C2B7BE' if dark else '#806D75',
            'border':mix(accent,'#596172' if dark else '#EBDAD5',.70),
            'accent':accent,'positive':'#81D6BE' if dark else '#238B71',
            'negative':'#F3A5A5' if dark else '#C95555','plot':mix(accent,'#333D4C' if dark else '#FFFFFF',.82 if dark else .96)}

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
    for a,b in rep.items():css=css.replace(a,b)
    return css

def hero_svg(accent):
    """SVG inline vẽ nến, thanh danh mục và các mức sổ lệnh."""
    return f'''<svg viewBox="0 0 420 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Minh họa tài chính">
      <g fill="none" stroke="{accent}" stroke-width="3" stroke-linecap="round">
      <path d="M15 174H403" opacity=".35"/><path d="M32 138V82M76 152V74M120 129V54M164 118V42M208 103V26" />
      </g><g fill="{accent}" opacity=".74"><rect x="21" y="100" width="22" height="34" rx="4"/><rect x="65" y="89" width="22" height="42" rx="4"/><rect x="109" y="70" width="22" height="45" rx="4"/><rect x="153" y="55" width="22" height="47" rx="4"/><rect x="197" y="39" width="22" height="46" rx="4"/></g>
      <g fill="{accent}" opacity=".35"><rect x="267" y="48" width="120" height="12" rx="5"/><rect x="267" y="75" width="93" height="12" rx="5"/><rect x="267" y="102" width="61" height="12" rx="5"/><rect x="267" y="129" width="108" height="12" rx="5"/></g></svg>'''
