"""Chuẩn hóa và lưu dữ liệu MARKET STREAM đã nhận, KHÔNG xác thực/đặt lệnh.

Dùng riêng CLI để có thể kiểm thử các message NEO mà không cần token.
Các trường được đối chiếu với tài liệu stockInfo do người dùng cung cấp.
TODO: xác nhận đơn vị giá, khối lượng, kiểu message envelope qua kết nối thực tế.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import math
import os
import pandas as pd

VN=ZoneInfo('Asia/Ho_Chi_Minh')
FIELDS=('symbol','closePrice','totalTradingVolume','bidPrice1','bidPrice2','bidPrice3',
        'bidVol1','bidVol2','bidVol3','askPrice1','askVol1','ceilingPrice','floorPrice','refPrice')
NUMERIC=FIELDS[1:]


def now_vn():
    return datetime.now(VN)


def _records(payload):
    """Unwraps raw stockInfo dict or common envelope; refuses unrelated channels."""
    if isinstance(payload,list):
        for it in payload:
            yield from _records(it)
        return
    if not isinstance(payload,dict):
        return
    chan=payload.get('channel') or payload.get('topic')
    if chan and chan != 'stockInfo':
        return
    if 'symbol' in payload:
        yield payload
        return
    for key in ('data','payload','message','items','result'):
        if key in payload:
            yield from _records(payload[key]);return


def _number(v):
    if v is None or isinstance(v,bool):return None
    if isinstance(v,str) and v.strip().upper() in ('','ATO','ATC','PLO','NULL'):return None
    try:
        z=float(v)
        return z if math.isfinite(z) else None
    except (ValueError,TypeError):return None


def normalize_event(msg, received_at=None, data_kind='live'):
    """Trả (rows, rejection_stats). Mỗi row là snapshot có timestamp lúc nhận.

    NEO stockInfo example không có exchange timestamp, dùng giờ nhận (KHÔNG phải giờ khớp lệnh).
    """
    if data_kind not in ('live','historical','synthetic'):
        raise ValueError('data_kind không hợp lệ')
    ts=received_at or now_vn()
    ts=pd.Timestamp(ts)
    ts=ts.tz_localize(VN) if ts.tzinfo is None else ts.tz_convert(VN)
    rows=[]; stats=Counter()
    for item in _records(msg):
        sym=str(item.get('symbol') or '').strip().upper()
        if not sym or not all(c.isalnum() or c in ('_','-') for c in sym):
            stats['invalid_symbol']+=1;continue
        values={k:_number(item.get(k)) for k in NUMERIC}
        bids=[(values[f'bidPrice{i}'],values[f'bidVol{i}']) for i in (1,2,3)]
        bad=values['closePrice'] is None or values['closePrice']<=0
        if bad:
            stats['missing_last_price']+=1;continue
        # ATO/ATC, missing bid or zero volume are kept as nullable fields: not usable for exit planning.
        valid_bids=[(p,v) for p,v in bids if p is not None and v is not None and p>0 and v>0]
        if not valid_bids:stats['no_executable_bid']+=1
        if any(v is not None and (v<0 or abs(v-round(v))>1e-6) for p,v in bids):
            stats['invalid_bid_volume']+=1;continue
        row={'ts_vn':ts,'symbol':sym,'data_kind':data_kind,'timestamp_semantics':'received_at_vn',
             'source_channel':'stockInfo',**values}
        rows.append(row)
        stats['accepted']+=1
    if not rows:stats['messages_without_stock_row']+=1
    return rows,dict(stats)


def ingest_jsonl(source, out, quality_out, *, data_kind='historical', append=False):
    """Import raw NDJSON previously captured by authorized stream, never invent historical observations.

    Input line can be raw stockInfo dict, envelope or {received_at, message}.
    """
    source=Path(source);out=Path(out);quality_out=Path(quality_out)
    if not source.is_file():raise FileNotFoundError(source)
    count=Counter(); rows=[]
    with source.open('r',encoding='utf-8') as stream:
        for line_number,line in enumerate(stream,1):
            if not line.strip():continue
            count['messages']+=1
            try:
                payload=json.loads(line)
                if isinstance(payload,dict) and 'message' in payload and 'received_at' in payload:
                    timestamp=payload['received_at'];msg=payload['message']
                else:timestamp=None;msg=payload
                if timestamp is None and data_kind=='historical':
                    count['missing_capture_timestamp']+=1
                    continue  # Không tự gán hiện tại cho bản ghi đã lưu trong quá khứ
                normalized,stat=normalize_event(msg,timestamp,data_kind)
                rows.extend(normalized);count.update(stat)
            except (ValueError,TypeError,OverflowError) as exc:
                count['invalid_messages']+=1
    if not rows:
        raise ValueError('Không có snapshot hợp lệ. Đầu vào lịch sử bắt buộc có received_at cho mỗi message.')
    df=pd.DataFrame(rows)
    if append and out.exists():
        previous=pd.read_parquet(out)
        if set(previous['data_kind'])!={data_kind}:
            raise ValueError('Không được trộn synthetic/live/historical vào cùng một file')
        df=pd.concat([previous,df],ignore_index=True)
    df=df.sort_values(['ts_vn','symbol'])
    before=len(df)
    df=df.drop_duplicates(subset=['ts_vn','symbol'],keep='last')
    count['duplicate_rows']=before-len(df)
    out.parent.mkdir(parents=True,exist_ok=True)
    quality_out.parent.mkdir(parents=True,exist_ok=True)
    df.to_parquet(out,index=False)
    qa=[]
    for sym,g in df.groupby('symbol'):
        invalid_bid=g[['bidPrice1','bidVol1','bidPrice2','bidVol2','bidPrice3','bidVol3']].isna().all(axis=1)
        qa.append(dict(symbol=sym,records=len(g),missing_bid=int(invalid_bid.sum()),
                       duplicates=0,invalid_rows=0,missing_pct=float(invalid_bid.mean()*100),
                       duplicate_pct=0.,invalid_pct=0.,data_kind=data_kind))
    pd.DataFrame(qa).to_csv(quality_out,index=False,encoding='utf-8-sig')
    return dict(stats=dict(count),rows=len(df),symbols=int(df['symbol'].nunique()),
                sessions=int(df['ts_vn'].dt.date.nunique()),
                first=str(df['ts_vn'].min()),last=str(df['ts_vn'].max()))


def write_status(path,**details):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    safe={'timestamp_vn':now_vn().isoformat(),**details}
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(safe,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    os.replace(tmp,p)
