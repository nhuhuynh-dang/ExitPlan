"""Các khối HTML hiển thị thuần; luôn escape dữ liệu người dùng."""
from html import escape
from src.app import fmt

def e(x): return escape(str(x),quote=True)

def badge(label,kind='default'):
    klass=' warn' if kind=='synthetic' else ''
    return f'<span class="ep-badge{klass}">{e(label)}</span>'

def cards_html(cards):
    """Return card markup, cards = [{label,value,note}] (no dynamic JS)."""
    items=[]
    for c in cards:
        items.append('<div class="ep-card"><div class="ep-kpi-label">'+e(c.get('label',''))+'</div>'
                     '<div class="ep-kpi-value">'+e(c.get('value','–'))+'</div>'
                     '<div class="ep-kpi-note">'+e(c.get('note',''))+'</div></div>')
    return '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:14px;margin:12px 0 21px">'+''.join(items)+'</div>'

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
