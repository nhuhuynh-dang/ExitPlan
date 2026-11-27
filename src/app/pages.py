"""Tám trang giao diện. Chỉ đọc file; chạy analytics khi người dùng bấm nút."""
from __future__ import annotations
import json
from html import escape
from pathlib import Path
import pandas as pd
import streamlit as st
from src.app import fmt, charts
from src.app.theme import hero_svg
from src.app.components import badge,cards_html,verdict,guide,html_table
from src.data.schema import SNAPSHOT,LIQUIDITY,PLANS,FRONTIER,QUALITY,VALIDATION_GLOB,KIND_LABELS
from src.data.repository import read_parquet,read_csv,normalize_book,latest_books,available_symbols,resolve_path,portfolio_snapshot
from src.finance.engine import quote_from_row,sell_preview,hhi
from src.data.stock_search import stock_catalog,search_stocks,known_nonstandard_lots
from src.data.equity_universe import equity_catalog,equity_symbols
from src.analytics.planner import calculate,summaries,frontier
from src.analytics.feasibility import eligible_books,compatible_symbols,liquidation_capacity

NAV={
 'overview':'Tổng quan',
 'planner':'Lập phương án',
 'compare':'Kết quả & so sánh',
 'liquidity':'Rủi ro thanh khoản',
 'data':'Dữ liệu & kết nối',
 'ssi_history':'Lịch sử giá',
 'validation':'Kiểm chứng',
 'methods':'Phương pháp & giới hạn',
 'downloads':'Tải dữ liệu',
}
PAGE_HELP={
 'overview':'Toàn cảnh và tình trạng dữ liệu đã ghi.',
 'planner':'Nhập danh mục, mục tiêu ròng và mức ưu tiên.',
 'compare':'Đánh đổi chi phí – độ tập trung và giải thích phương án.',
 'liquidity':'Độ sâu ba mức mua, ADV và cảnh báo thanh khoản.',
 'data':'Nguồn, chất lượng dữ liệu và bộ ghi WebSocket.',
 'ssi_history':'SSI FastConnect V3: lịch sử giá, danh mục mã, ADV và quyền API.',
 'validation':'Bằng chứng kiểm thử và độ nhạy đã lưu.',
 'methods':'Công thức, thông số, giả định và giới hạn.',
 'downloads':'Xuất bảng kết quả CSV UTF-8 có BOM.',
}
PAGE_INFO={
 'overview':('PORTFOLIO INTELLIGENCE','Tổng quan ExitPlan','Một góc nhìn thống nhất về danh mục, khả năng thu hồi tiền mặt và tình trạng dữ liệu.'),
 'planner':('','Lập phương án thanh lý','Xây dựng phương án bán cổ phiếu phù hợp với mục tiêu tài chính của bạn.'),
 'compare':('DECISION ANALYTICS','Kết quả & so sánh','So sánh A, B, C và mốc bán tỷ trọng; chỉ báo cáo dựa trên ảnh chụp có sổ lệnh hợp lệ.'),
 'liquidity':('MARKET MICROSTRUCTURE','Rủi ro thanh khoản','Độ sâu ba mức giá mua, chênh lệch mua–bán và giới hạn khối lượng quan sát.'),
 'data':('DATA OPERATIONS','Dữ liệu & kết nối','Tình trạng file, thời gian, chất lượng dữ liệu và nhật ký bộ ghi thị trường.'),
 'ssi_history':('SSI FASTCONNECT · MARKET DATA','Lịch sử giá cổ phiếu','Giá, khối lượng, ADV từ SSI V3 khi có quyền Market Data; tách biệt dữ liệu sổ lệnh WebSocket.'),
 'validation':('MODEL GOVERNANCE','Kiểm chứng mô hình','Xem kết quả kiểm thử, phân tích độ nhạy và phát lại ảnh chụp đã lưu.'),
 'methods':('METHODOLOGY','Phương pháp & giới hạn','Giả định, công thức, mô hình tối ưu hóa và phạm vi sử dụng có trách nhiệm.'),
 'downloads':('REPRODUCIBILITY','Tải dữ liệu','Xuất các bảng đã tính để kiểm tra, đối chiếu và viết báo cáo.'),
}

def page_header(key,accent,mode='Sáng'):
    eye,title,description=PAGE_INFO[key]
    icons={
        'overview':'<path d="m3 10 9-7 9 7v10H3z"/><path d="M9 21v-8h6v8"/>',
        'planner':'<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 8h8M8 12h8M8 16h5"/>',
        'compare':'<path d="M12 3v18M4 7h16M5 7l-3 6h6l-3-6Zm14 0-3 6h6l-3-6ZM4 21h16"/>',
        'liquidity':'<path d="M3 20V4M3 20h18M8 16v-4M13 16V7M18 16V9"/>',
        'data':'<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 2 4 3 9 3s9-1 9-3V5M3 12c0 2 4 3 9 3s9-1 9-3"/>',
        'ssi_history':'<path d="m3 17 6-6 4 3 8-9M16 5h5v5"/>',
        'validation':'<path d="m12 22 8-4V7l-8-4-8 4v11l8 4ZM9 12l2 2 4-4"/>',
        'methods':'<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
        'downloads':'<path d="M12 3v12m-5-5 5 5 5-5M5 17v4h14v-4"/>'
    }
    icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+icons.get(key,icons['overview'])+'</svg>'
    eyebrow='<div class="ep-eyebrow">'+escape(eye)+'</div>' if eye else ''
    if key in ('overview','compare'):
        st.markdown('<div class="ep-overview-header'+(' ep-compare-header' if key=='compare' else '')+'"><div class="ep-overview-heading"><div>'
                    +eyebrow+'<h1>'+escape(title)+'</h1><p>'+escape(description)+'</p></div>'
                    '<span class="ep-overview-header-icon material-symbols-rounded" aria-hidden="true">'+('balance' if key=='compare' else 'monitoring')+'</span>'
                    '</div></div>',unsafe_allow_html=True)
        return
    if key=='planner':icon='<span class="material-symbols-rounded" aria-hidden="true">calculate</span>'
    html=(
        '<div class="ep-hero'+(' ep-hero-planner' if key=='planner' else '')+'"><div class="ep-hero-heading"><span class="ep-hero-icon">'+icon+'</span>'
        '<div>'+eyebrow+'<h1>'+escape(title)+'</h1></div></div>'
        '<p>'+escape(description)+'</p><div class="art">'+hero_svg(accent,mode)+'</div></div>'
    )
    st.markdown(html,unsafe_allow_html=True)

def note(message):st.info(message,icon='ℹ️')
def explain(title,txt):
    with st.expander('Giải thích · '+title):st.markdown(txt)
def choose(label,options,default=None,key=None):
    return st.segmented_control(label,options=options,default=default or options[0],key=key)

def frame_table(frame,max_rows=70):
    """Bảng chỉ đọc dạng HTML, đồng bộ light/dark và thoát nội dung không tin cậy."""
    frame=frame.head(max_rows)
    values=[]
    for row in frame.itertuples(index=False,name=None):
        values.append(['–' if pd.isna(v) else fmt.num(v,2) if isinstance(v,float) else str(v) for v in row])
    return html_table([str(x) for x in frame.columns],values,
                      numeric=tuple(i for i,c in enumerate(frame.columns)
                                    if pd.api.types.is_numeric_dtype(frame[c])))


