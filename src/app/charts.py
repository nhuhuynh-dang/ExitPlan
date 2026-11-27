"""Biểu đồ Plotly chỉ nhận kết quả đã tính, không gọi API hay tối ưu."""
import colorsys
import pandas as pd
import plotly.graph_objects as go
from src.app.theme import palette
from src.app.fmt import signed

def _rotate(hex_color,delta=0.1):
    r,g,b=[int(hex_color[i:i+2],16)/255 for i in (1,3,5)]
    h,l,s=colorsys.rgb_to_hls(r,g,b)
    r,g,b=colorsys.hls_to_rgb((h+delta)%1,min(.8,l+.05),min(1,s+.02))
    return '#'+''.join(f'{round(c*255):02x}' for c in (r,g,b))

def apply_palette(mode,accent):
    p=palette(mode)
    p.update(secondary='#6FD6BA' if mode=='Tối' else '#4CB99A',tertiary='#B4A2FF' if mode=='Tối' else '#9280DD')
    return p

def layout(fig,t,height=360,title=None,legend=True):
    fig.update_layout(height=height,margin=dict(l=12,r=14,t=55 if title else 35,b=20),
                      paper_bgcolor=t['surface'],plot_bgcolor=t['plot'],
                      separators=',.',font=dict(family='Be Vietnam Pro, sans-serif',size=12,color=t['text']),
                      showlegend=legend,legend=dict(orientation='h',y=1.03,x=0,bgcolor='rgba(0,0,0,0)',font=dict(color=t['text'])),
                      hoverlabel=dict(bgcolor=t['surface'],font_color=t['text'],bordercolor=t['border']),
                      xaxis=dict(tickfont=dict(color=t['text'])),yaxis=dict(tickfont=dict(color=t['text'])))
    if title:fig.update_layout(title=dict(text=title,x=0,font=dict(size=15)))
    fig.update_xaxes(showgrid=False,zeroline=False,automargin=True,linecolor=t['border'],tickfont=dict(color=t['text']))
    fig.update_yaxes(showgrid=True,gridcolor=t['border'],zeroline=False,automargin=True,tickfont=dict(color=t['text']))
    return fig

def png_config(name):
    return {'displaylogo':False,'modeBarButtonsToRemove':['lasso2d','select2d','autoScale2d'],
            'toImageButtonOptions':{'format':'png','filename':name,'scale':2}}

def tradeoff_fig(frontier,plans,t):
    fig=go.Figure()
    if frontier is not None and not frontier.empty:
        fig.add_trace(go.Scatter(x=frontier['cost'],y=frontier['hhi'],name='Đường đánh đổi',mode='lines+markers',
                                 line=dict(color=t['accent'],width=2.4),marker=dict(size=6),
                                 customdata=frontier['lamb'],hovertemplate='Chi phí %{x:,.0f} đ<br>HHI %{y:.4f}<br>λ %{customdata:.2f}<extra></extra>'))
    if plans:
        for i,p in plans.items():
            if i not in ('A','B','C'):continue
            fig.add_trace(go.Scatter(x=[p['cost']],y=[p['hhi']],name=f'{i} · {p["label"]}',mode='markers+text',
                                     text=[i],textposition='top center',marker=dict(size=13,line=dict(width=1,color=t['text']),
                                     color={'A':t['accent'],'B':t['secondary'],'C':t['tertiary']}[i]),
                                     hovertemplate=f'{i}: %{{x:,.0f}} đ; HHI %{{y:.4f}}<extra></extra>'))
    layout(fig,t,height=385)
    fig.update_xaxes(title='Chi phí thanh khoản (đồng)')
    fig.update_yaxes(title='HHI danh mục sau bán')
    return fig

def holdings_fig(details,t):
    data=pd.DataFrame(details)
    fig=go.Figure()
    for col,label,color in [('before_value','Trước bán',t['accent']),('after_value','Sau bán',t['secondary'])]:
        fig.add_bar(x=data['symbol'],y=data[col],name=label,marker_color=color,
                    hovertemplate='%{x}<br>%{y:,.0f} đ<extra>'+label+'</extra>')
    fig.update_layout(barmode='group');layout(fig,t,340)
    fig.update_yaxes(title='Giá trị (đồng)')
    return fig

def waterfall_fig(plan,t):
    """Waterfall: last price reference gross, execution discount, fees, taxes, net.
    Reference = gross + observed liquidity_cost. Totals reconcile to net.
    """
    ref=plan['gross']+plan['cost']
    fig=go.Figure(go.Waterfall(orientation='v',measure=['absolute','relative','relative','relative','total'],
        x=['Giá trị tham chiếu','Chi phí thanh khoản','Phí bán','Thuế/khác','Tiền ròng'],
        y=[ref,-plan['cost'],-plan['fee'],-plan['tax'],0],
        text=[signed(ref,0,' ₫'),signed(-plan['cost'],0,' ₫'),signed(-plan['fee'],0,' ₫'),
              signed(-plan['tax'],0,' ₫'),signed(plan['net'],0,' ₫')],textposition='outside',
        increasing=dict(marker_color=t['positive']),decreasing=dict(marker_color=t['negative']),
        totals=dict(marker_color=t['accent']),connector=dict(line_color=t['border'])))
    layout(fig,t,height=390,legend=False)
    fig.update_yaxes(title='Giá trị (đồng)')
    return fig

