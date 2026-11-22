"""Các khối HTML hiển thị thuần; luôn escape dữ liệu người dùng."""
from html import escape
from src.app import fmt

def e(x): return escape(str(x),quote=True)

def badge(label,kind='default'):
    klass=' warn' if kind=='synthetic' else ''
    return f'<span class="ep-badge{klass}">{e(label)}</span>'

def cards_html(cards):
    """KPI cards with per-card pastel tint, outlined icons and escaped content.

    Each card optionally accepts tone='mint'|'violet'|'blue'|'amber'.
    Otherwise tones cycle to keep scorecards visually distinct.
    """
    icons={
        'mint':'<path d="M4 20V11m5 9V5m5 15v-8m5 8V8"/>',
        'violet':'<path d="m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5"/>',
        'blue':'<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M7 16v-4m5 4V7m5 9v-6"/>',
        'amber':'<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6m-6 4h6m-6 4h3"/>',
    }
    tones=('mint','violet','blue','amber')
    items=[]
    for i,c in enumerate(cards):
        tone=c.get('tone')
        if tone not in icons:
            tone=tones[i%len(tones)]
        svg=(
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            +icons[tone]+'</svg>'
        )
        items.append(
            '<div class="ep-card ep-card--'+tone+'">'
            '<span class="ep-card-icon">'+svg+'</span><div class="ep-card-copy">'
            '<div class="ep-kpi-value">'+e(c.get('value','–'))+'</div>'
            '<div class="ep-kpi-label">'+e(c.get('label',''))+'</div>'
            '<div class="ep-kpi-note">'+e(c.get('note',''))+'</div>'
            '</div></div>'
        )
    return '<div class="ep-kpi-grid">'+''.join(items)+'</div>'

def verdict(title,body):
    return f'<div class="ep-verdict"><strong>{e(title)}</strong><div style="margin-top:7px;line-height:1.6">{e(body)}</div></div>'

def guide(read,conclusion):
    return '<div class="ep-guide"><strong>Cách đọc hình:</strong> '+e(read)+'<div style="margin-top:6px"><strong>Kết luận:</strong> '+e(conclusion)+'</div></div>'

def html_table(headers,rows,numeric=(),tooltips=None,pills=None):
    """headers list; rows iterable of iterables; numeric = column indices."""
    tip=tooltips or {}
    h=''.join('<th'+(' class="numeric"' if i in numeric else '')+f' title="{e(tip.get(name,""))}">{e(name)}</th>' for i,name in enumerate(headers))
    rs=[]
    pills=pills or {}
    for row in rows:
        cells=[]
        for i,val in enumerate(row):
            value=e(val)
            if i in pills:
                tone=pills[i].get(str(val),'neutral')
                if tone not in ('ok','warn','neutral'):tone='neutral'
                value=f'<span class="ep-pill {tone}">{value}</span>'
            cells.append('<td'+(' class="numeric"' if i in numeric else '')+'>'+value+'</td>')
        rs.append('<tr>'+''.join(cells)+'</tr>')
    return '<div class="ep-table-wrap"><table class="ep-table"><thead><tr>'+h+'</tr></thead><tbody>'+''.join(rs)+'</tbody></table></div>'
