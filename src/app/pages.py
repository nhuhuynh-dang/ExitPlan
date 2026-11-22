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
from src.data.repository import read_parquet,read_csv,normalize_book,latest_books,available_symbols,resolve_path
from src.finance.engine import quote_from_row,sell_preview,hhi
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
 'ssi_history':'OHLCV thật nếu truy cập được iBoard, ADV 20 phiên và trạng thái API.',
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
 'ssi_history':('SSI IBOARD · HISTORICAL','Dữ liệu lịch sử SSI','Dữ liệu ngày, ADV và biến động từ API iBoard cộng đồng mô tả; chưa phải FastConnect và không có sổ lệnh.'),
 'validation':('MODEL GOVERNANCE','Kiểm chứng mô hình','Xem kết quả kiểm thử, phân tích độ nhạy và phát lại ảnh chụp đã lưu.'),
 'methods':('METHODOLOGY','Phương pháp & giới hạn','Giả định, công thức, mô hình tối ưu hóa và phạm vi sử dụng có trách nhiệm.'),
 'downloads':('REPRODUCIBILITY','Tải dữ liệu','Xuất các bảng đã tính để kiểm tra, đối chiếu và viết báo cáo.'),
}

def page_header(key,accent):
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
        '<p>'+escape(description)+'</p><div class="art">'+hero_svg(accent)+'</div></div>'
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
    raw,err=read_parquet(root,SNAPSHOT,overrides)
    books=None
    if raw is not None:
        try:books=normalize_book(raw)
        except Exception as exc:err=f'Dữ liệu không hợp lệ: {exc}'
    liquidity,liquidity_err=read_parquet(root,LIQUIDITY,overrides)
    saved_plans,_=read_parquet(root,PLANS,overrides)
    saved_frontier,_=read_parquet(root,FRONTIER,overrides)
    quality,_=read_csv(root,QUALITY,overrides)
    return dict(books=books,err=err,liquidity=liquidity,liquidity_err=liquidity_err,
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
    label=KIND_LABELS.get(kind,kind)
    st.markdown(badge('Nguồn: '+label,kind)+badge('Cập nhật: '+last.strftime('%d/%m/%Y %H:%M:%S')+' · UTC+7')+
                badge('File đã ghi · không kết nối API trong dashboard'),unsafe_allow_html=True)
    return True

def quote_map(data):
    return {s:quote_from_row(row) for s,row in latest_books(data['books']).iterrows() if s in available_symbols(data['books'])}

def plot(fig,code):st.plotly_chart(fig,use_container_width=True,config=charts.png_config(code))

def require_result():
    p=st.session_state.get('ep_plans')
    if p is None:
        note('Chưa có phương án cho danh mục hiện tại. Vào trang “Lập phương án” và bấm “Tính phương án”.')
        return None
    return p

def overview(root,data,t):
    if not source_labels(data):return
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
        plot(charts.time_fig(b,t,normalize=True),'EP01_price')
        st.markdown(guide('Mỗi mã được quy về 100 ở quan sát đầu tiên để dễ so sánh biến động tương đối.',
            'Dữ liệu chỉ phản ánh các bản ghi đã lưu, không phải lịch sử giá được API cấp tự động.'),unsafe_allow_html=True)
    with c:
        st.subheader('Trạng thái nguồn dữ liệu')
        status='Đã đọc file dữ liệu'
        st.metric('Trạng thái dashboard',status)
        st.metric('Thời điểm mới nhất',last.strftime('%d/%m/%Y %H:%M'))
        st.metric('Số mã có thể lập phương án',fmt.num(len(symbols)))
        st.caption('File đã lưu không xác nhận WebSocket đang kết nối. Xem trạng thái bộ ghi tại trang Dữ liệu & kết nối.')


def planner(root,data,t):
    if not source_labels(data):return
    syms=available_symbols(data['books'])
    if not syms:
        st.error('Không có mã có sổ lệnh bid hợp lệ. Không thể tính phương án.');return
    st.subheader('Danh mục tự nhập · không đọc tài khoản')
    default=[{'Mã':s,'Số lượng':5000 if i==0 else (4000 if i==1 else 3000)} for i,s in enumerate(syms[:3])]
    if 'ep_portfolio' not in st.session_state:st.session_state['ep_portfolio']=pd.DataFrame(default)
    with st.form('form_exitplan'):
        frame=st.data_editor(st.session_state['ep_portfolio'],num_rows='dynamic',hide_index=True,use_container_width=True,
          column_config={'Mã':st.column_config.SelectboxColumn('Mã cổ phiếu',options=syms,required=True),
                         'Số lượng':st.column_config.NumberColumn('Số lượng (CP)',min_value=0,step=100,format='%d')})
        c1,c2=st.columns(2)
        with c1:
            target=st.number_input('Tiền RÒNG cần thu (triệu đồng)',min_value=0.1,value=100.,step=5.)
            lamb=st.slider('Ưu tiên λ · 0 = chi phí / 1 = tập trung',0.,1.,.5,.05)
        with c2:
            st.caption('TODO: Xác nhận biểu phí và thuế áp dụng theo thời điểm giao dịch. Mặc định 0; nhập giả định nếu muốn.')
            fee=st.number_input('Phí bán giả định (%)',0.,5.,0.,.05)
            tax=st.number_input('Thuế/chi phí khác giả định (%)',0.,5.,0.,.05)
        run=st.form_submit_button('🧮 Tính phương án',type='primary',use_container_width=True)
    if run:
        try:
            holdings={}
            for row in frame.to_dict('records'):
                s=str(row.get('Mã') or '').strip().upper()
                if not s:continue
                if s not in syms:raise ValueError(f'{s}: không có sổ lệnh khả dụng')
                v=float(row.get('Số lượng') or 0)
                if v<0 or int(v)!=v:raise ValueError(f'{s}: số lượng phải là số nguyên không âm')
                holdings[s]=holdings.get(s,0)+int(v)
            holdings={k:v for k,v in holdings.items() if v>0}
            if not holdings:raise ValueError('Danh mục phải có ít nhất một mã số lượng dương')
            quotes=quote_map(data)
            with st.spinner('Đang giải mô hình tối ưu MILP...'):
                plans=calculate(holdings,quotes,target*1e6,lamb,fee/100,tax/100)
                fr=frontier(holdings,quotes,target*1e6,fee/100,tax/100)
            st.session_state['ep_plans']=plans
            st.session_state['ep_frontier']=fr
            st.session_state['ep_holdings']=holdings
            st.session_state['ep_plan_quotes']={s:quotes[s] for s in holdings}
            st.session_state['ep_params']=dict(target=target*1e6,lamb=lamb,fee=fee/100,tax=tax/100,
                                                  snapshot_at=str(data['books']['ts_vn'].max()),
                                                  data_kind=str(data['books']['data_kind'].iloc[0]))
            st.session_state['ep_portfolio']=frame
            st.success('Đã tính 4 phương án: A, B, C và mốc tỷ trọng. Xem trang So sánh phương án.')
        except Exception as ex:
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
    explain('Tại sao chỉ chọn mã có bid?', 'Mô hình tính tiền thu từ giá mua đang chờ và khối lượng tương ứng. Không có mức bid số hợp lệ thì không đủ cơ sở ước tính giá bán.')


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
        st.warning('Ảnh chụp trong file đã thay đổi so với lần tính gần nhất. Kết quả dưới đây là kết quả cũ; hãy tính lại phương án.')
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
    if not source_labels(data):return
    quotes=quote_map(data)
    if not quotes:st.error('Không có dữ liệu sổ lệnh hợp lệ.');return
    qstats=data['liquidity']
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
        z=sell_preview(quotes[s],held,0.,0.)
        if z['uncovered']:
            range_rows.append([s,fmt.shares(z['uncovered']),fmt.vnd(z['bound_low']),fmt.vnd(z['bound_high'])])
    if range_rows:st.markdown(html_table(['Mã','Vượt độ sâu','Bi quan','Lạc quan'],range_rows,numeric=(1,2,3)),unsafe_allow_html=True)
    else:note('Không có vị thế vượt độ sâu được quan sát, hoặc chưa nhập danh mục.')
    if qstats is None:st.caption('Chưa có dữ liệu: cần file '+LIQUIDITY+' để tính ADV và tỷ lệ tham gia.')


def ssi_history(root,data,t):
    path=Path(root)/'data/processed/ssi_history.parquet'
    stats_path=Path(root)/'outputs/tables/ssi_liquidity_stats.parquet'
    st.info('Nguồn: SSI iBoard (endpoint do cộng đồng ghi nhận), không phải FastConnect được cấp quyền. '
            'Dữ liệu OHLCV theo ngày chỉ để tính ADV và phân tích; không có ba mức bid để lập phương án.')
    st.code('py scripts/fetch_ssi_history.py --symbols HPG VPB ACB --from-date 01/09/2026 --to-date 20/11/2026',language='powershell')
    if not path.exists():
        st.warning('Chưa tìm thấy data/processed/ssi_history.parquet. Chạy lệnh trên từ thư mục dự án; nếu API trả 400 thì chưa có dữ liệu để hiển thị.')
        return
    try:
        h=pd.read_parquet(path)
        required={'symbol','tradingDate','close','volume','data_kind','source'}
        if not required.issubset(h.columns):raise ValueError('Thiếu cột: '+', '.join(sorted(required-set(h.columns))))
        if h.empty:return st.warning('File lịch sử SSI trống.')
        if set(h['data_kind'])!={'historical'}:raise ValueError('Nhãn data_kind không phải historical')
        h['tradingDate']=pd.to_datetime(h['tradingDate'],errors='coerce')
        names=sorted(h['symbol'].dropna().unique().tolist())
        selected=st.multiselect('Mã cổ phiếu',names,default=names)
        view=h[h['symbol'].isin(selected)].copy().sort_values(['symbol','tradingDate'])
        if view.empty:return st.info('Chọn ít nhất một mã để xem dữ liệu SSI.')
        from plotly import graph_objects as go
        f=go.Figure()
        for sym,g in view.groupby('symbol'):
            f.add_trace(go.Scatter(x=g['tradingDate'],y=g['close'],mode='lines+markers',name=sym))
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
    quality=data['quality']
    if quality is None or quality.empty:
        st.info('Chưa có file chất lượng dữ liệu. Vui lòng chạy pipeline trước.')
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
            st.warning('Dữ liệu GIẢ LẬP (synthetic) — chưa phản ánh báo giá SSI/NEO thật.')
        st.caption('Nguồn dữ liệu: '+source)
        with st.expander('Chi tiết kỹ thuật · Dữ liệu gốc',expanded=False):
            st.dataframe(quality,hide_index=True,use_container_width=True)

    st.subheader('Trạng thái kết nối dữ liệu')
    status_file=Path(root)/'outputs/tables/recorder_status.json'
    if status_file.exists():
        try:
            status=json.loads(status_file.read_text(encoding='utf-8'))
            if not isinstance(status,dict):raise ValueError('Trạng thái phải là đối tượng JSON')
            kind=str(status.get('data_kind','unknown'))
            state=str(status.get('state',status.get('status','unknown')))
            status_label='Giả lập' if kind=='synthetic' else ('Đang ghi dữ liệu' if state in ('connected','recording') else 'Chưa kết nối')
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
    with st.expander('Tham khảo trường dữ liệu NEO',expanded=False):
        from src.data.schema import NEO_TO_STANDARD
        st.markdown(html_table(['Trường nguồn','Trường chuẩn hóa'],
            [[a,v] for a,v in NEO_TO_STANDARD.items()]),unsafe_allow_html=True)
    st.caption('Múi giờ Asia/Ho_Chi_Minh (UTC+7); dữ liệu được thu thập ngoài dashboard.')


def validation(root,data,t):
    source_labels(data)
    folder=Path(root)/'outputs/tables'
    files=sorted(folder.glob('validation_*.csv'))
    if not files:
        st.warning('Chưa có dữ liệu: cần file outputs/tables/validation_*.csv')
        return
    selections=st.selectbox('Bảng kiểm chứng', [f.name for f in files])
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
    try:config=json.loads(config_path.read_text(encoding='utf-8'))
    except (OSError,ValueError) as ex:
        st.warning(f'Không đọc được config.json: {ex}');config={}
    definitions=[('01 · Dữ liệu','Ảnh chụp ba mức bid của NEO API WebSocket đã được pipeline ngoài dashboard lưu, có timestamp Việt Nam và nhãn loại dữ liệu.'),
      ('02 · Mô hình chi phí','Doanh thu = Σ số cổ phiếu bán × giá mua tại từng mức. Tiền ròng = doanh thu − phí − thuế giả định. Chi phí thanh khoản = max(0; giá gần nhất × lượng được bao phủ − doanh thu).'),
      ('03 · Bài toán tối ưu','MILP chọn số lô 100 cổ phiếu từ từng mã, không vượt lượng nắm giữ và độ sâu quan sát. A giảm chi phí; B đánh đổi chi phí với proxy tập trung; C giảm proxy tập trung; P gần tỷ trọng bán theo giá trị.'),
      ('04 · Giới hạn','Không có toàn bộ sổ lệnh hoặc diễn biến sau khi đặt lệnh; không chứng minh khả năng khớp. HHI được tính sau tối ưu, còn mục tiêu tập trung trong MILP sử dụng proxy bình phương giá trị còn lại.')]
    columns=st.columns(2)
    for i,(title,body) in enumerate(definitions):
        with columns[i%2]:
            st.markdown(f'<div class="ep-method"><h3>{escape(title)}</h3><p>{escape(body)}</p></div>',unsafe_allow_html=True)
    st.subheader('Thông số từ file cấu hình')
    if config:st.json(config)
    st.caption('TODO: Xác minh đơn vị NEO thực tế; phí bán, thuế và giả định tác động giá trước khi phân tích thực nghiệm.')
    st.warning('Không tự động đặt lệnh, không kết nối tài khoản, không đưa khuyến nghị đầu tư. Ước tính chỉ dựa trên ba mức giá mua tại một thời điểm.')


def downloads(root,data,t):
    source_labels(data)
    plans=st.session_state.get('ep_plans')
    if plans:
        summary=summaries(plans)
        st.download_button('⬇️ Tải bảng so sánh phương án',fmt.csv_bom(summary),'ExitPlan_plans.csv','text/csv',use_container_width=True)
        details=pd.DataFrame([dict(plan=k,**d) for k,p in plans.items() for d in p['details']])
        st.download_button('⬇️ Tải chi tiết lượng bán',fmt.csv_bom(details),'ExitPlan_plan_details.csv','text/csv',use_container_width=True)
        fr=st.session_state.get('ep_frontier')
        if fr is not None:st.download_button('⬇️ Tải đường đánh đổi',fmt.csv_bom(fr),'ExitPlan_frontier.csv','text/csv',use_container_width=True)
    else:st.info('Chưa có bảng phương án hiện tại. Bấm “Tính phương án” để tạo.')
    if data['liquidity'] is not None:
        st.download_button('⬇️ Tải bảng thanh khoản đã lưu',fmt.csv_bom(data['liquidity']),'ExitPlan_liquidity.csv','text/csv',use_container_width=True)
    else:st.warning('Chưa có dữ liệu: cần file '+LIQUIDITY)
    st.caption('Mỗi CSV dùng UTF-8 có BOM để Excel nhận tiếng Việt. Không tự tạo hoặc điều chỉnh dữ liệu nguồn.')

FUNCTIONS={'overview':overview,'planner':planner,'compare':compare,'liquidity':liquidity,
           'data':data_page,'ssi_history':ssi_history,'validation':validation,'methods':methods,'downloads':downloads}

def render_page(page,root,cfg):
    page_header(page,cfg['accent'])
    data=load(root)
    t=charts.apply_palette(cfg['mode'],cfg['accent'])
    try:
        FUNCTIONS[page](root,data,t)
    except Exception as ex:
        st.error(f'Không thể hiển thị trang: {type(ex).__name__}: {ex}')
        st.caption('Không dùng dữ liệu giả định để thay cho dữ liệu đang thiếu. Hãy kiểm tra file đầu vào và schema.')