def compare_style(fig,t,wide=False):
    """Comparison layout only: preserve all traces, values and hover templates."""
    fig.update_layout(
        height=380 if wide else 365,autosize=True,
        margin=dict(l=12,r=20,t=24,b=30,autoexpand=True),
        legend=dict(orientation='h',x=0,y=-.22,xanchor='left',yanchor='top',
                    font=dict(size=11,color=t['text'])),
        font=dict(size=12),hoverlabel=dict(font_size=12))
    fig.update_xaxes(automargin=True,tickfont=dict(size=11))
    fig.update_yaxes(automargin=True,tickfont=dict(size=11))
    if wide:
        # Horizontal, wrapped display labels; keep the original trace categories.
        labels=['Giá trị tham chiếu','Chi phí thanh khoản','Phí bán','Thuế/khác','Tiền ròng']
        display=['Giá trị<br>tham chiếu','Chi phí<br>thanh khoản','Phí bán','Thuế/khác','Tiền ròng']
        fig.update_xaxes(tickangle=0,tickmode='array',tickvals=labels,ticktext=display,
                         tickfont=dict(size=12,color=t['text']))
        fig.update_layout(margin=dict(b=55))
    return fig


def depth_fig(quotes,t):
    fig=go.Figure()
    for i in range(3):
        names=[]; vol=[]
        for s,q in quotes.items():
            names.append(s); vol.append(q.bids[i][1] if len(q.bids)>i else 0)
        fig.add_bar(x=names,y=vol,name=f'Bid {i+1}',marker_color=[t['accent'],t['secondary'],t['tertiary']][i])
    fig.update_layout(barmode='stack'); layout(fig,t,height=370)
    fig.update_yaxes(title='Khối lượng chào mua (CP)')
    return fig

def time_fig(df,t,normalize=False):
    """Vẽ chuỗi từ file. normalize=True chỉ chuẩn hóa HIỂN THỊ, không đổi dữ liệu gốc."""
    fig=go.Figure()
    colors=[t['accent'],t['secondary'],t['tertiary'],'#E5AC55','#63A6F2','#7DC6BA']
    for idx,(sym,g) in enumerate(df.groupby('symbol')):
        g=g.sort_values('ts_vn').dropna(subset=['closePrice'])
        if g.empty:continue
        original=pd.to_numeric(g['closePrice'],errors='coerce')
        valid=original[original.gt(0)]
        if valid.empty:continue
        value=(original / valid.iloc[0]*100) if normalize else original
        label=f'{sym} (gốc 100)' if normalize else str(sym)
        hover=('%{x|%d/%m/%Y %H:%M}<br>Chỉ số %{y:,.2f}<extra>'+str(sym)+'</extra>') if normalize else ('%{x|%d/%m/%Y %H:%M}<br>%{y:,.0f} đ<extra>'+str(sym)+'</extra>')
        fig.add_trace(go.Scatter(x=g['ts_vn'],y=value,mode='lines',name=label,
                                 line=dict(color=colors[idx%len(colors)],width=2.7),hovertemplate=hover))
    layout(fig,t,height=370)
    fig.update_layout(hovermode='x unified',legend=dict(orientation='h',x=0,y=1.1))
    fig.update_xaxes(tickformat='%d/%m %H:%M',nticks=7)
    fig.update_yaxes(title='Chỉ số giá (gốc = 100)' if normalize else 'Giá trị theo dữ liệu gốc')
    if normalize:fig.add_hline(y=100,line=dict(color=t['muted'],dash='dot',width=1))
    return fig

def overview_time_fig(df,t):
    """Presentation-only variant of the existing normalized price chart."""
    fig=time_fig(df,t,normalize=True)
    dark=t['bg']=='#0F172A'
    colors=(['#60A5FA','#2DD4BF','#FBBF24','#C4B5FD','#FB7185','#38BDF8',
             '#A3E635','#F9A8D4','#FDBA74','#A5B4FC','#67E8F9','#E2E8F0'] if dark else
            ['#2563EB','#087F75','#B45309','#7C3AED','#BE185D','#0369A1',
             '#4D7C0F','#C2410C','#4338CA','#0E7490','#9F1239','#475569'])
    for i,trace in enumerate(fig.data):
        trace.update(line=dict(color=colors[i%len(colors)],width=2.6,
                               dash='solid' if i<6 else 'dash'),
                     name=str(trace.name).replace(' (gốc 100)',''))
    fig.update_layout(height=490,autosize=True,
                      margin=dict(l=12,r=14,t=20,b=28,autoexpand=True),
                      legend=dict(orientation='h',x=0,y=-.22,xanchor='left',
                                  yanchor='top',font=dict(size=12,color=t['text'])),
                      hovermode='x unified',hoverlabel=dict(font_size=12),
                      font=dict(size=13))
    fig.update_xaxes(tickfont=dict(size=12),nticks=6,automargin=True)
    fig.update_yaxes(tickfont=dict(size=12),automargin=True,
                     title=dict(text='Chỉ số giá (gốc = 100)',font=dict(size=12)))
    fig.update_shapes(line=dict(color=t['muted'],dash='dash',width=1.3))
    return fig

def sensitivity_fig(df,t):
    fig=go.Figure()
    for label,g in df.groupby('variable'):
        fig.add_trace(go.Scatter(x=g['value'],y=g['net'],mode='lines+markers',name=label))
    layout(fig,t,height=340)
    fig.update_yaxes(title='Tiền ròng (đ)')
    return fig
