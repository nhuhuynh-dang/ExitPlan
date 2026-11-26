"""Đọc file đã lưu; tuyệt đối không gọi mạng, không fallback sang giả lập ngầm."""
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
from .schema import REQUIRED, KIND_LABELS
VN=ZoneInfo('Asia/Ho_Chi_Minh')

def resolve_path(root, relative, overrides=None):
    custom = (overrides or {}).get(relative)
    if custom:
        return Path(custom).expanduser()
    return Path(root)/relative

def read_parquet(root, relative, overrides=None):
    path=resolve_path(root,relative,overrides)
    if not path.is_file():
        return None, f'Chưa có dữ liệu: cần file {relative}'
    try:
        return pd.read_parquet(path), None
    except Exception as ex:
        return None, f'Không đọc được {relative}: {type(ex).__name__}: {ex}'

def read_csv(root, relative, overrides=None):
    path=resolve_path(root,relative,overrides)
    if not path.is_file():
        return None, f'Chưa có dữ liệu: cần file {relative}'
    try:
        return pd.read_csv(path), None
    except Exception as ex:
        return None, f'Không đọc được {relative}: {type(ex).__name__}: {ex}'

def normalize_book(df):
    missing=set(REQUIRED)-set(df.columns)
    if missing:
        raise ValueError('Thiếu cột snapshot: '+', '.join(sorted(missing)))
    out=df.copy()
    out['symbol']=out['symbol'].astype(str).str.strip().str.upper()
    # Datetimes coming from parquet are either timezone-aware or naive Asia/Ho_Chi_Minh.
    t=pd.to_datetime(out['ts_vn'],errors='coerce')
    if t.dt.tz is None:
        t=t.dt.tz_localize(VN,ambiguous='NaT',nonexistent='NaT')
    else:
        t=t.dt.tz_convert(VN)
    out['ts_vn']=t
    out=out.dropna(subset=['ts_vn'])
    for col in ['closePrice','totalTradingVolume','bidPrice1','bidPrice2','bidPrice3',
                'bidVol1','bidVol2','bidVol3','askPrice1','askVol1']:
        if col in out:
            out[col]=pd.to_numeric(out[col],errors='coerce')
    out['data_kind']=out['data_kind'].astype(str).str.lower().str.strip()
    invalid=set(out['data_kind'].dropna())-set(KIND_LABELS)
    if invalid:
        raise ValueError('data_kind không hợp lệ: '+', '.join(sorted(invalid)))
    return out.sort_values('ts_vn')

def latest_books(df):
    return df.drop_duplicates('symbol',keep='last').set_index('symbol',drop=False)

def available_symbols(df):
    result=[]
    for s,r in latest_books(df).iterrows():
        try:
            valid=any(float(r[f'bidPrice{i}'])>0 and float(r[f'bidVol{i}'])>0 for i in (1,2,3))
        except (TypeError,ValueError,KeyError):
            valid=False
        if valid and pd.notna(r['closePrice']) and r['closePrice']>0:
            result.append(s)
    return sorted(result)


def portfolio_snapshot(books, symbols):
    """Latest recorded evaluation with all chosen symbols; no cross-time fill."""
    syms=set(symbols)
    if not syms or len(syms)>12:
        raise ValueError("Chọn từ 1 đến 12 mã cho mỗi danh mục")
    rows=books[books.symbol.isin(syms)].copy()
    if rows.empty:
        raise ValueError("Chưa có dữ liệu cho danh mục")
    count=rows.groupby("ts_vn")["symbol"].nunique()
    valid=count[count==len(syms)]
    if valid.empty:
        raise ValueError("Chưa có thời điểm chung đủ các mã; cần thu thêm dữ liệu")
    stamp=valid.index.max()
    batch=rows[rows.ts_vn==stamp].drop_duplicates("symbol",keep="last")
    if set(available_symbols(batch))!=syms:
        raise ValueError("Snapshot chung có mã thiếu bid hợp lệ")
    return batch
