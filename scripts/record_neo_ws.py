"""Bộ ghi stockInfo raw -> NDJSON; không giao dịch, không đọc tài khoản.

Yêu cầu NEO_WS_URL=wss://... và cấu hình xác thực đúng theo tài liệu/khả năng tài khoản.
Không tự giả định rằng JWT trong header là quy trình xác thực WebSocket chính thức.
Lưu ý endpoint ws:// trong tài liệu là không mã hóa; script từ chối gửi JWT qua ws://.
"""
import argparse,asyncio,json,os,sys,time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.ingest.pipeline import write_status
from websockets.asyncio.client import connect
VN=ZoneInfo('Asia/Ho_Chi_Minh')

def _json_env(key):
    raw=os.environ.get(key)
    if not raw:return None
    return json.loads(raw)

async def record(url,symbols,out,status,duration=1800):
    if not url.startswith('wss://'):
        raise ValueError('Chỉ cho phép wss:// khi cấu hình xác thực; ws:// không mã hóa JWT. TODO: xác minh endpoint TLS chính thức với VPBankS.')
    header_name=os.environ.get('NEO_WS_TOKEN_HEADER','Authorization')
    token=os.environ.get('NEO_JWT')
    headers={header_name:'Bearer '+token} if token else {}
    # Một số dịch vụ dùng thông điệp xác thực riêng: truyền NEO_WS_AUTH_MESSAGE theo tài liệu đã xác minh.
    auth=_json_env('NEO_WS_AUTH_MESSAGE')
    if auth is None and not token:
        raise ValueError('Thiếu xác thực. Cần NEO_JWT hoặc NEO_WS_AUTH_MESSAGE đã kiểm chứng từ tài liệu.')
    out.parent.mkdir(parents=True,exist_ok=True)
    ids=[s.strip().upper() for s in symbols if s.strip()]
    if not ids:raise ValueError('Cần ít nhất một mã cổ phiếu')
    write_status(status,state='connecting',channel='stockInfo',records=0)
    n=0
    try:
        async with connect(url,additional_headers=headers,ping_interval=20,open_timeout=15,max_size=2**20) as ws:
            if auth is not None:
                # NOTE: authentication success/ack protocol unknown; user must validate credentials and ack.
                await ws.send(json.dumps(auth,ensure_ascii=False))
            await ws.send(json.dumps({'type':'sub','channel':'stockInfo','listId':ids}))
            write_status(status,state='connected_unverified_auth',channel='stockInfo',symbols=ids,records=0,
                         message='Socket đã mở. Cần xác minh server đã xác thực và trả stockInfo.')
            deadline=time.monotonic()+duration
            with out.open('a',encoding='utf-8') as f:
                while time.monotonic()<deadline:
                    try:message=await asyncio.wait_for(ws.recv(),timeout=min(30,max(.1,deadline-time.monotonic())))
                    except asyncio.TimeoutError:continue
                    stamp=datetime.now(VN).isoformat(timespec='milliseconds')
                    try:parsed=json.loads(message)
                    except (ValueError,TypeError):continue
                    # Never persist auth messages, raw token or suspected authorization fields.
                    if isinstance(parsed,dict) and any(k.lower() in ('token','jwt','authorization','access_token','refresh_token') for k in parsed):
                        continue
                    # Only stockInfo rows: other control/ack messages are not recorded.
                    from src.ingest.pipeline import _records
                    records=list(_records(parsed))
                    if not records:continue
                    for row in records:
                        f.write(json.dumps({'received_at':stamp,'message':{'channel':'stockInfo','data':row}},ensure_ascii=False)+'\n')
                        n+=1
                    f.flush()
                    write_status(status,state='receiving_stockinfo',channel='stockInfo',records=n,last_update_vn=stamp,
                                 symbols=ids,message='Đang nhận sự kiện stockInfo; chưa xác nhận đầy đủ chất lượng dữ liệu.')
            await ws.send(json.dumps({'type':'unsub','channel':'stockInfo','listId':ids}))
        write_status(status,state='stopped',channel='stockInfo',records=n)
    except Exception as exc:
        write_status(status,state='error',channel='stockInfo',records=n,error_type=type(exc).__name__,
                     message='Kết nối không thành công. Kiểm tra IP whitelist, TLS và quy trình xác thực.')
        raise
    return n

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--symbols',nargs='+',required=True)
    p.add_argument('--minutes',type=float,default=30)
    p.add_argument('--output',default='data/raw/neo_stockinfo.jsonl')
    a=p.parse_args()
    url=os.environ.get('NEO_WS_URL','')
    try:
        n=asyncio.run(record(url,a.symbols,ROOT/a.output,ROOT/'outputs/tables/recorder_status.json',int(a.minutes*60)))
        print(f'Đã ghi {n} bản ghi stockInfo vào {a.output}')
    except Exception as exc:
        print(f'Chưa ghi được: {type(exc).__name__}: {exc}',file=sys.stderr);sys.exit(1)
