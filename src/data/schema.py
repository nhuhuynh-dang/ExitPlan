"""Tên trường chuẩn hóa từ NEO stockInfo; thay đổi tên NEO chỉ tại đây.
TODO: xác minh đơn vị giá và khối lượng trên tài khoản NEO thực tế.
"""
SNAPSHOT = 'data/processed/book_snapshots.parquet'
LIQUIDITY = 'outputs/tables/liquidity_stats.parquet'
PLANS = 'outputs/tables/plans.parquet'
FRONTIER = 'outputs/tables/frontier.parquet'
QUALITY = 'outputs/tables/data_quality.csv'
VALIDATION_GLOB = 'outputs/tables/validation_*.csv'
NEO_TO_STANDARD = {
    'symbol':'symbol','closePrice':'closePrice','totalTradingVolume':'totalTradingVolume',
    'bidPrice1':'bidPrice1','bidPrice2':'bidPrice2','bidPrice3':'bidPrice3',
    'bidVol1':'bidVol1','bidVol2':'bidVol2','bidVol3':'bidVol3',
    'askPrice1':'askPrice1','askVol1':'askVol1',
    'ceilingPrice':'ceilingPrice','floorPrice':'floorPrice','refPrice':'refPrice',
}
REQUIRED = ('ts_vn','symbol','closePrice','bidPrice1','bidVol1','bidPrice2','bidVol2','bidPrice3','bidVol3','data_kind')
KIND_LABELS={'synthetic':'giả lập', 'historical':'lịch sử', 'live':'live'}
