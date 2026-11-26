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
from src.analytics.planner import calculate,summaries,frontier

NAV={
 'overview':'🏠  Tổng quan',
 'planner':'🧮  Lập phương án',
 'compare':'⚖️  So sánh phương án',
 'liquidity':'📊  Thanh khoản các mã',
 'data':'🗄️  Dữ liệu & kết nối',
 'ssi_history':'📈  SSI · Dữ liệu lịch sử',
 'validation':'✅  Kiểm chứng',
 'methods':'📖  Phương pháp & giới hạn',
 'downloads':'📥  Tải dữ liệu',
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
 'planner':('SMART EXIT PLANNER','Lập phương án thanh lý','Thiết lập mục tiêu tiền ròng và cân bằng chi phí thanh khoản với mức tập trung còn lại.'),
 'compare':('DECISION ANALYTICS','So sánh phương án','So sánh A, B, C và mốc bán tỷ trọng; chỉ báo cáo dựa trên ảnh chụp có sổ lệnh hợp lệ.'),
 'liquidity':('MARKET MICROSTRUCTURE','Thanh khoản các mã','Độ sâu ba mức giá mua, chênh lệch mua–bán và giới hạn khối lượng quan sát.'),
 'data':('DATA OPERATIONS','Dữ liệu & kết nối','Tình trạng file, thời gian, chất lượng dữ liệu và nhật ký bộ ghi thị trường.'),
 'ssi_history':('SSI FASTCONNECT · MARKET DATA','Dữ liệu lịch sử SSI','Giá, khối lượng, ADV từ SSI V3 khi có quyền Market Data; tách biệt dữ liệu sổ lệnh WebSocket.'),
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
    html=(
        '<div class="ep-hero"><div class="ep-hero-heading"><span class="ep-hero-icon">'+icon+'</span>'
        '<div><div class="ep-eyebrow">'+escape(eye)+'</div><h1>'+escape(title)+'</h1></div></div>'
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


def load(root):
    overrides={}
    if str(st.query_params.get('advanced',''))=='1':
        with st.sidebar.expander('Nâng cao · đường dẫn file',expanded=False):
            for relative in [SNAPSHOT,LIQUIDITY,PLANS,FRONTIER,QUALITY]:
                value=st.text_input(relative,value=str(Path(root)/relative),key='path_'+relative)
                overrides[relative]=value
    ssi_path='data/processed/ssi_book_snapshots.parquet'
    use_ssi=SNAPSHOT not in overrides and (Path(root)/ssi_path).is_file()
    raw,err=read_parquet(root,ssi_path if use_ssi else SNAPSHOT,overrides)
    books=None
    if raw is not None:
        try:
            books=normalize_book(raw)
            if use_ssi and (books.empty or 'source' not in books or
                set(books['source'])!={'ssi_fastconnect_v3_ws'} or set(books['data_kind'])!={'live'}):
                raise ValueError('File SSI không đúng nguồn hoặc trống')
        except Exception as exc:
            books=None
            err=f'Dữ liệu không hợp lệ: {exc}'
    liquidity,liquidity_err=read_parquet(root,LIQUIDITY,overrides)
    saved_plans,_=read_parquet(root,PLANS,overrides)
    saved_frontier,_=read_parquet(root,FRONTIER,overrides)
    quality,_=read_csv(root,QUALITY,overrides)
    if use_ssi:
        # Never reuse synthetic quality or liquidity with actual SSI snapshots.
        quality=None
        saved_plans=saved_frontier=None
        liquidity=None
        liquidity_err=None
        if books is not None and not books.empty:
            try:
                from src.analytics.ssi_history_stats import asof_history_stats
                history,herr=read_parquet(root,'data/processed/ssi_history.parquet')
                if history is None:raise ValueError(herr)
                factors=books['history_volume_factor'].dropna().unique()
                if len(factors)!=1 or not 0<float(factors[0])<float('inf'):
                    raise ValueError('Chưa xác nhận đơn vị volume lịch sử')
                liquidity=asof_history_stats(history,books['ts_vn'].max().date())
                liquidity['adv']*=float(factors[0])
                liquidity['volume_note']='OHLCV SSI trước ngày snapshot · CP/ngày'
            except Exception as ex:liquidity_err=str(ex)
    # Clear computed plans when the source or latest input snapshot changes.
    signature=(ssi_path if use_ssi else str(overrides.get(SNAPSHOT,SNAPSHOT)),
               str(books['ts_vn'].max()) if books is not None and not books.empty else '',
               tuple(sorted(books['data_kind'].unique())) if books is not None else (),
               len(books) if books is not None else 0)
    if st.session_state.get('ep_data_signature')!=signature:
        for key in ('ep_plans','ep_frontier','ep_holdings','ep_plan_quotes','ep_params'):
            st.session_state.pop(key,None)
        st.session_state['ep_data_signature']=signature
    return dict(use_ssi=use_ssi,books=books,err=err,liquidity=liquidity,liquidity_err=liquidity_err,
                saved_plans=saved_plans,saved_frontier=saved_frontier,quality=quality,overrides=overrides)

def source_labels(data):
    books=data['books']
    if books is None or books.empty:
        st.warning(data['err'] or f'Chưa có dữ liệu: cần file {SNAPSHOT}')
        return False
    kinds=sorted(set(books['data_kind']))
    if len(kinds)>1:
        st.error('Tồn tại dữ liệu trộn nguồn live/lịch sử/giả lập. Chọn một nguồn riêng trước khi tính; hệ thống không tự trộn.')
        return False
    kind=kinds[0]
    if kind=='synthetic':st.warning('⚠️ DỮ LIỆU GIẢ LẬP (synthetic) — Không phải báo giá thị trường thật.')
    last=books['ts_vn'].max()
    label='SSI FastConnect V3 · snapshot đã ghi' if data.get('use_ssi') else KIND_LABELS.get(kind,kind)
    st.markdown(badge('Nguồn: '+label,kind)+badge('Cập nhật: '+last.strftime('%d/%m/%Y %H:%M:%S')+' · UTC+7')+
                badge('File đã ghi · không kết nối API trong dashboard'),unsafe_allow_html=True)
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

def overview(root,data,t):
    if not source_labels(data):
        # Khi dữ liệu thiếu, hiện trạng thái thật thay vì vẽ số liệu/bảng giả.
        st.markdown(cards_html([
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
    b=data['books']; latest=latest_books(b); symbols=available_symbols(b)
    plans=st.session_state.get('ep_plans')
    last=b['ts_vn'].max(); sessions=int(b['ts_vn'].dt.date.nunique())
    cards=[{'label':'Mã có sổ lệnh hợp lệ','value':fmt.num(len(symbols)),'note':'Chỉ đếm mã có ít nhất một bid số hợp lệ'},
           {'label':'Phiên dữ liệu đã lưu','value':fmt.num(sessions),'note':'Phiên tính từ ts_vn'},
           {'label':'Bản ghi snapshot','value':fmt.num(len(b)),'note':'Không tự thay dữ liệu trống'},
           {'label':'Tiền ròng phương án B','value':fmt.vnd_big(plans['B']['net']) if plans else 'Chờ',
            'note':'Bấm “Tính phương án” để có kết quả' if not plans else 'Dựa trên dữ liệu và danh mục khi tính'}]
    st.markdown(cards_html(cards),unsafe_allow_html=True)
    a,c=st.columns([1.65,1])
    with a:
        st.subheader('Diễn biến giá chuẩn hóa (gốc = 100)')
        shown=st.multiselect('Mã hiển thị',symbols,default=symbols[:5],max_selections=12,key='ep_overview_symbols')
        if shown:plot(charts.time_fig(b[b.symbol.isin(shown)],t,normalize=True),'EP01_price')
        st.markdown(guide('Mỗi mã được quy về 100 ở quan sát đầu tiên để dễ so sánh biến động tương đối.',
            'Dữ liệu chỉ phản ánh các bản ghi đã lưu, không phải lịch sử giá được API cấp tự động.'),unsafe_allow_html=True)
    with c:
        st.subheader('Trạng thái nguồn dữ liệu')
        status='Đã đọc file dữ liệu'
        st.metric('Trạng thái dashboard',status)
        st.metric('Thời điểm mới nhất',last.strftime('%d/%m/%Y %H:%M'))
        st.metric('Số mã có thể lập phương án',fmt.num(len(symbols)))
        st.caption('File đã lưu không xác nhận WebSocket đang kết nối. Xem trạng thái bộ ghi tại trang Dữ liệu & kết nối.')


def _clear_plan():
    for key in ('ep_plans','ep_frontier','ep_holdings','ep_plan_quotes','ep_params'):
        st.session_state.pop(key,None)


def _change_quantity(symbol):
    draft=dict(st.session_state.get('ep_draft_holdings',{}))
    draft[symbol]=int(st.session_state['ep_qty_'+symbol])
    st.session_state['ep_draft_holdings']=draft
    _clear_plan()


def _change_setting(name):
    settings=dict(st.session_state.get('ep_draft_settings',{}))
    settings[name]=st.session_state['ep_setting_'+name]
    st.session_state['ep_draft_settings']=settings
    _clear_plan()


def planner(root,data,t):
    valid_source=source_labels(data)
    books=data['books'] if valid_source else None
    raw,catalog_err=read_parquet(root,'data/processed/ssi_securities.parquet')
    try:
        catalog=stock_catalog(raw,books)
    except ValueError as ex:
        st.warning(str(ex))
        catalog=stock_catalog(None,books)
    if raw is None:
        st.caption('Chưa có danh mục SSI đã lưu; hiện chỉ tra cứu mã trong file sổ lệnh. '+str(catalog_err or ''))
    valid_symbols=set(available_symbols(books)) if books is not None else set()
    kind=str(books['data_kind'].iloc[0]) if books is not None else ''
    # Real daily bars are displayed only as independent history coverage, never as depth.
    history,_=read_parquet(root,'data/processed/ssi_history.parquet')
    history_counts={}
    if history is not None and {'symbol','tradingDate','source','data_kind'}.issubset(history.columns):
        if set(history.source)=={'ssi_fastconnect_v3'} and set(history.data_kind)=={'historical'}:
            history_counts=history.groupby('symbol')['tradingDate'].nunique().to_dict()
    if 'ep_draft_holdings' not in st.session_state:
        st.session_state['ep_draft_holdings']={}
    draft=st.session_state['ep_draft_holdings']
    st.subheader('1. Tìm kiếm cổ phiếu')
    st.caption(f'{len(catalog):,} mã tra cứu · {len(valid_symbols):,} mã có sổ lệnh trong nguồn đang chọn. Danh sách SSI có thể gồm chứng khoán khác cổ phiếu phổ thông.')
    search_col,board_col=st.columns([3,1])
    with search_col:
        query=st.text_input('Tìm theo mã hoặc tên doanh nghiệp',placeholder='Ví dụ: HPG, Hòa Phát, ngân hàng…',key='ep_stock_query')
    with board_col:
        board=st.selectbox('Sàn giao dịch',['Tất cả']+sorted(catalog.board.unique()),key='ep_stock_board')
    matches=search_stocks(catalog,query,board,exclude=draft,limit=30)
    if matches.empty:
        st.info('Không có mã phù hợp chưa được thêm. Thử tên/mã khác hoặc đổi sàn.')
    else:
        names={r.symbol:f"{r.symbol} · {r.name or 'Chưa có tên'} · {r.board}" for r in matches.itertuples()}
        pick_col,add_col=st.columns([4,1])
        with pick_col:
            selected=st.selectbox('Kết quả tìm kiếm',list(names),index=None,
                 format_func=names.get,placeholder='Chọn mã cần thêm',key='ep_stock_pick')
        with add_col:
            st.caption('Thêm vào danh mục')
            add=st.button('Thêm mã',key='ep_stock_add',icon=':material/add:',
                          use_container_width=True,disabled=selected is None or len(draft)>=12)
        if add and selected not in draft and len(draft)<12:
            st.session_state['ep_draft_holdings']={**draft,selected:0}
            st.session_state.pop('ep_qty_'+selected,None)
            _clear_plan()
            st.rerun()
        st.caption('Hiển thị tối đa 30 kết quả; nhập mã/tên cụ thể để tìm nhanh. Tìm kiếm không phụ thuộc việc mã đã có sổ lệnh.')
    st.divider()
    st.subheader(f'2. Danh mục của tôi · {len(draft)}/12 mã')
    st.caption('Nhập số lượng cổ phiếu thực tế đang nắm giữ. Chỉ mô phỏng cổ phiếu phổ thông lô 100; không đọc tài khoản và không đặt lệnh.')
    if not draft:
        st.info('Danh mục đang trống. Hãy tìm và thêm cổ phiếu ở phía trên.')
    meta=catalog.set_index('symbol').to_dict('index')
    nonstandard=known_nonstandard_lots(catalog,draft)
    unknown=set(draft)-set(meta)
    if draft:
        header=st.columns([3,2,3,1])
        for col,label in zip(header,['Cổ phiếu','Nắm giữ (CP)','Dữ liệu đã lưu','Xóa']):
            col.caption(label)
        for sym,qty in list(draft.items()):
            a,b,d,e=st.columns([3,2,3,1],vertical_alignment='center')
            info=meta.get(sym,{})
            with a:
                st.markdown('**'+escape(sym)+'**')
                st.caption((info.get('name') or 'Chưa có tên')+' · '+(info.get('board') or 'Chưa rõ sàn'))
            with b:
                st.number_input('Số lượng '+sym,min_value=0,value=int(qty),step=100,
                    key='ep_qty_'+sym,label_visibility='collapsed',on_change=_change_quantity,args=(sym,))
            with d:
                if sym in nonstandard:
                    st.caption('Không hỗ trợ lô giao dịch khác 100')
                elif sym in valid_symbols:
                    st.caption('Có sổ lệnh giả lập' if kind=='synthetic' else 'Có sổ lệnh đã lưu')
                else:
                    st.caption('Chưa có sổ lệnh hợp lệ')
                n=history_counts.get(sym,0)
                st.caption(f'SSI OHLCV: {n} phiên đã lưu' if n else 'SSI OHLCV: chưa có')
            with e:
                if st.button('Xóa',key='ep_remove_'+sym,icon=':material/close:',
                             help='Xóa '+sym,use_container_width=True):
                    st.session_state['ep_draft_holdings']={s:v for s,v in draft.items() if s!=sym}
                    st.session_state.pop('ep_qty_'+sym,None)
                    _clear_plan()
                    st.rerun()
        if st.button('Xóa toàn bộ danh mục',key='ep_clear_draft'):
            st.session_state['ep_draft_holdings']={}
            for sym in draft:st.session_state.pop('ep_qty_'+sym,None)
            _clear_plan()
            st.rerun()
    st.divider()
    st.subheader('3. Mục tiêu và điều kiện thanh lý')
    settings=st.session_state.setdefault('ep_draft_settings',dict(target=100.,lamb=.5,fee=0.,tax=0.))
    c1,c2=st.columns(2)
    with c1:
        target=st.number_input('Tiền RÒNG cần thu (triệu đồng)',min_value=.1,value=float(settings['target']),step=5.,
            key='ep_setting_target',on_change=_change_setting,args=('target',))
        lamb=st.slider('Ưu tiên λ · 0 = chi phí / 1 = tập trung',0.,1.,float(settings['lamb']),.05,
            key='ep_setting_lamb',on_change=_change_setting,args=('lamb',))
    with c2:
        fee=st.number_input('Phí bán giả định (%)',0.,5.,float(settings['fee']),.05,
            key='ep_setting_fee',on_change=_change_setting,args=('fee',))
        tax=st.number_input('Thuế/chi phí khác giả định (%)',0.,5.,float(settings['tax']),.05,
            key='ep_setting_tax',on_change=_change_setting,args=('tax',))
        st.caption('Phí và thuế là giả định người dùng nhập; mặc định 0%, cần điều chỉnh phù hợp.')
    missing=sorted(set(draft)-valid_symbols)
    zeros=sorted(s for s,v in draft.items() if v<=0)
    batch=None
    if draft:
        if missing:st.warning('Thiếu sổ lệnh hợp lệ: '+', '.join(missing)+'. Cần thu thập dữ liệu trước khi tính; OHLCV không thay cho sổ lệnh.')
        if zeros:st.info('Nhập số lượng nắm giữ lớn hơn 0 cho: '+', '.join(zeros))
        if nonstandard:st.warning('Không hỗ trợ lô giao dịch khác 100: '+', '.join(nonstandard))
        if unknown:st.warning('Mã không còn trong danh sách tra cứu: '+', '.join(sorted(unknown)))
        if not missing and not nonstandard and not unknown:
            try:
                batch=portfolio_snapshot(books,draft)
                if 'lotSize' in batch and (pd.to_numeric(batch['lotSize'],errors='coerce').dropna()!=100).any():
                    raise ValueError('Danh mục chứa mã có lô giao dịch khác 100')
                # Validate quote structure before enabling calculation.
                for _,row in batch.iterrows():quote_from_row(row)
                stamp=batch['ts_vn'].max()
                st.caption('Snapshot chung gần nhất của danh mục: '+stamp.strftime('%d/%m/%Y %H:%M:%S')+' · UTC+7 (dữ liệu đã ghi, không phải báo giá trực tiếp).')
            except (ValueError,RuntimeError,KeyError,TypeError) as ex:
                batch=None
                st.warning(str(ex))
    demo_ok=True
    if kind=='synthetic':
        demo_ok=st.checkbox('Cho phép tính thử bằng dữ liệu GIẢ LẬP',key='ep_demo_opt_in',on_change=_clear_plan)
    ready=bool(draft) and batch is not None and not zeros and demo_ok
    run=st.button('Tính phương án',icon=':material/calculate:',type='primary',
                  use_container_width=True,disabled=not ready,key='ep_calculate_plan')
    if run and ready:
        _clear_plan()
        try:
            holdings=dict(draft)
            quotes={r['symbol']:quote_from_row(r) for _,r in batch.iterrows()}
            with st.spinner('Đang giải mô hình tối ưu MILP...'):
                plans=calculate(holdings,quotes,target*1e6,lamb,fee/100,tax/100)
                fr=frontier(holdings,quotes,target*1e6,fee/100,tax/100)
            st.session_state['ep_plans']=plans
            st.session_state['ep_frontier']=fr
            st.session_state['ep_holdings']=holdings
            st.session_state['ep_plan_quotes']=quotes
            st.session_state['ep_params']=dict(target=target*1e6,lamb=lamb,fee=fee/100,tax=tax/100,
                 snapshot_at=str(batch['ts_vn'].max()),data_kind=kind)
            st.success('Đã tính 4 phương án: A, B, C và mốc tỷ trọng. Xem trang So sánh phương án.')
        except Exception as ex:
            _clear_plan()
            st.error(f'Không thể tính phương án: {type(ex).__name__}: {ex}')
    plans=st.session_state.get('ep_plans')
    if plans:
        p=plans['B']; st.markdown(cards_html([
            {'label':'Phương án cân bằng B','value':fmt.vnd_big(p['net']),'note':'Tiền ròng mô phỏng'},
            {'label':'Chi phí thanh khoản','value':fmt.vnd_big(p['cost']),'note':fmt.bps(p['cost_bps'])+' bps trên doanh số'},
            {'label':'HHI sau bán','value':fmt.num(p['hhi'],4),'note':'Độ tập trung danh mục còn lại'},
            {'label':'Mục tiêu','value':'Đạt' if p['satisfied'] else 'Chưa đạt','note':fmt.vnd_big(p['shortfall'])+' thiếu hụt'}]),unsafe_allow_html=True)
        st.markdown(verdict('Kết quả phương án B', 'Đạt mục tiêu ròng trong độ sâu ba bid quan sát.' if p['satisfied'] else
            'Mục tiêu không khả thi trong độ sâu ba mức mua; xem phần thiếu hụt.'),unsafe_allow_html=True)
    explain('Tại sao chưa thể tính với một số mã?', 'Mọi mã trong danh sách có thể được tra cứu, nhưng mô hình cần giá mua và khối lượng chờ mua tại một thời điểm chung của danh mục. OHLCV không thay thế sổ lệnh.')


def compare(root,data,t):
    if not source_labels(data):return
    plans=require_result()
    if not plans:
        saved=data['saved_plans']
        if saved is not None and not saved.empty:
            st.warning('BẢNG MẪU ĐÃ LƯU (không gắn với danh mục tự nhập hiện tại). Chỉ để kiểm tra giao diện.')
            st.markdown(frame_table(saved),unsafe_allow_html=True)
        return
    params=st.session_state['ep_params']
    if str(data['books']['ts_vn'].max())!=params['snapshot_at']:
        st.caption('Đang dùng ảnh chụp chung gần nhất của danh mục, có thể sớm hơn bản ghi mới nhất toàn thị trường.')
    st.caption('Nguồn kết quả: '+KIND_LABELS.get(params['data_kind'],params['data_kind'])+
               ' · snapshot '+params['snapshot_at']+' · phương án từ bộ tối ưu bên ngoài giao diện.')
    rows=[]
    for k,p in plans.items():
        rows.append([k+' · '+p['label'],fmt.vnd(p['net']),fmt.vnd(p['cost']),fmt.bps(p['cost_bps']),
                     fmt.shares(p['uncovered']),fmt.num(p['hhi'],4),fmt.pct(p['max_weight'])])
    columns=['Phương án','Tiền ròng','Chi phí TK','Chi phí bps','Chưa bao phủ','HHI sau bán','Tỷ trọng lớn nhất']
    st.markdown(html_table(columns,rows,numeric=set(range(1,7)),tooltips={'Chi phí TK':'Chênh lệch so với giá gần nhất ở lượng được bao phủ','HHI sau bán':'Tổng bình phương tỷ trọng giá trị còn lại'}),unsafe_allow_html=True)
    sel=choose('Xem chi tiết', ['A','B','C','P'],default='B',key='ep_compare_selected')
    p=plans[sel]
    kpi=[{'label':'Tiền thu ròng','value':fmt.vnd_big(p['net']),'note':'Ước tính tại một thời điểm'},
         {'label':'Chi phí thanh khoản','value':fmt.vnd_big(p['cost']),'note':fmt.bps(p['cost_bps'])+' bps'},
         {'label':'HHI sau bán','value':fmt.num(p['hhi'],4),'note':'Chỉ số tập trung danh mục'},
         {'label':'Thiếu mục tiêu','value':fmt.vnd_big(p['shortfall']),'note':'0 nếu đạt mục tiêu'}]
    st.markdown(cards_html(kpi),unsafe_allow_html=True)
    baseline=plans['P']; saving=baseline['cost']-plans['B']['cost']
    st.markdown(verdict('Đối chiếu phương án cân bằng B và mốc tỷ trọng',
        ('B tiết kiệm '+fmt.vnd(saving)+' chi phí thanh khoản so với mốc bán tỷ trọng.' if saving>=0 else
         'B tốn thêm '+fmt.vnd(-saving)+' chi phí thanh khoản so với mốc bán tỷ trọng.')+
        ' Khác biệt này phụ thuộc mô hình, ảnh chụp sổ lệnh và λ đã chọn.'),unsafe_allow_html=True)
    st.warning('Ước tính chi phí chỉ dựa trên BA mức giá mua tại thời điểm quan sát, KHÔNG phải giá khớp thực. Phần vượt độ sâu chỉ được báo dưới dạng khoảng lạc quan – bi quan.')
    c1,c2=st.columns(2)
    with c1:
        st.subheader('Đánh đổi chi phí – tập trung')
        plot(charts.tradeoff_fig(st.session_state.get('ep_frontier'),plans,t),'EP02_tradeoff')
        st.markdown(guide('Mỗi điểm là phương án tối ưu ở một giá trị λ; vị trí A/B/C được đánh dấu.',
            'Đường này phản ánh kết quả theo ràng buộc và hàm mục tiêu mô phỏng, không phải lợi nhuận kỳ vọng.'),unsafe_allow_html=True)
    with c2:
        st.subheader('Giá trị danh mục trước/sau')
        plot(charts.holdings_fig(p['details'],t),'EP03_holdings')
        st.markdown(guide('Chiều cao mỗi cột là số cổ phiếu còn nắm giữ × giá gần nhất.',
            'Bán cổ phiếu có thể làm cơ cấu danh mục thay đổi đáng kể.'),unsafe_allow_html=True)
    st.subheader('Thác chi phí từ giá trị tham chiếu đến tiền ròng')
    plot(charts.waterfall_fig(p,t),'EP04_cost_waterfall')
    st.markdown(guide('Mốc đầu là giá trị lượng bán theo giá gần nhất; lần lượt trừ chi phí thanh khoản, phí và thuế giả định.',
        'Tiền ròng chỉ áp dụng với lượng bán nằm trong ba mức mua đang quan sát.'),unsafe_allow_html=True)
    detail=pd.DataFrame(p['details']).rename(columns={'symbol':'Mã','held':'Nắm giữ','sold':'Bán','remaining':'Còn lại','net':'Tiền ròng','visible_depth':'Độ sâu ba mức','uncovered':'Chưa bao phủ'})
    st.markdown(frame_table(detail[['Mã','Nắm giữ','Bán','Còn lại','Độ sâu ba mức','Tiền ròng']]),unsafe_allow_html=True)
    explain('Các cột phương án','**HHI** = Σ(tỷ trọng giá trị còn lại)². **Chi phí bps** = (chi phí thanh khoản/doanh số khớp mô phỏng) × 10.000. **A/B/C/P** là tối ưu hóa theo các hàm mục tiêu khác nhau; không được hiểu là khuyến nghị mua bán.')


def liquidity(root,data,t):
    if not source_labels(data):
        history,_=read_parquet(root,'data/processed/ssi_history.parquet')
        if history is not None:
            from src.analytics.ssi_history_stats import asof_history_stats
            stats=asof_history_stats(history)
            st.caption('ADV20 lịch sử SSI (đơn vị volume gốc; chưa xác minh quy đổi CP). Chưa có sổ lệnh để tính tỷ lệ tham gia.')
            st.dataframe(stats[['symbol','adv','sigma','n_sessions','asof_date']],hide_index=True,use_container_width=True)
        return
    quotes=st.session_state.get('ep_plan_quotes') or quote_map(data)
    if not quotes:st.error('Không có dữ liệu sổ lệnh hợp lệ.');return
    if not st.session_state.get('ep_plan_quotes') and len(quotes)>12:
        selected=st.multiselect('Mã xem thanh khoản',sorted(quotes),default=sorted(quotes)[:5],max_selections=12)
        quotes={s:quotes[s] for s in selected}
    qstats=data['liquidity']
    if data.get('use_ssi') and st.session_state.get('ep_params'):
        try:
            from src.analytics.ssi_history_stats import asof_history_stats
            history,_=read_parquet(root,'data/processed/ssi_history.parquet')
            factor=float(data['books']['history_volume_factor'].iloc[0])
            qstats=asof_history_stats(history,pd.Timestamp(st.session_state['ep_params']['snapshot_at']).date())
            qstats['adv']*=factor
        except Exception as ex:
            qstats=None
            st.warning('Không tính được ADV theo thời điểm danh mục: '+str(ex))
    if data.get('use_ssi'):
        st.caption('ADV20 lấy từ 20 phiên SSI trước ngày snapshot; không dùng volume trong phiên hiện tại.')
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
    for s,q in quotes.items():
        depth=sum(v for _,v in q.bids)
        qty=sold_map.get(s,0)
        a=adv.get(s)
        participation=qty/a if a is not None and pd.notna(a) and a>0 else None
        spread=((q.ask1-q.bids[0][0])/((q.ask1+q.bids[0][0])/2)*10000
                if q.ask1 is not None and q.bids and q.ask1>0 else None)
        rows.append([s,fmt.shares(a),fmt.pct(participation),fmt.shares(depth),fmt.bps(spread),fmt.shares(qty)])
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
    if qstats is None:st.caption('Chưa có dữ liệu: cần file '+LIQUIDITY+' để tính ADV và tỷ lệ tham gia.')


def ssi_history(root,data,t):
    path=Path(root)/'data/processed/ssi_history.parquet'
    stats_path=Path(root)/'outputs/tables/ssi_liquidity_stats.parquet'
    st.info('SSI FastConnect V3 chính thức. Chạy lệnh với API Key/Secret Market Data đã được cấp. '
            'OHLCV theo ngày dùng cho biểu đồ và ADV; không có ba mức bid để lập phương án.')
    st.code('py scripts/ssi_v3_sync.py --check\n'
            'py scripts/ssi_v3_sync.py --catalog\n'
            'py scripts/ssi_v3_sync.py --history --symbols HPG VPB ACB --from-date 01/09/2026 --to-date 20/11/2026',
            language='powershell')
    st.caption('Hướng dẫn kết nối: docs/SSI_FASTCONNECT_SETUP.md. Không nhập API Key hoặc Secret vào dashboard.')
    # The 3-board securities catalog is real only after --catalog succeeds.
    # Show it independently of the historical prices, with an explicit source label.
    catalog_path=Path(root)/'data/processed/ssi_securities.parquet'
    if catalog_path.exists():
        with st.expander('Danh sách mã SSI FastConnect V3 đã lưu (HOSE · HNX · UPCOM)'):
            try:
                catalog=pd.read_parquet(catalog_path)
                if not {'symbol','board','source'}.issubset(catalog.columns):
                    raise ValueError('Thiếu symbol, board hoặc source')
                if set(catalog['source'])!={'ssi_fastconnect_v3'}:
                    raise ValueError('Không đúng nguồn SSI FastConnect V3')
                query=st.text_input('Tìm theo mã / tên chứng khoán',key='ep_ssi_search').strip()
                if query:
                    matched=catalog['symbol'].astype(str).str.contains(query,case=False,regex=False)
                    if 'name' in catalog.columns:
                        matched=matched|catalog['name'].fillna('').astype(str).str.contains(query,case=False,regex=False)
                    shown=catalog.loc[matched]
                else:
                    shown=catalog
                boards=st.multiselect('Sàn',sorted(catalog.board.dropna().unique()),default=sorted(catalog.board.dropna().unique()),key='ep_catalog_boards')
                shown=shown[shown.board.isin(boards)]
                st.caption(f'Tìm thấy {len(shown)} / {len(catalog)} mã đã lưu · không phải toàn bộ đều là cổ phiếu phổ thông đang giao dịch.')
                st.download_button('Tải danh sách đã lọc',fmt.csv_bom(shown),'ExitPlan_catalog.csv','text/csv')
                st.markdown(frame_table(shown,max_rows=60),unsafe_allow_html=True)
            except (OSError,ValueError,KeyError) as exc:
                st.warning(f'File danh sách mã SSI không đọc được: {exc}')
    if not path.exists():
        st.warning('Chưa có ssi_history.parquet. Khi SSI cấp quyền, dùng script V3 để ghi dữ liệu thực tế; không tự tạo dữ liệu demo.')
        return
    try:
        h=pd.read_parquet(path)
        required={'symbol','tradingDate','close','volume','data_kind','source'}
        if not required.issubset(h.columns):raise ValueError('Thiếu cột: '+', '.join(sorted(required-set(h.columns))))
        if h.empty:return st.warning('File lịch sử SSI trống.')
        if set(h['data_kind'])!={'historical'}:raise ValueError('Nhãn data_kind không phải historical')
        origins=set(h['source'].dropna().astype(str))
        if origins=={'ssi_fastconnect_v3'}:
            st.success('Đã nạp file dữ liệu lịch sử từ SSI FastConnect V3 được ghi bởi script riêng.')
        else:
            st.warning('File lịch sử hiện tại không xác nhận là từ SSI FastConnect V3. '
                       'Nguồn ghi trong file: '+', '.join(sorted(origins or {'không xác định'})))
        st.caption('Nguồn file lưu cục bộ không chứng minh kết nối API đang hoạt động ở thời điểm xem dashboard.')
        h['tradingDate']=pd.to_datetime(h['tradingDate'],errors='coerce')
        names=sorted(h['symbol'].dropna().unique().tolist())
        selected=st.multiselect('Mã cổ phiếu',names,default=names[:5],max_selections=12)
        st.caption(f'Kho lịch sử có {len(names)} mã; biểu đồ hiển thị tối đa 12 mã để dễ đọc.')
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
        if stats_path.exists():
            stats=pd.read_parquet(stats_path)
            st.subheader('ADV 20 phiên và độ biến động')
            st.caption('ADV/sigma chỉ có khi >=20 phiên hợp lệ mỗi mã. Đơn vị volume: số cổ phiếu theo nguồn API.')
            st.markdown(frame_table(stats[stats['symbol'].isin(selected)],max_rows=40),unsafe_allow_html=True)
        st.subheader('Dữ liệu OHLCV đã lưu')
        st.markdown(frame_table(view,max_rows=60),unsafe_allow_html=True)
        st.download_button('⬇️ Tải CSV lịch sử SSI',fmt.csv_bom(view),'ExitPlan_SSI_history.csv','text/csv')
        st.warning('Không tự tạo bidPrice1–3/bidVol1–3 từ giá đóng cửa. Trang Lập phương án chỉ dùng snapshot sổ lệnh độc lập.')
    except Exception as exc:st.error(f'Lỗi đọc dữ liệu SSI: {type(exc).__name__}: {exc}')


def data_page(root,data,t):
    """Trình bày thống kê và trạng thái kết nối theo thẻ, không nhúng Excel/JSON thô."""
    valid=source_labels(data)
    b=data['books']
    if valid:
        duration=b['ts_vn'].max()-b['ts_vn'].min()
        st.markdown(cards_html([
            {'label':'Số phiên','value':fmt.num(b['ts_vn'].dt.date.nunique()),'note':'Theo ngày giờ Việt Nam'},
            {'label':'Tổng bản ghi','value':fmt.num(len(b)),'note':'Trong file snapshot'},
            {'label':'Số mã','value':fmt.num(b['symbol'].nunique()),'note':'Được theo dõi'},
            {'label':'Khoảng thời gian','value':fmt.num(duration.total_seconds()/3600,1)+' giờ','note':'Dữ liệu đã ghi'}
        ]),unsafe_allow_html=True)

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
            st.dataframe(quality,hide_index=True,use_container_width=True)

    st.subheader('Trạng thái kết nối dữ liệu')
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
                '<div class="ep-panel-desc">Tình trạng từ file đã ghi; dashboard không tự kết nối API.</div>'
                +info_html+'</div>',
                unsafe_allow_html=True,
            )
            if kind=='synthetic':st.warning('Bộ ghi chỉ đang mô phỏng. Chưa có kết nối WebSocket thật.')
            with st.expander('Chi tiết kỹ thuật · Nhật ký JSON',expanded=False):
                st.code(json.dumps(status,ensure_ascii=False,indent=2),language='json')
        except (OSError,ValueError) as ex:
            st.error(f'Tệp trạng thái không hợp lệ: {ex}')
    else:
        st.info('Chưa có file trạng thái bộ ghi. Dashboard không tự mở WebSocket.')
    st.caption('Múi giờ Asia/Ho_Chi_Minh (UTC+7); dữ liệu được thu thập ngoài dashboard.')


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


def downloads(root,data,t):
    source_labels(data)
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
    if data['liquidity'] is not None:
        st.download_button('⬇️ Tải bảng thanh khoản đã lưu',fmt.csv_bom(data['liquidity']),'ExitPlan_liquidity.csv','text/csv',use_container_width=True)
    else:st.warning('Chưa có dữ liệu: cần file '+LIQUIDITY)
    st.caption('Mỗi CSV dùng UTF-8 có BOM để Excel nhận tiếng Việt. Không tự tạo hoặc điều chỉnh dữ liệu nguồn.')

FUNCTIONS={'overview':overview,'planner':planner,'compare':compare,'liquidity':liquidity,
           'data':data_page,'ssi_history':ssi_history,'validation':validation,'methods':methods,'downloads':downloads}

def render_page(page,root,cfg):
    page_header(page,cfg['accent'],cfg['mode'])
    data=load(root)
    t=charts.apply_palette(cfg['mode'],cfg['accent'])
    try:
        FUNCTIONS[page](root,data,t)
    except Exception as ex:
        st.error(f'Không thể hiển thị trang: {type(ex).__name__}: {ex}')
        st.caption('Không dùng dữ liệu giả định để thay cho dữ liệu đang thiếu. Hãy kiểm tra file đầu vào và schema.')