def paged_table(frame,key,page_size=20):
    if frame.empty:
        st.info('Không có dữ liệu phù hợp.')
        return
    total=len(frame)
    pages=max(1,(total+page_size-1)//page_size)
    # Reset a stale page index when a filter reduces the available results.
    if int(st.session_state.get(key,1))>pages:st.session_state[key]=1
    page=1
    if pages>1:
        a,b=st.columns([4,1],vertical_alignment='center')
        with a:st.caption(f'{fmt.num(total)} dòng · {page_size} dòng/trang')
        with b:page=int(st.number_input('Trang',min_value=1,max_value=pages,value=1,step=1,key=key))
    part=frame.iloc[(page-1)*page_size:page*page_size]
    html=frame_table(part,max_rows=page_size).replace('class="ep-table-wrap"','class="ep-table-wrap ep-paged"',1)
    st.markdown(html,unsafe_allow_html=True)


HISTORY_STATUS={'complete':'Đủ phiên','stale':'Dữ liệu cũ','missing_sessions':'Thiếu phiên','invalid_values':'Giá/khối lượng lỗi','calendar_unavailable':'Chưa có lịch','observations_only':'Chưa đối chiếu lịch'}


def history_stats_table(stats,key,verified_volume=False):
    view=pd.DataFrame({
        'Mã':stats['symbol'],
        'ADV20 (CP/ngày)' if verified_volume else 'ADV20 (đơn vị API)':stats['adv'].map(fmt.num),
        'Biến động ngày (%)':stats['sigma'].map(lambda v:fmt.pct(v)),
        'Số phiên':stats['n_sessions'].map(fmt.num),
        'Ngày dữ liệu':pd.to_datetime(stats['asof_date'],errors='coerce').dt.strftime('%d/%m/%Y').fillna('–')
    })
    if 'quality_status' in stats:
        view['Chất lượng']=stats['quality_status'].map(HISTORY_STATUS).fillna(stats['quality_status'])
    paged_table(view,key)


def _file_version(path):
    """Metadata-only invalidation; missing/replaced files also change the key."""
    try:
        stat=path.stat()
        return (str(path.resolve()),stat.st_mtime_ns,stat.st_ctime_ns,stat.st_size,stat.st_ino)
    except OSError:
        return (str(path.absolute()),None)


@st.cache_data(show_spinner=False,max_entries=8)
def _cached_market_parquet(root,relative,file_version):
    return read_parquet(root,relative)


def _market_parquet(root,relative):
    return _cached_market_parquet(str(root),relative,_file_version(Path(root)/relative))


@st.cache_data(show_spinner=False,max_entries=12)
def _cached_ssi_stats(root,file_version,snapshot_date,allowed=None):
    from src.analytics.ssi_history_stats import asof_history_stats
    history,error=_cached_market_parquet(root,'data/processed/ssi_history.parquet',file_version)
    if history is None:raise ValueError(error)
    if allowed is not None:history=history[history.symbol.isin(allowed)]
    return asof_history_stats(history,snapshot_date,strict_calendar=True)


def _ssi_stats(root,snapshot_date=None,allowed=None):
    return _cached_ssi_stats(str(root),_file_version(Path(root)/'data/processed/ssi_history.parquet'),
                             snapshot_date,tuple(sorted(allowed)) if allowed is not None else None)


def _market_reference_panel(root,symbols):
    """Independent display-only price references; never input to the MILP."""
    from src.ingest.ssi_dashboard_close import CLOSE_FILE, market_phase, completed_date, close_references
    from src.app.live import close_controller
    symbols=list(dict.fromkeys(symbols))[:12]
    if not symbols:return
    phase=market_phase()
    if phase=='closed':
        target=completed_date()
        if target is None:return
        history,_=_market_parquet(root,'data/processed/ssi_history.parquet')
        extra,_=_market_parquet(root,CLOSE_FILE)
        values=close_references(history,extra,symbols,target)
        missing=[sym for sym in symbols if not values.get(sym,{}).get('current')]
        if missing:close_controller(root).request(missing,target)
        rows=[]
        for sym in symbols:
            v=values.get(sym)
            rows.append([sym,fmt.num(v['close'],2) if v else '–',
                         v['date'].strftime('%d/%m/%Y') if v else '–',
                         'Đúng phiên' if v and v['current'] else 'Phiên cũ' if v else 'Chưa có'])
        st.markdown('**Giá đóng cửa tham chiếu · SSI**')
        st.caption('Phiên cần lấy: '+target.strftime('%d/%m/%Y')+' · giá theo đơn vị API. Chỉ dùng để tham chiếu; không thay sổ lệnh thanh lý.')
        st.markdown(html_table(['Mã','Giá đóng cửa','Ngày giao dịch','Dữ liệu'],rows,numeric=(1,),
                    pills={3:{'Đúng phiên':'ok','Phiên cũ':'warn','Chưa có':'neutral'}}),unsafe_allow_html=True)
        if missing:st.caption('Chưa có giá đúng phiên cho '+', '.join(missing)+'. Hệ thống thử tải tự động nếu có quyền API.')
    elif phase in ('continuous','lunch','transition'):
        books,_=_market_parquet(root,'data/processed/ssi_book_snapshots.parquet')
        if books is None or books.empty or not {'source','data_kind','symbol','ts_vn','closePrice'}.issubset(books.columns):
            return
        if set(books.source)!={'ssi_fastconnect_v3_ws'} or set(books.data_kind)!={'live'}:return
        subset=books[books.symbol.isin(symbols)].sort_values('ts_vn').drop_duplicates('symbol',keep='last')
        by_symbol={r.symbol:r for r in subset.itertuples()}
        rows=[]
        for sym in symbols:
            r=by_symbol.get(sym)
            rows.append([sym,fmt.vnd(r.closePrice) if r else '–',
                         pd.Timestamp(r.ts_vn).strftime('%d/%m/%Y %H:%M:%S') if r else '–'])
        st.markdown('**Giá khớp gần nhất · snapshot SSI**')
        st.markdown(html_table(['Mã','Giá','Snapshot (UTC+7)'],rows,numeric=(1,)),unsafe_allow_html=True)
        st.caption('Cập nhật theo đợt đã chuẩn hóa. Mỗi mã có thể khác thời điểm; không sử dụng bảng này làm sổ lệnh chung để tính phương án.')


@st.fragment(run_every=15)
def _market_reference_fragment(root,symbols):
    _market_reference_panel(root,symbols)


def _data_versions(root,overrides):
    paths=['data/processed/ssi_book_snapshots.parquet','data/processed/ssi_securities.parquet',
           'data/processed/ssi_history.parquet',SNAPSHOT,LIQUIDITY,PLANS,FRONTIER,QUALITY]
    return tuple(_file_version(resolve_path(root,path,overrides)) for path in paths)


@st.cache_data(show_spinner=False,max_entries=4)
def _load_market_files(root,overrides,file_versions):
    """Cache only file-derived data, not UI or session state."""
    ssi_path='data/processed/ssi_book_snapshots.parquet'
    use_ssi=SNAPSHOT not in overrides and (Path(root)/ssi_path).is_file()
    catalog_raw,catalog_error=_market_parquet(root,'data/processed/ssi_securities.parquet')
    allowed=None
    if catalog_raw is not None:
        try:allowed=set(equity_symbols(catalog_raw))
        except ValueError as ex:catalog_error=str(ex)
    raw,err=read_parquet(root,ssi_path if use_ssi else SNAPSHOT,overrides)
    books=None
    if raw is not None:
        try:
            books=normalize_book(raw)
            if use_ssi and (books.empty or 'source' not in books or
                set(books['source'])!={'ssi_fastconnect_v3_ws'} or set(books['data_kind'])!={'live'}):
                raise ValueError('File SSI không đúng nguồn hoặc trống')
            if use_ssi:
                if allowed is None:raise ValueError('Cần danh mục SSI hợp lệ để lọc cổ phiếu')
                books=books[books.symbol.isin(allowed)].copy()
        except Exception as exc:
            books=None
            err=f'Dữ liệu không hợp lệ: {exc}'
    if not use_ssi:
        liquidity,liquidity_err=read_parquet(root,LIQUIDITY,overrides)
        saved_plans,_=read_parquet(root,PLANS,overrides)
        saved_frontier,_=read_parquet(root,FRONTIER,overrides)
        quality,_=read_csv(root,QUALITY,overrides)
    else:
        # Never reuse synthetic quality or liquidity with actual SSI snapshots.
        quality=None
        saved_plans=saved_frontier=None
        liquidity=None
        liquidity_err=None
        if books is not None and not books.empty:
            try:
                from src.analytics.ssi_history_stats import asof_history_stats
                history,herr=_market_parquet(root,'data/processed/ssi_history.parquet')
                if history is None:raise ValueError(herr)
                factors=books['history_volume_factor'].dropna().unique()
                if len(factors)!=1 or not 0<float(factors[0])<float('inf'):
                    raise ValueError('Chưa xác nhận đơn vị volume lịch sử')
                history=history[history.symbol.isin(allowed)]
                liquidity=_ssi_stats(root,books['ts_vn'].max().date(),allowed)
                liquidity['adv']*=float(factors[0])
                liquidity['volume_note']='OHLCV SSI trước ngày snapshot · CP/ngày'
            except Exception as ex:liquidity_err=str(ex)
    return dict(use_ssi=use_ssi,allowed_equities=allowed,books=books,err=err,liquidity=liquidity,liquidity_err=liquidity_err,
                saved_plans=saved_plans,saved_frontier=saved_frontier,quality=quality,overrides=overrides)

def _keep_recorded_plan(data,previous,signature,state):
    """Appending newer quotes must not rewrite an already computed evaluation.
    Clear it if the original SSI snapshot disappears or any selected quote changes.
    """
    if not data.get('use_ssi') or not previous or previous[0]!=signature[0]:
        return False
    params=state.get('ep_params') or {}
    quotes=state.get('ep_plan_quotes') or {}
    if params.get('data_kind')!='live' or not quotes or data['books'] is None:return False
    try:
        books=data['books']
        stamp=pd.Timestamp(params['snapshot_at'])
        batch=books[books.ts_vn.eq(stamp)&books.symbol.isin(quotes)].drop_duplicates('symbol',keep='last')
        if set(batch.symbol)!=set(quotes):return False
        return all(quote_from_row(row)==quotes[row['symbol']] for _,row in batch.iterrows())
    except (KeyError,TypeError,ValueError,OverflowError):
        return False


def load(root):
    overrides={}
    if str(st.query_params.get('advanced',''))=='1':
        with st.sidebar.expander('Nâng cao · đường dẫn file',expanded=False):
            for relative in [SNAPSHOT,LIQUIDITY,PLANS,FRONTIER,QUALITY]:
                value=st.text_input(relative,value=str(Path(root)/relative),key='path_'+relative)
                overrides[relative]=value
    data=_load_market_files(str(root),overrides,_data_versions(root,overrides))
    books=data['books']
    use_ssi=data['use_ssi']
    ssi_path='data/processed/ssi_book_snapshots.parquet'
    # Clear computed plans when the source or latest input snapshot changes.
    signature=(ssi_path if use_ssi else str(overrides.get(SNAPSHOT,SNAPSHOT)),
               str(books['ts_vn'].max()) if books is not None and not books.empty else '',
               tuple(sorted(books['data_kind'].unique())) if books is not None else (),
               len(books) if books is not None else 0)
    previous=st.session_state.get('ep_data_signature')
    if previous!=signature:
        if not _keep_recorded_plan(data,previous,signature,st.session_state):
            for key in ('ep_plans','ep_frontier','ep_holdings','ep_plan_quotes','ep_params'):
                st.session_state.pop(key,None)
        st.session_state['ep_data_signature']=signature
    return data


def planner_notice(message,kind='info'):
    """Single theme-aware message surface; no BaseWeb notification layers."""
    icons={'info':'info','warning':'warning','error':'error','success':'check_circle'}
    if kind not in icons:kind='info'
    role='alert' if kind in ('warning','error') else 'status'
    st.markdown(
        '<div class="ep-planner-notice '+kind+'" role="'+role+'">'
        '<span class="material-symbols-rounded" aria-hidden="true">'+icons[kind]+'</span>'
        '<span>'+escape(str(message))+'</span></div>',unsafe_allow_html=True)


def source_labels(data,compact=False):
    books=data['books']
    if books is None or books.empty:
        if compact:planner_notice('Dữ liệu thị trường chưa sẵn sàng.','warning')
        else:st.warning(data['err'] or f'Chưa có dữ liệu: cần file {SNAPSHOT}',icon=':material/info:')
        return False
    kinds=sorted(set(books['data_kind']))
    if len(kinds)>1:
        if compact:planner_notice('Nguồn dữ liệu không đồng nhất. Vui lòng kiểm tra trong Thông tin & hỗ trợ.','error')
        else:st.error('Tồn tại dữ liệu trộn nguồn live/lịch sử/giả lập. Chọn một nguồn riêng trước khi tính; hệ thống không tự trộn.',icon=':material/error:')
        return False
    kind=kinds[0]
    if kind=='synthetic':
        if compact:planner_notice('Dữ liệu giả lập — không phải báo giá thị trường thật.','warning')
        else:st.warning('Dữ liệu giả lập — không phải báo giá thị trường thật.',icon=':material/warning:')
    last=books['ts_vn'].max()
    label='SSI FastConnect V3 · snapshot đã ghi' if data.get('use_ssi') else KIND_LABELS.get(kind,kind)
    if compact:
        st.caption(label+' · '+last.strftime('%d/%m/%Y %H:%M')+' (UTC+7)')
    else:
        st.markdown(badge('Nguồn: '+label,kind)+badge('Cập nhật: '+last.strftime('%d/%m/%Y %H:%M:%S')+' · UTC+7'),unsafe_allow_html=True)
    return True

def quote_map(data):
    books=data['books']
    # Do not combine quotes recorded at different evaluation timestamps.
    aligned=books[books['ts_vn']==books['ts_vn'].max()]
    return {s:quote_from_row(row) for s,row in latest_books(aligned).iterrows() if s in available_symbols(aligned)}

def plot(fig,code):st.plotly_chart(fig,use_container_width=True,config=charts.png_config(code))

def require_result():
    p=st.session_state.get('ep_plans')
    if p is None:
        note('Chưa có phương án cho danh mục hiện tại. Vào trang “Lập phương án” và bấm “Tính phương án”.')
        return None
    return p

def _overview_kpis(cards):
    return '<div class="ep-overview-kpis">'+cards_html(cards)+'</div>'


def _overview_status(label,value,icon,ok=False):
    return ('<div class="ep-overview-status'+(' is-ok' if ok else '')+'">'
            '<span class="ep-overview-status-icon material-symbols-rounded" aria-hidden="true">'+escape(icon)+'</span>'
            '<div class="ep-overview-status-copy"><div class="ep-overview-status-label">'+escape(label)+'</div>'
            '<div class="ep-overview-status-value">'+escape(value)+'</div></div></div>')


def _overview_section(title,icon):
    st.markdown('<div class="ep-overview-section-title"><span class="material-symbols-rounded" aria-hidden="true">'
                +escape(icon)+'</span><h2>'+escape(title)+'</h2></div>',unsafe_allow_html=True)


def _overview_history_kpi(data,symbols):
    """Count eligible book symbols with complete, finite point-in-time SSI metrics."""
    card={'label':'Mã đủ ADV20 & Sigma20','value':'–',
          'note':'Chưa có thống kê lịch sử hợp lệ','tone':'mint'}
    if not data.get('use_ssi') or data.get('liquidity_err'):
        return card
    stats=data.get('liquidity')
    required={'symbol','adv','sigma','quality_status','source','data_kind'}
    if stats is None or not required.issubset(stats.columns):
        return card
    adv=pd.to_numeric(stats['adv'],errors='coerce')
    sigma=pd.to_numeric(stats['sigma'],errors='coerce')
    ready=stats[
        stats.symbol.isin(symbols) & stats.quality_status.eq('complete')
        & stats.source.eq('ssi_fastconnect_v3') & stats.data_kind.eq('historical')
        & adv.ge(0) & adv.lt(float('inf')) & sigma.ge(0) & sigma.lt(float('inf'))
    ].symbol.nunique()
    total=len(set(symbols))
    card['value']=fmt.num(ready)
    card['note']=f'{fmt.num(ready)}/{fmt.num(total)} mã · Đủ lịch sử giao dịch'
    return card


def overview(root,data,t):
    with st.container(key='ep_overview_source'):
        valid=source_labels(data)
    if not valid:
        # Khi dữ liệu thiếu, hiện trạng thái thật thay vì vẽ số liệu/bảng giả.
        st.markdown(_overview_kpis([
            {'label':'Nguồn đang thử nghiệm','value':'SSI','note':'Chưa xác nhận kết nối API thật','tone':'blue'},
            {'label':'Sổ lệnh cổ phiếu','value':'Chưa có','note':'Cần snapshot giá và khối lượng mua','tone':'mint'},
            {'label':'Mô hình A/B/C/P','value':'Chưa tính','note':'Cần dữ liệu sổ lệnh hợp lệ','tone':'violet'},
            {'label':'Dữ liệu trực tiếp','value':'Chưa kết nối','note':'Dashboard đang đọc file đã lưu','tone':'amber'},
        ]),unsafe_allow_html=True)
        st.markdown(guide(
            'Các thẻ trên phản ánh trạng thái hiện tại, không phải giá cổ phiếu hay kết quả mô phỏng.',
            'Thu thập dữ liệu có quyền truy cập phù hợp hoặc sử dụng dữ liệu giả lập được gắn nhãn để thử mô hình.'
        ),unsafe_allow_html=True)
        return
    b=data['books']; symbols=available_symbols(b)
    plans=st.session_state.get('ep_plans')
    last=b['ts_vn'].max()
    cards=[{'label':'Mã có sổ lệnh hợp lệ','value':fmt.num(len(symbols)),'note':'Chỉ đếm mã có ít nhất một bid số hợp lệ','tone':'blue'},
           _overview_history_kpi(data,symbols),
           {'label':'Bản ghi snapshot','value':fmt.num(len(b)),'note':'Không tự thay dữ liệu trống','tone':'violet'},
           {'label':'Tiền ròng phương án B','value':fmt.vnd_big(plans['B']['net']) if plans else 'Chờ',
            'note':'Bấm “Tính phương án” để có kết quả' if not plans else 'Dựa trên dữ liệu và danh mục khi tính','tone':'amber' if not plans else 'mint'}]
    st.markdown(_overview_kpis(cards),unsafe_allow_html=True)
    with st.container(key='ep_overview_layout'):
        a,c=st.columns([2,1],gap='medium')
        with a:
            with st.container(key='ep_overview_chart'):
                _overview_section('Diễn biến giá chuẩn hóa (gốc = 100)','show_chart')
                shown=st.multiselect('Mã hiển thị',symbols,default=symbols[:5],max_selections=12,key='ep_overview_symbols')
                if shown:
                    if data.get('use_ssi'):_market_reference_panel(root,shown)
                    plot(charts.overview_time_fig(b[b.symbol.isin(shown)],t),'EP01_price')
                else:st.info('Chọn ít nhất một mã để hiển thị biểu đồ.',icon=':material/info:')
        with c:
            with st.container(key='ep_overview_status'):
                _overview_section('Trạng thái nguồn dữ liệu','database')
                st.markdown(
                    '<div class="ep-overview-status-list">'
                    +_overview_status('Trạng thái dashboard','Đã đọc snapshot SSI' if data.get('use_ssi') else 'Đã đọc file dữ liệu','check_circle',ok=True)
                    +_overview_status('Thời điểm mới nhất',last.strftime('%d/%m/%Y %H:%M'),'schedule')
                    +_overview_status('Số mã có thể lập phương án',fmt.num(len(symbols)),'stacked_bar_chart')
                    +'</div><div class="ep-overview-ws-note"><span class="material-symbols-rounded" aria-hidden="true">info</span>'
                    '<span>Snapshot đã lưu không tự xác nhận WebSocket đang kết nối. Xem trạng thái SSI tại thanh bên.</span></div>',
                    unsafe_allow_html=True)
    st.markdown(
        '<div class="ep-overview-insight"><span class="material-symbols-rounded" aria-hidden="true">lightbulb</span>'
        '<div class="ep-overview-insight-body"><div><strong>Cách đọc hình</strong><p>'
        'Mỗi mã được quy về 100 ở quan sát đầu tiên để dễ so sánh biến động tương đối.</p></div>'
        '<div><strong>Kết luận</strong><p>Dữ liệu chỉ phản ánh các bản ghi đã lưu, không phải lịch sử giá được API cấp tự động.</p></div>'
        '</div></div>',unsafe_allow_html=True)


def _clear_plan():
    for key in ('ep_plans','ep_frontier','ep_holdings','ep_plan_quotes','ep_params'):
        st.session_state.pop(key,None)


def _reset_stock_preview_qty():
    # Selection is a preview only. Preserve previously computed plans.
    st.session_state['ep_stock_preview_qty']=100


def _add_selected_stock(allowed):
    symbol=st.session_state.get('ep_stock_autocomplete')
    draft=dict(st.session_state.get('ep_draft_holdings',{}))
    qty=st.session_state.get('ep_stock_preview_qty',100)
    if (symbol not in allowed or symbol in draft or len(draft)>=12
            or not isinstance(qty,int) or isinstance(qty,bool) or qty<=0):
        return
    draft[symbol]=qty
    st.session_state['ep_draft_holdings']=draft
    st.session_state.pop('ep_qty_'+symbol,None)
    _clear_plan()
    # Explicit add callback runs before widgets render.
    st.session_state['ep_stock_autocomplete']=None
    st.session_state['ep_stock_preview_qty']=100
    st.session_state['ep_stock_added_notice']=f'Đã thêm {fmt.shares(qty)} {symbol} vào danh mục.'


def _stock_preview(books, draft, symbol, info, history, use_ssi):
    """Read the same latest common snapshot used by the planner, never mix dates."""
    batch=portfolio_snapshot(books,set(draft)|{symbol})
    row=batch.loc[batch.symbol.eq(symbol)].iloc[0]
    q=quote_from_row(row)
    stamp=pd.Timestamp(row['ts_vn'])
    adv=sigma=None
    quality='Chưa có lịch sử SSI hợp lệ'
    if use_ssi and q.kind=='live' and row.get('source')=='ssi_fastconnect_v3_ws' and history is not None:
        try:
            from src.analytics.ssi_history_stats import asof_history_stats
            selected=history[history.symbol.eq(symbol)]
            if not selected.empty:
                stats=asof_history_stats(selected,stamp.date(),strict_calendar=True)
                if not stats.empty:
                    stat=stats.iloc[0]
                    quality=HISTORY_STATUS.get(stat['quality_status'],'Chưa xác định')
                    sigma=stat['sigma']
                    factor=float(row.get('history_volume_factor',float('nan')))
                    if 0<factor<float('inf'):
                        adv=stat['adv']*factor
        except (ValueError,KeyError,TypeError,OverflowError):
            quality='Không đọc được lịch sử hợp lệ'
    if q.kind=='synthetic':
        quality='Dữ liệu giả lập · không ghép lịch sử SSI'
    lot=pd.to_numeric(info.get('lotSize'),errors='coerce')
    return dict(symbol=symbol,name=info.get('name') or 'Chưa có tên doanh nghiệp',
        board=info.get('board') or 'Chưa rõ',kind=q.kind,stamp=stamp,
        last=q.last,bid=q.bids[0][0],depth=sum(v for _,v in q.bids),
        adv=adv,sigma=sigma,lot=fmt.shares(lot) if pd.notna(lot) else 'Chưa xác nhận · mô hình lô 100',
        quality=quality)


def _stock_preview_html(p):
    status='Sổ lệnh giả lập' if p['kind']=='synthetic' else 'Có sổ lệnh đã lưu'
    tone='warn' if p['kind']=='synthetic' else 'ok'
    items=[('Giá khớp gần nhất',fmt.vnd(p['last'])),('Giá mua tốt nhất (Bid 1)',fmt.vnd(p['bid'])),
           ('Độ sâu 3 mức mua',fmt.shares(p['depth'])),('ADV20',fmt.shares(p['adv']) if pd.notna(p['adv']) else 'Chưa đủ dữ liệu'),
           ('Sigma20',fmt.pct(p['sigma'],4) if pd.notna(p['sigma']) else 'Chưa đủ dữ liệu'),
           ('Lô giao dịch',p['lot'])]
    metrics=''.join('<div class="ep-stock-preview-metric"><span>'+escape(label)+'</span><strong>'+escape(value)+'</strong></div>'
                    for label,value in items)
    return ('<div class="ep-stock-preview"><div class="ep-stock-preview-head">'
            '<span class="ep-stock-preview-symbol">'+escape(p['symbol'])+'</span>'
            '<div class="ep-stock-preview-company"><strong>'+escape(p['name'])+'</strong>'
            '<span>'+escape(p['board'])+' · Phạm vi cổ phiếu đã lọc</span></div>'
            '<span class="ep-holding-status '+tone+'">'+status+'</span></div>'
            '<div class="ep-stock-preview-grid">'+metrics+'</div>'
            '<div class="ep-stock-preview-foot"><span>OHLCV: <strong>'+escape(p['quality'])+'</strong></span>'
            '<span>Snapshot chung: '+escape(p['stamp'].strftime('%d/%m/%Y %H:%M:%S'))+' (UTC+7) · Dữ liệu đã ghi</span>'
            '</div></div>')


def _change_quantity(symbol):
    draft=dict(st.session_state.get('ep_draft_holdings',{}))
    key='ep_qty_'+symbol
    # A pending widget event can arrive after removal or widget cleanup.
    # Never recreate a removed holding or overwrite its saved quantity.
    if symbol not in draft or key not in st.session_state:
        return
    qty=int(st.session_state[key])
    if draft[symbol]!=qty:
        draft[symbol]=qty
        st.session_state['ep_draft_holdings']=draft
        _clear_plan()


def _change_setting(name):
    settings=dict(st.session_state.get('ep_draft_settings',{}))
    key='ep_setting_'+name
    if key not in st.session_state:return
    settings[name]=st.session_state[key]
    st.session_state['ep_draft_settings']=settings
    _clear_plan()


def _planner_step(number,title,icon,count=''):
    counter='<span class="ep-step-count">'+escape(count)+'</span>' if count else ''
    st.markdown('<div class="ep-step-heading"><span class="ep-step-icon material-symbols-rounded" aria-hidden="true">'+escape(icon)+'</span><div><span class="ep-step-number">Bước '+str(number)+'</span><h2>'+escape(title)+'</h2></div>'+counter+'</div>',unsafe_allow_html=True)


@st.cache_data(show_spinner=False,max_entries=3)
def _planner_eligible_books(books):
    return eligible_books(books)


def planner(root,data,t):
    valid_source=source_labels(data,compact=True)
    raw_books=data['books'] if valid_source else None
    books=_planner_eligible_books(raw_books)
    raw,catalog_err=_market_parquet(root,'data/processed/ssi_securities.parquet')
    try:
        catalog=stock_catalog(raw,books,equity_only=raw is not None or data.get('use_ssi',False))
    except ValueError as ex:
        planner_notice('Danh mục cổ phiếu chưa hợp lệ. Kiểm tra Thông tin & hỗ trợ.','warning')
        catalog=stock_catalog(None,books,equity_only=True)
    if raw is None:
        planner_notice('Danh mục cổ phiếu SSI chưa sẵn sàng.','info')
    valid_symbols=set(books.symbol) if books is not None and not books.empty else set()
    kind=str(raw_books['data_kind'].iloc[0]) if raw_books is not None and not raw_books.empty else ''
    # Real daily bars are displayed only as independent history coverage, never as depth.
    history,_=_market_parquet(root,'data/processed/ssi_history.parquet')
    history_counts={}
    if history is not None and {'symbol','tradingDate','source','data_kind'}.issubset(history.columns):
        if set(history.source)=={'ssi_fastconnect_v3'} and set(history.data_kind)=={'historical'}:
            history_counts=history.groupby('symbol')['tradingDate'].nunique().to_dict()
    if 'ep_draft_holdings' not in st.session_state:
        st.session_state['ep_draft_holdings']={}
    draft=st.session_state['ep_draft_holdings']
    supported=set(catalog.symbol)-set(known_nonstandard_lots(catalog,catalog.symbol))
    compatible=compatible_symbols(books,draft) & supported
    with st.container(border=False,key='ep_planner_step1'):
        _planner_step(1,'Tìm kiếm cổ phiếu','search')
        search_col,board_col=st.columns([3,1],gap='medium')
        with board_col:
            board=st.selectbox('Sàn giao dịch',['Tất cả']+sorted(catalog.board.unique()),key='ep_stock_board')
        matches=search_stocks(catalog[catalog.symbol.isin(compatible)],board=board,exclude=draft,limit=len(catalog))
        names={r.symbol:f"{r.symbol} · {r.name or 'Chưa có tên'} · {r.board}" for r in matches.itertuples()}
        if st.session_state.get('ep_stock_autocomplete') not in names:
            st.session_state['ep_stock_autocomplete']=None
            st.session_state['ep_stock_preview_qty']=100
        with search_col:
            selected=st.selectbox('Mã hoặc tên doanh nghiệp',list(names),index=None,
                format_func=names.get,placeholder='Nhập mã hoặc tên doanh nghiệp',
                key='ep_stock_autocomplete',on_change=_reset_stock_preview_qty,
                disabled=not names or len(draft)>=12)
        st.caption(f'{len(names)} mã có thể thêm trên sàn đã chọn · '+
                   ('có ít nhất một snapshot chung với toàn bộ danh mục.' if draft else 'có sổ lệnh hợp lệ đã ghi.'))
        added=st.session_state.pop('ep_stock_added_notice',None)
        if added:planner_notice(added,'success')
        preview=None
        if selected in names and len(draft)<12:
            try:
                info=matches.loc[matches.symbol.eq(selected)].iloc[0].to_dict()
                preview=_stock_preview(books,draft,selected,info,history,data.get('use_ssi',False))
                st.markdown(_stock_preview_html(preview),unsafe_allow_html=True)
                if data.get('use_ssi'):_market_reference_fragment(root,[selected])
            except (ValueError,RuntimeError,KeyError,TypeError,IndexError,OverflowError):
                planner_notice('Chưa đọc được snapshot hợp lệ của mã này.','warning')
        with st.container(key='ep_stock_preview_actions'):
            qty_col,add_col=st.columns([1,1],vertical_alignment='bottom')
            with qty_col:
                qty=st.number_input('Số lượng cổ phiếu sở hữu',min_value=1,value=100,step=100,
                    format='%d',key='ep_stock_preview_qty',disabled=preview is None)
            with add_col:
                st.button('Thêm vào danh mục',key='ep_add_stock',icon=':material/add:',
                    type='primary',use_container_width=True,disabled=preview is None or qty<=0,
                    on_click=_add_selected_stock,args=(tuple(names),))
        st.caption('Nhập số nguyên dương. Mô hình chỉ bán theo lô 100 CP.')
        if preview is not None and qty<100:
            st.caption('Dưới lô 100 CP: vẫn thêm được vào danh mục, nhưng không thể bán theo mô hình.')
        if len(draft)>=12:
            planner_notice('Đã đủ 12 mã. Xóa một mã để thêm mã khác.','info')
        elif not names:
            planner_notice('Không có mã phù hợp với bộ lọc/snapshot chung. Thử đổi sàn, bỏ mã đang chọn hoặc thu thêm dữ liệu.','info')
    meta=catalog.set_index('symbol').to_dict('index')
    nonstandard=known_nonstandard_lots(catalog,draft)
    unknown=set(draft)-set(meta)
    with st.container(border=False,key='ep_planner_step2'):
        _planner_step(2,'Danh mục của tôi','account_balance_wallet',f'{len(draft)}/12 mã')
        if not draft:
            st.markdown('<div class="ep-planner-empty"><span class="material-symbols-rounded" aria-hidden="true">account_balance_wallet</span><strong>Danh mục đang trống</strong><span>Tìm và thêm cổ phiếu ở bước 1.</span></div>',unsafe_allow_html=True)
        else:
            widths=[1.15,.85,2.1,2.7,.7]
            with st.container(key='ep_compact_portfolio'):
                with st.container(key='ep_portfolio_head'):
                    header=st.columns(widths,vertical_alignment='center')
                    for col,label in zip(header,['Mã','Sàn','Nắm giữ (CP)','Dữ liệu','']):
                        if label:col.markdown('<span class="ep-table-label">'+escape(label)+'</span>',unsafe_allow_html=True)
                for sym,qty in list(draft.items()):
                    with st.container(key='ep_holding_'+sym):
                        a,b,n,d,e=st.columns(widths,vertical_alignment='center')
                        info=meta.get(sym,{})
                        with a:
                            st.markdown('<strong title="'+escape(info.get('name') or sym,quote=True)+'">'+escape(sym)+'</strong>',unsafe_allow_html=True)
                        with b:
                            st.markdown('<span class="ep-board-label">'+escape(info.get('board') or 'Chưa rõ')+'</span>',unsafe_allow_html=True)
                        with n:
                            st.markdown('<span class="ep-mobile-qty">Nắm giữ (CP)</span>',unsafe_allow_html=True)
                            if 'ep_qty_'+sym not in st.session_state:
                                st.session_state['ep_qty_'+sym]=int(qty)
                            st.number_input('Số lượng '+sym,min_value=0,step=100,format='%d',
                                key='ep_qty_'+sym,label_visibility='collapsed',on_change=_change_quantity,args=(sym,),
                                help='Nhập số nguyên bất kỳ. Lượng bán theo lô 100.')
                        with d:
                            if sym in unknown:
                                status,tone='Ngoài danh mục','warn'
                            elif sym in nonstandard:
                                status,tone='Lô không hỗ trợ','warn'
                            elif sym in valid_symbols:
                                status,tone=('Sổ lệnh giả lập','warn') if kind=='synthetic' else ('Có sổ lệnh','ok')
                            elif history_counts.get(sym,0):
                                status,tone='Có lịch sử · thiếu sổ lệnh','neutral'
                            else:
                                status,tone='Chưa có dữ liệu','neutral'
                            st.markdown('<span class="ep-holding-status '+tone+'">'+escape(status)+'</span>',unsafe_allow_html=True)
                        with e:
                            if st.button('',key='ep_remove_'+sym,icon=':material/delete:',
                                         help='Xóa '+sym,use_container_width=True):
                                st.session_state['ep_draft_holdings']={s:v for s,v in draft.items() if s!=sym}
                                st.session_state.pop('ep_qty_'+sym,None)
                                _clear_plan()
                                st.rerun()
                if len(draft)>=2:
                    _,actions=st.columns([3,1])
                    with actions:
                        with st.popover('Xóa toàn bộ',icon=':material/delete_sweep:',use_container_width=True):
                            st.write(f'Xóa cả {len(draft)} mã khỏi danh mục?')
                            if st.button('Xác nhận xóa',key='ep_clear_draft',type='primary',use_container_width=True):
                                st.session_state['ep_draft_holdings']={}
                                for sym in draft:st.session_state.pop('ep_qty_'+sym,None)
                                _clear_plan()
                                st.rerun()
    if draft and data.get('use_ssi'):_market_reference_fragment(root,list(draft))
    with st.container(border=False,key='ep_planner_step3'):
        _planner_step(3,'Mục tiêu và điều kiện thanh lý','tune')
        settings=st.session_state.setdefault('ep_draft_settings',dict(target=100.,lamb=.5,fee=0.,tax=0.))
        c1,c2=st.columns(2,gap='large')
        with c1:
            st.markdown('<div class="ep-form-heading">Mục tiêu thanh lý</div>',unsafe_allow_html=True)
            target=st.number_input('Tiền ròng cần thu (triệu đồng)',min_value=.1,value=float(settings['target']),step=5.,
                key='ep_setting_target',on_change=_change_setting,args=('target',))
            lamb=st.slider('Mức độ ưu tiên tối ưu',0.,1.,float(settings['lamb']),.05,
                key='ep_setting_lamb',on_change=_change_setting,args=('lamb',))
            preference='Cân bằng' if abs(lamb-.5)<1e-9 else ('Ưu tiên chi phí' if lamb<.5 else 'Ưu tiên tập trung')
            st.markdown('<div class="ep-priority-labels"><span>Giảm chi phí</span><strong>'+preference+'</strong><span>Giảm tập trung</span></div>',unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="ep-form-heading">Chi phí giao dịch</div>',unsafe_allow_html=True)
            fee=st.number_input('Phí bán giả định (%)',0.,5.,float(settings['fee']),.05,
                key='ep_setting_fee',on_change=_change_setting,args=('fee',))
            tax=st.number_input('Thuế và chi phí khác giả định (%)',0.,5.,float(settings['tax']),.05,
                key='ep_setting_tax',on_change=_change_setting,args=('tax',))
        missing=sorted(set(draft)-valid_symbols)
        zeros=sorted(s for s,v in draft.items() if v<=0)
        batch=None
        capacity=None
        quotes={}
        if not draft:st.caption('Thêm cổ phiếu để bắt đầu.')
        if draft:
            if missing:planner_notice('Thiếu sổ lệnh: '+', '.join(missing)+'.','warning')
            if zeros:planner_notice('Nhập số lượng cho: '+', '.join(zeros),'info')
            odd=sorted(s for s,v in draft.items() if 0<v<100)
            if odd:planner_notice('Dưới lô 100 CP, không thể bán theo mô hình: '+', '.join(odd)+'. Phần lẻ vẫn được giữ lại.','warning')
            if nonstandard:planner_notice('Không hỗ trợ lô giao dịch khác 100: '+', '.join(nonstandard),'warning')
            if unknown:planner_notice('Mã không còn trong danh sách tra cứu: '+', '.join(sorted(unknown)),'warning')
            if not missing and not nonstandard and not unknown:
                try:
                    batch=portfolio_snapshot(books,draft)
                    if 'lotSize' in batch and (pd.to_numeric(batch['lotSize'],errors='coerce').dropna()!=100).any():
                        raise ValueError('Danh mục chứa mã có lô giao dịch khác 100')
                    # Validate quote structure before enabling calculation.
                    quotes={r['symbol']:quote_from_row(r) for _,r in batch.iterrows()}
                    capacity=liquidation_capacity(draft,quotes,fee/100,tax/100)
                    stamp=batch['ts_vn'].max()
                    st.caption('Sổ lệnh đồng bộ: '+stamp.strftime('%d/%m/%Y %H:%M:%S')+' (UTC+7) · dữ liệu đã ghi.')
                    if data.get('use_ssi'):
                        from src.ingest.ssi_dashboard_close import market_phase
                        phase=market_phase()
                        age=(pd.Timestamp.now(tz='Asia/Ho_Chi_Minh')-stamp).total_seconds()
                        if phase!='continuous':
                            st.caption('Ngoài khung thu thập liên tục: phương án mô phỏng trên sổ lệnh đã ghi, không phải lệnh có thể khớp ngay.')
                        elif not 0<=age<=120:
                            planner_notice('Snapshot chung chưa được cập nhật trong 120 giây gần nhất. Kết quả chỉ mô phỏng trên dữ liệu đã ghi.','warning')
                except (ValueError,RuntimeError,KeyError,TypeError) as ex:
                    batch=None
                    capacity=None
                    planner_notice('Chưa có sổ lệnh đồng bộ, hợp lệ cho danh mục. Bỏ bớt mã hoặc thu thêm dữ liệu.','warning')
        if capacity is not None:
            st.markdown('<div class="ep-form-heading">Đánh giá khả năng thanh lý</div>',unsafe_allow_html=True)
            st.markdown(cards_html([
                {'label':'Giá trị danh mục','value':fmt.vnd_big(capacity['value']),'note':'Theo giá khớp gần nhất'},
                {'label':'Tiền ròng tối đa','value':fmt.vnd_big(capacity['max_net']),'note':'Ba mức mua · sau phí và thuế'},
                {'label':'Số lượng có thể bán','value':fmt.shares(capacity['sellable_shares']),'note':'Lô 100 · trong độ sâu quan sát'},
                {'label':'Mã đồng bộ','value':f'{len(quotes)}/{len(draft)}','note':'Cùng một snapshot đã ghi'}]),unsafe_allow_html=True)
            if capacity['sellable_shares']==0:
                planner_notice('Không có lô 100 CP nào có thể bán. Tăng lượng nắm giữ hoặc thu thêm sổ lệnh.','warning')
            elif capacity['max_net']<target*1e6-.01:
                planner_notice('Mục tiêu vượt khả năng thanh lý ước tính, thiếu ít nhất '+fmt.vnd(target*1e6-capacity['max_net'])+'. Vẫn có thể tính phương án thu tối đa.','warning')
            else:
                planner_notice('Mục tiêu nằm trong giới hạn tiền ròng tối đa ước tính; kết quả còn phụ thuộc ràng buộc mô hình.','success')
        demo_ok=True
        if kind=='synthetic':
            demo_ok=st.checkbox('Cho phép tính thử bằng dữ liệu GIẢ LẬP',key='ep_demo_opt_in',on_change=_clear_plan)
        ready=bool(draft) and batch is not None and not zeros and demo_ok and capacity is not None and capacity['sellable_shares']>0
        run=st.button('Tính phương án',icon=':material/calculate:',type='primary',
                      use_container_width=True,disabled=not ready,key='ep_calculate_plan')
        if run and ready:
            _clear_plan()
            try:
                holdings=dict(draft)
                with st.spinner('Đang tính phương án bán…'):
                    plans=calculate(holdings,quotes,target*1e6,lamb,fee/100,tax/100)
                    fr=frontier(holdings,quotes,target*1e6,fee/100,tax/100)
                st.session_state['ep_plans']=plans
                st.session_state['ep_frontier']=fr
                st.session_state['ep_holdings']=holdings
                st.session_state['ep_plan_quotes']=quotes
                st.session_state['ep_params']=dict(target=target*1e6,lamb=lamb,fee=fee/100,tax=tax/100,
                     snapshot_at=str(batch['ts_vn'].max()),data_kind=kind)
                planner_notice('Đã tính 4 phương án. Xem Kết quả & so sánh.','success')
            except Exception as ex:
                _clear_plan()
                planner_notice('Không thể tính phương án. Vui lòng kiểm tra dữ liệu và thử lại.','error')
    plans=st.session_state.get('ep_plans')
    if plans:
        p=plans['B']; st.markdown(cards_html([
            {'label':'Phương án cân bằng B','value':fmt.vnd_big(p['net']),'note':'Tiền ròng mô phỏng'},
            {'label':'Chi phí thanh khoản','value':fmt.vnd_big(p['cost']),'note':fmt.bps(p['cost_bps'])+' bps trên doanh số'},
            {'label':'HHI sau bán','value':fmt.num(p['hhi'],4),'note':'Độ tập trung danh mục còn lại'},
            {'label':'Mục tiêu','value':'Đạt' if p['satisfied'] else 'Chưa đạt','note':fmt.vnd_big(p['shortfall'])+' thiếu hụt'}]),unsafe_allow_html=True)
        st.markdown(verdict('Kết quả phương án B', 'Đạt mục tiêu ròng trong độ sâu ba bid quan sát.' if p['satisfied'] else
            'Mục tiêu không khả thi trong độ sâu ba mức mua; xem phần thiếu hụt.'),unsafe_allow_html=True)
    with st.expander('Điều kiện và phương pháp tính',icon=':material/info:'):
        st.markdown('Mô hình cần sổ lệnh tại một thời điểm chung của danh mục; OHLCV không thay thế sổ lệnh. Số lượng nắm giữ nhập tự do, lượng bán theo lô 100 và phần lẻ được giữ lại. Mức ưu tiên λ giữ nguyên từ 0 (chi phí) đến 1 (độ tập trung); 0,5 là mức cân bằng. Phí và thuế do người dùng giả định, mặc định 0%. Không đọc tài khoản hoặc đặt lệnh thật. Danh mục SSI được lọc theo phạm vi cổ phiếu; mã chưa có phân loại rõ chỉ là ứng viên.')


def compare(root,data,t):
    with st.container(key='ep_compare_source'):
        if not source_labels(data):return
    plans=require_result()
    columns=['Phương án','Tiền ròng','Chi phí TK','Chi phí bps','Chưa bao phủ','HHI sau bán','Tỷ trọng lớn nhất','Thiếu hụt','Mục tiêu']
    if not plans:
        saved=data['saved_plans']
        if saved is not None and not saved.empty:
            st.warning('BẢNG MẪU ĐÃ LƯU (không gắn với danh mục tự nhập hiện tại). Chỉ để kiểm tra giao diện.')
            st.markdown(frame_table(saved),unsafe_allow_html=True)
        with st.container(key='ep_compare_pending'):
            _overview_section('Bảng tổng hợp phương án','table_chart')
            st.markdown(html_table(columns,[[k]+['–']*7+['Chưa chạy'] for k in ('A','B','C','P')],
                numeric=set(range(1,8)),pills={8:{'Chưa chạy':'neutral'}}),unsafe_allow_html=True)
        return
    params=st.session_state['ep_params']
    if str(data['books']['ts_vn'].max())!=params['snapshot_at']:
        st.caption('Đang xem phương án đã cố định tại snapshot khi tính; có thể sớm hơn dữ liệu mới nhất. Tính lại để dùng snapshot chung mới.')
    st.caption('Nguồn kết quả: '+KIND_LABELS.get(params['data_kind'],params['data_kind'])+
               ' · snapshot '+params['snapshot_at']+' · phương án từ bộ tối ưu bên ngoài giao diện.')
    rows=[]
    for k,p in plans.items():
        rows.append([k+' · '+p['label'],fmt.vnd(p['net']),fmt.vnd(p['cost']),fmt.bps(p['cost_bps']),
                     fmt.shares(p['uncovered']),fmt.num(p['hhi'],4),fmt.pct(p['max_weight']),
                     fmt.vnd(p['shortfall']),'Đạt' if p['satisfied'] else 'Chưa đạt'])
    selected=st.session_state.get('ep_compare_selected') or 'B'
    with st.container(key='ep_compare_table'):
        _overview_section('Bảng tổng hợp phương án','table_chart')
        st.markdown(html_table(columns,rows,numeric=set(range(1,8)),pills={8:{'Đạt':'ok','Chưa đạt':'warn'}},
            tooltips={'Chi phí TK':'Chênh lệch so với giá gần nhất ở lượng được bao phủ','HHI sau bán':'Tổng bình phương tỷ trọng giá trị còn lại'},
            highlight_row=list(plans).index(selected) if selected in plans else None),unsafe_allow_html=True)
    with st.container(key='ep_compare_filter'):
        sel=choose('Xem chi tiết', ['A','B','C','P'],default='B',key='ep_compare_selected') or 'B'
    p=plans[sel]
    kpi=[{'label':'Tiền thu ròng','value':fmt.vnd_big(p['net']),'note':'Ước tính tại một thời điểm'},
         {'label':'Chi phí thanh khoản','value':fmt.vnd_big(p['cost']),'note':fmt.bps(p['cost_bps'])+' bps'},
         {'label':'HHI sau bán','value':fmt.num(p['hhi'],4),'note':'Chỉ số tập trung danh mục'},
         {'label':'Thiếu mục tiêu','value':fmt.vnd_big(p['shortfall']),'note':'0 nếu đạt mục tiêu'}]
    for card,tone in zip(kpi,('blue','mint','blue','mint' if p['satisfied'] else 'amber')):card['tone']=tone
    st.markdown('<div class="ep-compare-kpis">'+cards_html(kpi)+'</div>',unsafe_allow_html=True)
    achieved={k:p for k,p in plans.items() if p['satisfied']}
    if achieved:
        min_cost=min(p['cost'] for p in achieved.values())
        min_hhi=min(p['hhi'] for p in achieved.values())
        best_cost=', '.join(k for k,p in achieved.items() if abs(p['cost']-min_cost)<.01)
        best_hhi=', '.join(k for k,p in achieved.items() if abs(p['hhi']-min_hhi)<1e-9)
        st.markdown(verdict('So sánh các phương án đạt mục tiêu',
            'Chi phí thanh khoản thấp nhất: '+best_cost+' ('+fmt.vnd(min_cost)+'). HHI thấp nhất: '+best_hhi+' ('+fmt.num(min_hhi,4)+'). So sánh theo tiền ròng, chi phí và cơ cấu danh mục còn lại.'),unsafe_allow_html=True)
        if 'B' in achieved and 'P' in achieved:
            saving=plans['P']['cost']-plans['B']['cost']
            text=('B tiết kiệm '+fmt.vnd(saving) if saving>0 else 'B tốn thêm '+fmt.vnd(-saving) if saving<0 else 'B có cùng chi phí thanh khoản')
            st.markdown(verdict('Đối chiếu B với mốc tỷ trọng P',text+' so với P. Hai phương án có thể thu tiền ròng khác nhau.'),unsafe_allow_html=True)
    else:
        best_net=max(p['net'] for p in plans.values())
        planner_notice('Không phương án nào đạt mục tiêu. Tiền ròng cao nhất: '+fmt.vnd(best_net)+'. Giảm mục tiêu hoặc thay đổi danh mục; không diễn giải chênh lệch chi phí như lợi ích của phương án đạt mục tiêu.','warning')
    st.warning('Ước tính chi phí chỉ dựa trên BA mức giá mua tại thời điểm quan sát, KHÔNG phải giá khớp thực. Phần vượt độ sâu chỉ được báo dưới dạng khoảng lạc quan – bi quan.')
    with st.container(key='ep_compare_charts'):
        c1,c2=st.columns(2,gap='medium')
        with c1, st.container(key='ep_compare_tradeoff'):
            _overview_section('Đánh đổi chi phí – tập trung','scatter_plot')
            plot(charts.compare_style(charts.tradeoff_fig(st.session_state.get('ep_frontier'),plans,t),t),'EP02_tradeoff')
            st.markdown(guide('Mỗi điểm là phương án tối ưu ở một giá trị λ; vị trí A/B/C được đánh dấu.',
                'Đường này phản ánh kết quả theo ràng buộc và hàm mục tiêu mô phỏng, không phải lợi nhuận kỳ vọng.'),unsafe_allow_html=True)
        with c2, st.container(key='ep_compare_holdings'):
            _overview_section('Giá trị danh mục trước/sau','bar_chart')
            plot(charts.compare_style(charts.holdings_fig(p['details'],t),t),'EP03_holdings')
            st.markdown(guide('Chiều cao mỗi cột là số cổ phiếu còn nắm giữ × giá gần nhất.',
                'Bán cổ phiếu có thể làm cơ cấu danh mục thay đổi đáng kể.'),unsafe_allow_html=True)
    with st.container(key='ep_compare_waterfall'):
        _overview_section('Thác chi phí từ giá trị tham chiếu đến tiền ròng','waterfall_chart')
        plot(charts.compare_style(charts.waterfall_fig(p,t),t,wide=True),'EP04_cost_waterfall')
        st.markdown(guide('Mốc đầu là giá trị lượng bán theo giá gần nhất; lần lượt trừ chi phí thanh khoản, phí và thuế giả định.',
            'Tiền ròng chỉ áp dụng với lượng bán nằm trong ba mức mua đang quan sát.'),unsafe_allow_html=True)
    detail=pd.DataFrame(p['details']).rename(columns={'symbol':'Mã','held':'Nắm giữ','sold':'Bán','remaining':'Còn lại','net':'Tiền ròng','visible_depth':'Độ sâu ba mức','uncovered':'Chưa bao phủ'})
    with st.container(key='ep_compare_detail'):
        _overview_section('Chi tiết thanh lý theo cổ phiếu','list_alt')
        st.markdown(frame_table(detail[['Mã','Nắm giữ','Bán','Còn lại','Độ sâu ba mức','Tiền ròng']]),unsafe_allow_html=True)
    explain('Các cột phương án','**HHI** = Σ(tỷ trọng giá trị còn lại)². **Chi phí bps** = (chi phí thanh khoản/doanh số khớp mô phỏng) × 10.000. **A/B/C/P** là tối ưu hóa theo các hàm mục tiêu khác nhau; không được hiểu là khuyến nghị mua bán.')
    with st.expander('Xuất kết quả CSV',icon=':material/download:'):
        downloads(root,data,t,show_source=False,include_liquidity=False)


def liquidity(root,data,t):
    if data['books'] is None or data['books'].empty:
        st.info('Chưa có sổ lệnh. Có thể xem thanh khoản lịch sử bên dưới.')
        history,_=_market_parquet(root,'data/processed/ssi_history.parquet')
        if history is not None:
            from src.analytics.ssi_history_stats import asof_history_stats
            allowed=data.get('allowed_equities')
            if allowed is None:return st.info('Cần danh mục SSI hợp lệ để lọc cổ phiếu.')
            history=history[history.symbol.isin(allowed)]
            if history.empty:return st.info('Chưa có lịch sử cổ phiếu hợp lệ.')
            stats=_ssi_stats(root,allowed=allowed)
            st.subheader('Thanh khoản lịch sử')
            names=sorted(stats.symbol.unique())
            draft=st.session_state.get('ep_draft_holdings',{})
            selected=st.multiselect('Tìm mã cổ phiếu',names,default=[s for s in draft if s in names][:12],key='ep_liq_hist_search',placeholder='Nhập mã cần xem',max_selections=12)
            view=stats[stats.symbol.isin(selected)] if selected else stats
            st.caption('ADV20 theo đơn vị API, chưa xác minh quy đổi. Chưa thể tính tỷ lệ tham gia khi thiếu sổ lệnh.')
            history_stats_table(view,'ep_liq_hist_page')
            st.download_button('Tải thống kê CSV',fmt.csv_bom(view),'ExitPlan_historical_liquidity.csv','text/csv',icon=':material/download:')
        return
    if not source_labels(data):return
    quotes=st.session_state.get('ep_plan_quotes') or quote_map(data)
    if not quotes:st.error('Không có dữ liệu sổ lệnh hợp lệ.');return
    if not st.session_state.get('ep_plan_quotes') and len(quotes)>12:
        selected=st.multiselect('Mã xem thanh khoản',sorted(quotes),default=sorted(quotes)[:5],max_selections=12)
        quotes={s:quotes[s] for s in selected}
    qstats=data['liquidity']
    if data.get('use_ssi') and st.session_state.get('ep_params'):
        try:
            from src.analytics.ssi_history_stats import asof_history_stats
            history,_=_market_parquet(root,'data/processed/ssi_history.parquet')
            factor=float(data['books']['history_volume_factor'].iloc[0])
            qstats=_ssi_stats(root,pd.Timestamp(st.session_state['ep_params']['snapshot_at']).date())
            qstats['adv']*=factor
        except Exception as ex:
            qstats=None
            st.warning('Không tính được ADV theo thời điểm danh mục: '+str(ex))
    if data.get('use_ssi'):
        st.caption('ADV20 cần đủ 20 phiên theo lịch 2026 trước snapshot; Sigma20 cần 21 giá đóng cửa liên tiếp. Không nội suy phiên thiếu.')
        if qstats is None:st.warning(data.get('liquidity_err') or 'Chưa có ADV20 hợp lệ.')
    elif qstats is not None and ('data_kind' not in qstats or set(qstats['data_kind'])!=set(data['books']['data_kind'])):
        qstats=None
        st.warning('Bỏ ADV không cùng loại dữ liệu với sổ lệnh.')
    part_threshold=st.slider('Ngưỡng cảnh báo tham gia so với ADV (%)',1,100,10,1)
    holdings=st.session_state.get('ep_holdings',{})
    p=st.session_state.get('ep_plans',{}).get('B')
    sold_map={d['symbol']:d['sold'] for d in p['details']} if p else {}
    adv={}
    if qstats is not None and {'symbol','adv'}.issubset(qstats.columns):
        adv=dict(zip(qstats['symbol'],qstats['adv']))
    rows=[]; alerts=[]
    quality_map=dict(zip(qstats['symbol'],qstats['quality_status'])) if qstats is not None and 'quality_status' in qstats else {}
    for s,q in quotes.items():
        depth=sum(v for _,v in q.bids)
        qty=sold_map.get(s,0)
        a=adv.get(s)
        participation=qty/a if a is not None and pd.notna(a) and a>0 else None
        spread=((q.ask1-q.bids[0][0])/((q.ask1+q.bids[0][0])/2)*10000
                if q.ask1 is not None and q.bids and q.ask1>0 else None)
        rows.append([s,fmt.shares(a),fmt.pct(participation),fmt.shares(depth),fmt.bps(spread),fmt.shares(qty)])
        if data.get('use_ssi') and (a is None or pd.isna(a) or a<=0):
            alerts.append(f"{s}: chưa tính được tỷ lệ tham gia ADV — "+HISTORY_STATUS.get(quality_map.get(s),'thiếu lịch sử hợp lệ'))
        if qty>depth:alerts.append(f'{s}: khối lượng bán vượt độ sâu quan sát')
        if participation is not None and participation*100>part_threshold:
            alerts.append(f'{s}: tỷ lệ tham gia {fmt.pct(participation)} vượt ngưỡng {part_threshold}%')
    st.markdown(html_table(['Mã','ADV','Tỷ lệ tham gia π','Độ sâu 3 bid','Spread (bps)','Dự kiến bán'],rows,numeric=(1,2,3,4,5),
        tooltips={'ADV':'Khối lượng bình quân theo ngày từ file liquidity_stats','Tỷ lệ tham gia π':'Lượng bán theo B / ADV; không phải xác suất khớp'}),unsafe_allow_html=True)
    for message in alerts:st.warning(message)
    st.subheader('Độ sâu sổ lệnh theo mã')
    plot(charts.depth_fig(quotes,t),'EP05_depth')
    st.markdown(guide('Ba màu lần lượt biểu diễn khối lượng chờ mua tại ba mức giá.',
      'Độ sâu đang hiển thị không bảo đảm tồn tại đến lúc lệnh thật tới sàn.'),unsafe_allow_html=True)
    st.subheader('Giới hạn bán toàn bộ vị thế (khoảng kịch bản)')
    st.caption('Cận bi quan: chỉ thu tiền từ độ sâu hiện thấy; cận lạc quan: giả định phần thiếu được bán ở giá gần nhất. Đây là giả định minh họa, không phải dự báo.')
    range_rows=[]
    for s,held in holdings.items():
        if s not in quotes:continue
        z=sell_preview(quotes[s],held,0.,0.)
        if z['uncovered']:
            range_rows.append([s,fmt.shares(z['uncovered']),fmt.vnd(z['bound_low']),fmt.vnd(z['bound_high'])])
    if range_rows:st.markdown(html_table(['Mã','Vượt độ sâu','Bi quan','Lạc quan'],range_rows,numeric=(1,2,3)),unsafe_allow_html=True)
    else:note('Không có vị thế vượt độ sâu được quan sát, hoặc chưa nhập danh mục.')
    if qstats is None:st.caption('Chưa có ADV để tính tỷ lệ tham gia.')
    else:
        st.download_button('Tải bảng thanh khoản CSV',fmt.csv_bom(qstats),'ExitPlan_liquidity.csv','text/csv',icon=':material/download:')


def ssi_history(root,data,t):
    path=Path(root)/'data/processed/ssi_history.parquet'
    stats_path=Path(root)/'outputs/tables/ssi_liquidity_stats.parquet'
    # Investor-facing view: technical commands and the full security catalog
    # remain in Data & connection, not on the price history page.
    if not path.exists():
        st.info('Chưa có lịch sử giá đã lưu.')
        return
    try:
        h,herr=_market_parquet(root,'data/processed/ssi_history.parquet')
        if h is None:raise ValueError(herr)
        required={'symbol','tradingDate','close','volume','data_kind','source'}
        if not required.issubset(h.columns):raise ValueError('Thiếu cột: '+', '.join(sorted(required-set(h.columns))))
        if h.empty:return st.warning('File lịch sử SSI trống.')
        if set(h['data_kind'])!={'historical'}:raise ValueError('Nhãn data_kind không phải historical')
        origins=set(h['source'].dropna().astype(str))
        if origins!={'ssi_fastconnect_v3'}:
            raise ValueError('Nguồn lịch sử chưa được xác minh là SSI FastConnect V3.')
        h['tradingDate']=pd.to_datetime(h['tradingDate'],errors='coerce')
        allowed=data.get('allowed_equities')
        if allowed is None:
            st.warning('Cần cập nhật danh mục SSI để xác định phạm vi cổ phiếu.');return
        h=h[h.symbol.isin(allowed)]
        if h.empty:return st.info('Chưa có lịch sử cho mã cổ phiếu trong phạm vi đã lọc.')
        names=sorted(h['symbol'].dropna().unique().tolist())
        raw,_=_market_parquet(root,'data/processed/ssi_securities.parquet')
        catalog=stock_catalog(raw,equity_only=True)
        labels={r.symbol:f'{r.symbol} · {r.name}' for r in catalog.itertuples()}
        draft=st.session_state.get('ep_draft_holdings',{})
        defaults=[s for s in draft if s in names][:5] or names[:1]
        selected=st.multiselect('Tìm mã cổ phiếu',names,default=defaults,max_selections=12,
            format_func=lambda s:labels.get(s,s),placeholder='Nhập mã hoặc tên doanh nghiệp',key='ep_price_search')
        st.caption('Nguồn SSI · dữ liệu cuối ngày đã lưu')
        if selected:_market_reference_fragment(root,selected)
        view=h[h['symbol'].isin(selected)].copy().sort_values(['symbol','tradingDate'])
        if view.empty:return st.info('Chọn ít nhất một mã để xem dữ liệu SSI.')
        from plotly import graph_objects as go
        f=go.Figure()
        ssi_colors=[t['accent'],t['secondary'],t['tertiary'],'#E3AC55','#609CD8']
        for i,(sym,g) in enumerate(view.groupby('symbol')):
            f.add_trace(go.Scatter(x=g['tradingDate'],y=g['close'],mode='lines+markers',
                                   line=dict(color=ssi_colors[i%len(ssi_colors)],width=2.7),
                                   marker=dict(size=5),name=sym))
        charts.layout(f,t,height=370,legend=True)
        f.update_yaxes(title='Giá đóng cửa (theo đơn vị API)')
        plot(f,'SSI_daily_close')
        st.markdown(cards_html([{'label':'Mã có dữ liệu','value':str(view['symbol'].nunique()),'note':'Từ file đã lưu'},
              {'label':'Số dòng OHLCV','value':fmt.num(len(view)),'note':'Theo ngày giao dịch'},
              {'label':'Ngày mới nhất','value':view['tradingDate'].max().strftime('%d/%m/%Y'),'note':'Không phải báo giá tức thời'}]),unsafe_allow_html=True)
        if not h.empty:
            from src.analytics.ssi_history_stats import asof_history_stats
            stats=_ssi_stats(root,allowed=allowed)
            st.subheader('ADV 20 phiên và độ biến động')
            if {'symbol','adv','sigma','n_sessions','asof_date','source','data_kind'}.issubset(stats.columns) and set(stats.source)=={'ssi_fastconnect_v3'} and set(stats.data_kind)=={'historical'}:
                history_stats_table(stats[stats.symbol.isin(selected)],'ep_price_stats_page')
                st.caption('ADV20 theo đơn vị API. Chỉ tính trên các phiên theo lịch 2026, không nội suy dữ liệu thiếu.')
        st.subheader('Lịch sử giao dịch')
        columns={'symbol':'Mã','tradingDate':'Ngày','open':'Mở cửa','high':'Cao nhất','low':'Thấp nhất','close':'Đóng cửa','volume':'Khối lượng'}
        shown=view.sort_values(['tradingDate','symbol'],ascending=[False,True])[[k for k in columns if k in view]].copy()
        shown['tradingDate']=shown.tradingDate.dt.strftime('%d/%m/%Y')
        for k in ('open','high','low','close'):
            if k in shown:shown[k]=shown[k].map(lambda v:fmt.num(v,2))
        shown['volume']=shown.volume.map(fmt.num)
        paged_table(shown.rename(columns=columns),'ep_price_history_page')
        st.download_button('Tải lịch sử CSV',fmt.csv_bom(view),'ExitPlan_SSI_history.csv','text/csv',icon=':material/download:')
        explain('Nguồn và đơn vị','Giá và khối lượng theo đơn vị gốc SSI; dữ liệu lịch sử không thay thế sổ lệnh để lập phương án.')
    except Exception as exc:st.error(f'Lỗi đọc dữ liệu SSI: {type(exc).__name__}: {exc}')


def data_page(root,data,t):
    """Trình bày thống kê và trạng thái kết nối theo thẻ, không nhúng Excel/JSON thô."""
    valid=source_labels(data)
    b=data['books']
    if valid:
        duration=b['ts_vn'].max()-b['ts_vn'].min()
        st.markdown(cards_html([
            {'label':'Số ngày giao dịch đã lưu','value':fmt.num(b['ts_vn'].dt.date.nunique()),'note':'Theo ngày của snapshot (UTC+7)'},
            {'label':'Tổng bản ghi','value':fmt.num(len(b)),'note':'Trong file snapshot'},
            {'label':'Số mã','value':fmt.num(b['symbol'].nunique()),'note':'Được theo dõi'},
            {'label':'Khoảng thời gian','value':fmt.num(duration.total_seconds()/3600,1)+' giờ','note':'Dữ liệu đã ghi'}
        ]),unsafe_allow_html=True)

    with st.expander('Danh mục cổ phiếu',expanded=False):
        catalog_raw,_=_market_parquet(root,'data/processed/ssi_securities.parquet')
        if catalog_raw is None:st.info('Chưa có danh mục SSI.')
        else:
            catalog=equity_catalog(catalog_raw)
            q=st.text_input('Tìm mã hoặc tên',key='ep_catalog_query')
            boards=st.multiselect('Sàn',sorted(catalog.board.unique()),default=sorted(catalog.board.unique()),key='ep_catalog_boards')
            simple=stock_catalog(catalog,equity_only=False)
            simple=simple[simple.board.isin(boards)]
            matches=search_stocks(simple,q,limit=len(simple))
            shown=catalog[catalog.symbol.isin(matches.symbol)].copy().sort_values('symbol')
            cols={'symbol':'Mã','board':'Sàn','name':'Tên doanh nghiệp','icbName':'Ngành','lotSize':'Lô giao dịch'}
            paged_table(shown[[k for k in cols if k in shown]].rename(columns=cols),'ep_catalog_page')
            st.download_button('Tải danh mục CSV',fmt.csv_bom(shown),'ExitPlan_catalog.csv','text/csv')
    with st.expander('Hướng dẫn kỹ thuật',expanded=False):
        st.code('py scripts/ssi_v3_sync.py --check\\npy scripts/ssi_v3_sync.py --catalog',language='powershell')
        st.caption('Xem README và docs/SSI_FASTCONNECT_SETUP.md. Không nhập khóa API vào dashboard.')
    st.subheader('Chất lượng dữ liệu')
    if data.get('use_ssi'):
        report=Path(root)/'outputs/tables/ssi_ws_quality.json'
        if report.is_file():
            qa=json.loads(report.read_text(encoding='utf-8'))
            st.markdown(cards_html([
              {'label':'Bản tin đầu vào','value':fmt.num(qa.get('input'))},
              {'label':'Nhóm đồng bộ','value':fmt.num(qa.get('aligned_snapshots'))},
              {'label':'Quote lỗi','value':fmt.num(qa.get('invalid_quote',0))},
              {'label':'Trade lỗi','value':fmt.num(qa.get('invalid_trade',0))}
            ]),unsafe_allow_html=True)
            st.caption('Thống kê thực tế của importer SSI; thiếu nhóm đồng bộ không phải lệnh không khớp.')
            with st.expander('Chi tiết kiểm tra SSI'):
                st.json(qa)
        else:st.info('Chưa có báo cáo chất lượng SSI.')
    quality=data['quality']
    if quality is None or quality.empty:
        if not data.get('use_ssi'):st.info('Chưa có file chất lượng dữ liệu. Vui lòng chạy pipeline trước.')
    else:
        source=', '.join(sorted(map(str,quality['data_kind'].dropna().unique()))) if 'data_kind' in quality.columns else 'Chưa xác định'
        count_col=next((c for c in ('records','rows','n_records','total_records','count') if c in quality.columns),None)
        missing_cols=[c for c in quality.columns if c.startswith('missing_') and not c.endswith('_pct')]
        duplicates_cols=[c for c in ('duplicates','invalid_rows','invalid') if c in quality.columns]
        total=lambda cols: sum(pd.to_numeric(quality[c],errors='coerce').fillna(0).sum() for c in cols)
        nr=pd.to_numeric(quality[count_col],errors='coerce').fillna(0).sum() if count_col else None
        missing=total(missing_cols)
        invalid=total(duplicates_cols)
        st.markdown(cards_html([
            {'label':'Tổng bản ghi','value':fmt.num(nr) if nr is not None else '–','note':'Theo bảng kiểm tra'},
            {'label':'Mã chứng khoán','value':fmt.num(quality['symbol'].nunique()) if 'symbol' in quality else '–','note':'Được kiểm tra'},
            {'label':'Giá trị thiếu','value':fmt.num(missing) if missing_cols else '–','note':'Các trường dữ liệu nguồn'},
            {'label':'Lỗi & trùng lặp','value':fmt.num(invalid) if duplicates_cols else '–','note':'Cần đối chiếu khi khác 0'}
        ]),unsafe_allow_html=True)
        cols=[c for c in ('symbol',count_col,'missing_bid','duplicates','invalid_rows') if c and c in quality]
        cols=list(dict.fromkeys(cols))
        vn={'symbol':'Mã cổ phiếu','records':'Bản ghi','missing_bid':'Thiếu giá mua',
            'duplicates':'Trùng lặp','invalid_rows':'Bản ghi lỗi','rows':'Bản ghi',
            'n_records':'Bản ghi','total_records':'Bản ghi','count':'Bản ghi'}
        if cols:
            rows=[]
            for _,r in quality.iterrows():
                values=[]
                for c in cols:
                    v=r[c]
                    values.append('–' if pd.isna(v) else str(v) if c=='symbol' else fmt.num(v))
                good=all(pd.to_numeric(pd.Series([r.get(c,0)]),errors='coerce').fillna(0).iloc[0]==0 for c in ('missing_bid','duplicates','invalid_rows'))
                rows.append(values+['Đạt' if good else 'Cần kiểm tra'])
            st.markdown(
                '<div class="ep-panel"><div class="ep-panel-title">Chi tiết theo mã cổ phiếu</div>'
                '<div class="ep-panel-desc">Đối chiếu số bản ghi, dữ liệu thiếu và lỗi theo từng mã.</div>'
                +html_table([vn.get(c,c) for c in cols]+['Đánh giá'],rows,
                    numeric=tuple(i for i,c in enumerate(cols) if c!='symbol'),
                    pills={len(cols):{'Đạt':'ok','Cần kiểm tra':'warn'}})
                +'</div>',
                unsafe_allow_html=True,
            )
        if 'synthetic' in source.lower():
            st.warning('Dữ liệu GIẢ LẬP (synthetic) — không phải dữ liệu thị trường SSI thật.')
        st.caption('Nguồn dữ liệu: '+source)
        with st.expander('Chi tiết kỹ thuật · Dữ liệu gốc',expanded=False):
            paged_table(quality,'ep_quality_raw_page')

    st.subheader('Trạng thái kết nối dữ liệu')
    st.caption('Tự kết nối trong khung thu thập; ngoài giờ lấy giá đóng cửa cho mã đang xem. Trạng thái trực tiếp ở thanh bên. Không chạy thêm bộ ghi terminal cùng lúc.')
    ssi_status=Path(root)/'outputs/tables/ssi_recorder_status.json'
    status_file=ssi_status if ssi_status.is_file() or data.get('use_ssi') else Path(root)/'outputs/tables/recorder_status.json'
    if status_file.exists():
        try:
            status=json.loads(status_file.read_text(encoding='utf-8'))
            if not isinstance(status,dict):raise ValueError('Trạng thái phải là đối tượng JSON')
            kind=str(status.get('data_kind','unknown'))
            state=str(status.get('state',status.get('status','unknown')))
            state_labels={'connecting':'Đang kết nối','connected_unverified_auth':'Socket đã mở','subscribed_no_data':'Đăng ký thành công · chưa có dữ liệu','receiving_stockinfo':'Đã nhận dữ liệu tại lần cập nhật','stopped':'Đã dừng · có bản tin','stopped_no_data':'Đã dừng · chưa có bản tin','connected':'Đã mở socket','recording':'Đã ghi dữ liệu tại lần cập nhật','error':'Lỗi kết nối'}
            status_label='Giả lập' if kind=='synthetic' else state_labels.get(state,'Chưa xác nhận')
            updated=str(status.get('last_update_vn',status.get('updated_at',status.get('timestamp','–'))))
            channel=str(status.get('channel','–'))
            records=status.get('records')
            display_time=updated.replace('T',' ')[:25] if updated!='–' else updated
            info=[
                ('Nguồn dữ liệu','Giả lập (synthetic)' if kind=='synthetic' else kind),
                ('Kênh ghi nhận',channel),
                ('Cập nhật gần nhất',display_time),
                ('Số bản ghi',fmt.num(records) if records is not None else '–'),
            ]
            info_html=''.join(
                '<div class="ep-info-row"><span class="ep-info-key">'+escape(k)+'</span>'
                '<span class="ep-info-val">'+escape(str(v))+'</span></div>' for k,v in info
            )
            st.markdown(
                '<div class="ep-panel"><div class="ep-panel-title">Bộ thu thập dữ liệu thị trường'
                ' <span class="ep-pill '+('warn' if kind=='synthetic' else 'ok' if state in ('connected','recording') else 'neutral')+'">'
                +escape(status_label)+'</span></div>'
                '<div class="ep-panel-desc">Nhật ký bộ ghi dòng lệnh; kết nối từ dashboard có trạng thái riêng tại thanh bên.</div>'
                +info_html+'</div>',
                unsafe_allow_html=True,
            )
            if kind=='synthetic':st.warning('Bộ ghi chỉ đang mô phỏng. Chưa có kết nối WebSocket thật.')
            with st.expander('Chi tiết kỹ thuật · Nhật ký JSON',expanded=False):
                st.code(json.dumps(status,ensure_ascii=False,indent=2),language='json')
        except (OSError,ValueError) as ex:
            st.error(f'Tệp trạng thái không hợp lệ: {ex}')
    else:
        st.info('Chưa có file trạng thái bộ ghi dòng lệnh. Có thể kết nối SSI tại thanh bên.')
    st.caption('Múi giờ Asia/Ho_Chi_Minh (UTC+7); dashboard hỗ trợ bộ thu thập SSI độc lập, hoặc đọc dữ liệu đã lưu.')


def validation(root,data,t):
    source_labels(data)
    folder=Path(root)/'outputs/tables'
    files=sorted(folder.glob('validation_*_ssi.csv')) if data.get('use_ssi') else sorted(f for f in folder.glob('validation_*.csv') if not f.stem.endswith('_ssi'))
    if not files:
        st.warning('Chưa có dữ liệu: cần file outputs/tables/validation_*.csv')
        return
    st.markdown('**Bảng kiểm chứng**')
    filenames=[f.name for f in files]
    choice_key='ep_validation_choice'
    if st.session_state.get(choice_key) not in filenames:
        st.session_state[choice_key]=filenames[0]
    if len(filenames)<=3:
        # Với ít bảng kiểm chứng, dùng nút chọn thay cho native dropdown
        # (dropdown portal của Streamlit không đồng bộ dark mode).
        label_map={
            'validation_replay.csv':'Phát lại dữ liệu',
            'validation_replay_ssi.csv':'Phát lại dữ liệu SSI',
            'validation_sensitivity.csv':'Độ nhạy tham số',
        }
        buttons=st.columns(len(filenames),gap='small')
        for col,filename in zip(buttons,filenames):
            with col:
                if st.button(label_map.get(filename,filename.replace('validation_','').replace('.csv','')),
                             key='ep_validation_'+filename,
                             type='primary' if st.session_state[choice_key]==filename else 'secondary',
                             use_container_width=True):
                    st.session_state[choice_key]=filename
        selections=st.session_state[choice_key]
        st.caption('Đang xem: '+selections)
    else:
        selections=st.selectbox('Chọn tệp kiểm chứng',filenames,
                                index=filenames.index(st.session_state[choice_key]))
        st.session_state[choice_key]=selections
    try:
        df=pd.read_csv(folder/selections)
        if 'data_kind' in df and (df['data_kind']=='synthetic').any():st.warning('⚠️ Bảng kiểm chứng GIẢ LẬP: chưa thể dùng làm bằng chứng ngoài mẫu.')
        st.markdown(frame_table(df,max_rows=80),unsafe_allow_html=True)
        if {'variable','value','net'}.issubset(df.columns):
            st.subheader('Độ nhạy tham số (đã tính và lưu)')
            plot(charts.sensitivity_fig(df,t),'EP06_sensitivity')
        elif {'snapshot_ts','plan_id','net','hhi'}.issubset(df.columns):
            st.subheader('Phát lại nhiều ảnh chụp')
            x=df.copy(); x['snapshot_ts']=pd.to_datetime(x['snapshot_ts'],errors='coerce')
            plot(charts.time_fig(x.rename(columns={'snapshot_ts':'ts_vn','plan_id':'symbol','net':'closePrice'}),t),'EP07_replay')
        else:st.caption('Không có dữ liệu phù hợp để tạo biểu đồ từ bảng này; chỉ hiển thị giá trị được lưu.')
    except Exception as ex:st.error(f'Không đọc được {selections}: {ex}')
    st.caption('Kết quả kiểm chứng cần dùng dữ liệu thật và công bố mẫu/tần suất trước khi kết luận mô hình ổn định.')
    st.subheader('Kiểm thử tự động')
    path=folder/'test_results.csv'
    if path.exists():
        st.markdown(frame_table(pd.read_csv(path),max_rows=80),unsafe_allow_html=True)
    else:st.info('Chưa có dữ liệu: cần file outputs/tables/test_results.csv sau khi chạy pytest.')


def methods(root,data,t):
    source_labels(data)
    config_path=Path(root)/'config.json'
    try:
        config=json.loads(config_path.read_text(encoding='utf-8'))
        if not isinstance(config,dict):
            raise ValueError('Cấu hình phải là đối tượng JSON')
    except (OSError,ValueError) as ex:
        st.warning(f'Không đọc được config.json: {ex}')
        config={}

    definitions=[
        ('01 · Dữ liệu','ExitPlan phân tích ảnh chụp sổ lệnh đã lưu. Dữ liệu SSI lịch sử (nếu có) dùng để tính ADV và nghiên cứu biến động; dữ liệu giả lập luôn được gắn nhãn riêng.'),
        ('02 · Mô hình chi phí','Doanh thu = Σ số cổ phiếu bán × giá mua tại từng mức. Tiền ròng = doanh thu − phí − thuế giả định. Chi phí thanh khoản = max(0; giá gần nhất × lượng được bao phủ − doanh thu).'),
        ('03 · Bài toán tối ưu','MILP chọn số lô cổ phiếu từ từng mã, không vượt lượng nắm giữ và độ sâu quan sát. A giảm chi phí; B đánh đổi chi phí với proxy tập trung; C giảm proxy tập trung; P gần tỷ trọng bán theo giá trị.'),
        ('04 · Giới hạn','Không có toàn bộ sổ lệnh hoặc diễn biến sau khi đặt lệnh; không chứng minh khả năng khớp. HHI được tính sau tối ưu, còn mục tiêu tập trung trong MILP sử dụng proxy bình phương giá trị còn lại.')
    ]
    # Một khối HTML grid để có khoảng cách dọc/ngang nhất quán trên mọi màn hình.
    method_cards=''.join(
        '<article class="ep-method"><h3>'+escape(title)+'</h3>'
        '<p>'+escape(body)+'</p></article>'
        for title,body in definitions
    )
    st.markdown('<div class="ep-method-grid">'+method_cards+'</div>',unsafe_allow_html=True)

    st.subheader('Thiết lập & giới hạn mô hình')
    st.caption('Thông số vận hành được lưu trong file cấu hình để tái lập kết quả; không phải báo giá hay dữ liệu thị trường trực tiếp.')

    if config:
        def show_number(key,suffix='',digits=0):
            v=config.get(key)
            return fmt.num(v,digits)+suffix if isinstance(v,(int,float)) and not isinstance(v,bool) else 'Chưa thiết lập'

        st.markdown(cards_html([
            {'label':'Quy mô lô giao dịch','value':show_number('lot_size',' CP'),'note':'Số cổ phiếu trong một lô'},
            {'label':'Độ sâu sổ lệnh','value':show_number('observed_book_levels',' mức'),'note':'Số mức giá mua dùng để phân tích'},
            {'label':'Số mã tối đa','value':show_number('maximum_assets_mvp',' mã'),'note':'Giới hạn khai báo cho phiên bản MVP'},
            {'label':'Ngưỡng tham gia ADV','value':show_number('participation_threshold_pct_default','%'),'note':'Ngưỡng cảnh báo mặc định'}
        ]),unsafe_allow_html=True)

        def setting_row(label,key,description,percent=False):
            v=config.get(key)
            defined=isinstance(v,(int,float)) and not isinstance(v,bool)
            value=(fmt.pct(v) if percent else fmt.num(v,4)) if defined else 'Chưa thiết lập'
            klass='ok' if defined else 'warn'
            return (
                '<div class="ep-setting-row">'
                '<div><div class="ep-setting-name">'+escape(label)+'</div>'
                '<div class="ep-setting-description">'+escape(description)+'</div></div>'
                '<span class="ep-pill '+klass+'">'+escape(value)+'</span></div>'
            )

        st.markdown(
            '<div class="ep-panel">'
            '<div class="ep-panel-title">Các giả định chi phí</div>'
            '<div class="ep-panel-desc">Các giá trị trống không đồng nghĩa với chi phí bằng 0. Cần xác nhận trước khi đánh giá phương án bằng dữ liệu thật.</div>'
            + setting_row('Phí giao dịch','fee_rate_default','Tỷ lệ phí bán mặc định',percent=True)
            + setting_row('Thuế giao dịch','tax_rate_default','Tỷ lệ thuế/chi phí thuế mặc định',percent=True)
            + setting_row('Hệ số tác động giá','impact_coefficient','Tham số ước lượng market impact (nếu dùng)')
            +'</div>',
            unsafe_allow_html=True
        )
        timezone=config.get('timezone')
        source=config.get('data_source')
        st.markdown(
            '<div class="ep-panel"><div class="ep-panel-title">Thông tin nguồn & thời gian</div>'
            '<div class="ep-info-row"><span class="ep-info-key">Múi giờ</span><span class="ep-info-val">'
            +escape(str(timezone) if timezone else 'Chưa xác định')+'</span></div>'
            '<div class="ep-info-row"><span class="ep-info-key">Nguồn khai báo trong cấu hình</span><span class="ep-info-val">'
            +escape(str(source) if source else 'Chưa xác định')+'</span></div>'
            '</div>',
            unsafe_allow_html=True
        )
        st.info('SSI REST đã được kiểm tra trên tài khoản người dùng; kết quả sổ lệnh chỉ dùng file SSI được chuẩn hóa. Dữ liệu đã ghi không đồng nghĩa đang kết nối trực tuyến.')
    else:
        st.info('Chưa có thông số để hiển thị. Kiểm tra file config.json.')

    st.warning('Ứng dụng không đặt lệnh thật và không đưa ra khuyến nghị đầu tư. Chi phí và khả năng khớp chỉ là ước tính theo dữ liệu sổ lệnh được cung cấp.')


def downloads(root,data,t,show_source=True,include_liquidity=True):
    if show_source:source_labels(data)
    plans=st.session_state.get('ep_plans')
    if plans:
        summary=summaries(plans)
        params=st.session_state.get('ep_params',{})
        meta={'data_kind':params.get('data_kind'),'snapshot_at':params.get('snapshot_at'),'source':'ssi_fastconnect_v3_ws' if data.get('use_ssi') else 'saved_book','target_net':params.get('target'),'fee_rate':params.get('fee'),'tax_rate':params.get('tax'),'lambda_weight':params.get('lamb')}
        summary=summary.assign(**meta)
        st.download_button('⬇️ Tải bảng so sánh phương án',fmt.csv_bom(summary),'ExitPlan_plans.csv','text/csv',use_container_width=True)
        details=pd.DataFrame([dict(plan=k,**d) for k,p in plans.items() for d in p['details']]).assign(**meta)
        st.download_button('⬇️ Tải chi tiết lượng bán',fmt.csv_bom(details),'ExitPlan_plan_details.csv','text/csv',use_container_width=True)
        fr=st.session_state.get('ep_frontier')
        if fr is not None:st.download_button('⬇️ Tải đường đánh đổi',fmt.csv_bom(fr.assign(**meta)),'ExitPlan_frontier.csv','text/csv',use_container_width=True)
    else:st.info('Chưa có bảng phương án hiện tại. Bấm “Tính phương án” để tạo.')
    if include_liquidity:
        if data['liquidity'] is not None:
            st.download_button('⬇️ Tải bảng thanh khoản đã lưu',fmt.csv_bom(data['liquidity']),'ExitPlan_liquidity.csv','text/csv',use_container_width=True)
        else:st.warning('Chưa có dữ liệu: cần file '+LIQUIDITY)
    st.caption('Mỗi CSV dùng UTF-8 có BOM để Excel nhận tiếng Việt. Không tự tạo hoặc điều chỉnh dữ liệu nguồn.')

FUNCTIONS={'overview':overview,'planner':planner,'compare':compare,'liquidity':liquidity,
           'data':data_page,'ssi_history':ssi_history,'validation':validation,'methods':methods,'downloads':downloads}

def render_page(page,root,cfg):
    page_header(page,cfg['accent'],cfg['mode'])
    t=charts.apply_palette(cfg['mode'],cfg['accent'])
    try:
        if page=='overview' and str(st.query_params.get('advanced',''))!='1':
            # Refresh even when the app is opened before the session starts.
            # The planner's editable widgets are never rerun by this timer.
            interval=15
            @st.fragment(run_every=interval)
            def refresh_overview():
                overview(root,load(root),t)
            refresh_overview()
        else:
            FUNCTIONS[page](root,load(root),t)
    except Exception as ex:
        if page=='planner':
            import logging
            logging.getLogger(__name__).exception('Lỗi giao diện lập phương án')
            st.error('Trang chưa thể hiển thị. Kiểm tra dữ liệu trong Thông tin & hỗ trợ.',icon=':material/error:')
        else:
            st.error(f'Không thể hiển thị trang: {type(ex).__name__}: {ex}')
            st.caption('Không dùng dữ liệu giả định để thay cho dữ liệu đang thiếu. Hãy kiểm tra file đầu vào và schema.')
