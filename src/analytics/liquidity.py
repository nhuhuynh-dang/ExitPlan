"""ADV và sigma thực nghiệm từ snapshot đã lưu. Không giả định các bản ghi là lịch sử đầy đủ."""
import numpy as np
import pandas as pd


def liquidity_statistics(books,min_sessions=5):
    """ADV proxy từ totalTradingVolume lũy kế ở quan sát CUỐI mỗi ngày.

    Chỉ công bố ADV nếu >= min_sessions. Khi recorder không chụp lúc hết phiên,
    đây là thống kê của volume tới thời điểm ghi cuối, KHÔNG phải ADV toàn phiên.
    """
    if books is None or books.empty:return pd.DataFrame(columns=['symbol','adv','sigma','n_sessions','data_kind','volume_note'])
    rows=[]
    if books['data_kind'].nunique()!=1:raise ValueError('Dữ liệu trộn nguồn')
    for sym,g in books.groupby('symbol'):
        g=g.sort_values('ts_vn').copy()
        g['trade_date']=g['ts_vn'].dt.date
        daily=g.drop_duplicates('trade_date',keep='last')
        count=len(daily)
        volumes=pd.to_numeric(daily.get('totalTradingVolume',pd.Series(index=daily.index,dtype=float)),errors='coerce')
        prices=pd.to_numeric(daily['closePrice'],errors='coerce')
        volume_ok=(volumes.notna() & volumes.ge(0)).all()
        prices_ok=(prices.notna() & prices.gt(0)).all()
        valid=count>=min_sessions and volume_ok and prices_ok
        ret=np.log(prices).diff().dropna()
        adv=float(volumes.mean()) if valid else np.nan
        sigma=float(ret.std(ddof=1)) if valid and len(ret)>1 else np.nan
        rows.append(dict(symbol=sym,adv=adv,sigma=sigma,n_sessions=count,
                         data_kind=str(g['data_kind'].iloc[0]),
                         volume_note='proxy: khối lượng lũy kế tại snapshot cuối ngày; chưa xác nhận phiên kết thúc'))
    return pd.DataFrame(rows)
