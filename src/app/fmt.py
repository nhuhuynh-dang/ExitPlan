"""Định dạng Việt Nam, không làm thay đổi dữ liệu gốc."""
import math
MINUS = '−'

def _valid(x):
    try:
        return x is not None and math.isfinite(float(x))
    except (TypeError, ValueError):
        return False

def num(x, digits=0):
    if not _valid(x):
        return '–'
    s = f'{float(x):,.{digits}f}'.replace(',', '_').replace('.', ',').replace('_', '.')
    return s.replace('-', MINUS)

def bps(x):
    return num(x, 4 if _valid(x) and 0 < abs(float(x)) < .01 else 2)

def pct(x, digits=2):
    return '–' if not _valid(x) else num(float(x)*100, digits) + '%'

def rank(x):
    return '–' if not _valid(x) else '#' + num(int(x))

def vnd(x, digits=0):
    return '–' if not _valid(x) else num(x, digits) + ' ₫'

def vnd_big(x):
    if not _valid(x):
        return '–'
    x = float(x)
    for scale, name in ((1e9,'tỷ'), (1e6,'triệu'), (1e3,'nghìn')):
        if abs(x) >= scale:
            v=x/scale
            return num(v, 2 if abs(v)<100 else 1) + f' {name} ₫'
    return vnd(x)

def shares(x):
    return '–' if not _valid(x) else num(x) + ' CP'

def signed(x, digits=2, suffix=''):
    if not _valid(x):
        return '–'
    return ('+' if float(x)>0 else '') + num(x,digits) + suffix

def csv_bom(df):
    return df.to_csv(index=False).encode('utf-8-sig')
