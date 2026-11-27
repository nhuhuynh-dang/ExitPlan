"""Dashboard controls and live status. Network operations stay in the worker."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import streamlit as st
from src.ingest.ssi_dashboard_live import DashboardLive, operator_live_enabled
from src.ingest.ssi_dashboard_close import CloseWorker, market_phase, completed_date

VN=timezone(timedelta(hours=7))

@st.cache_resource(show_spinner=False)
def _controller(root):
    return DashboardLive(root)

def controller(root):
    return _controller(str(Path(root).resolve()))


def status_label(info,now=None):
    state=info.get("state","idle")
    if state=="receiving_stockinfo":
        try:
            stamp=datetime.fromisoformat(info["last_event_vn"])
            age=((now or datetime.now(VN))-stamp).total_seconds()
            if info.get("active") and 0<=age<=20:return "Đang nhận bản tin SSI","success"
        except (ValueError,TypeError,KeyError):pass
        return "Chưa có bản tin mới","warning"
    labels={
        "idle":("Dữ liệu đã lưu","neutral"),
        "authenticating":("Đang xác thực SSI","neutral"),
        "connecting":("Đang mở WebSocket","neutral"),
        "connected_unverified_auth":("Socket đã mở · chờ dữ liệu","neutral"),
        "subscribed_no_data":("Đã đăng ký · chờ dữ liệu","neutral"),
        "importing":("Đang chuẩn hóa snapshot","neutral"),
        "retrying":("Đang thử kết nối lại","warning"),
        "stopping":("Đang dừng và lưu dữ liệu","neutral"),
        "stopped":("Đã dừng · dữ liệu đã lưu","neutral"),
        "outside_hours":("Ngoài giờ thu thập","neutral"),
        "missing_credentials":("Chưa có khóa API trong môi trường","warning"),
        "error":("Chưa kết nối / xử lý thành công","warning"),
    }
    return labels.get(state,("Chưa xác nhận","neutral"))


@st.cache_resource(show_spinner=False)
def _close_controller(root):
    return CloseWorker(root)


def close_controller(root):
    return _close_controller(str(Path(root).resolve()))


@st.fragment(run_every=5)
def sidebar_live(root):
    worker=controller(root)
    worker.auto_tick()
    info=worker.snapshot()
    if not operator_live_enabled():
        st.markdown("**Dữ liệu thị trường**")
        st.caption("Dữ liệu đã lưu · Không cần API cá nhân")
        try:
            from src.app.pages import _market_parquet
            books,_=_market_parquet(root,"data/processed/ssi_book_snapshots.parquet")
            if books is not None and not books.empty and set(books.source)=={"ssi_fastconnect_v3_ws"} and set(books.data_kind)=={"live"}:
                st.caption("Snapshot SSI: "+str(books.ts_vn.max())[:19]+" (UTC+7)")
        except (ValueError,KeyError,TypeError,OSError):
            pass
        return
    phase=market_phase()
    text,tone=status_label(info)
    if phase=="closed":
        text,tone="Ngoài giờ giao dịch · giá đóng cửa","neutral"
    elif phase=="lunch":
        text,tone="Nghỉ trưa · snapshot gần nhất","neutral"
    elif phase=="transition":
        text,tone="Đầu/cuối phiên · snapshot gần nhất","neutral"
    elif phase=="calendar_unknown":
        text,tone="Chưa có lịch giao dịch đã kiểm chứng","warning"
    elif not info.get("active") and tone=="neutral":
        text,tone="Chờ kết nối tự động · dữ liệu đã lưu","warning"
    st.markdown("**SSI FastConnect V3**")
    icon={"success":"🟢","warning":"🟠","neutral":"⚪"}[tone]
    st.caption(icon+" "+text)
    if phase=="continuous" and info.get("failure_stage") and info.get("state") in ("error","retrying"):
        stage={"auth":"Xác thực SSI","stored_data":"Dữ liệu đầu vào","websocket":"Nhận bản tin","import":"Chuẩn hóa snapshot"}.get(info["failure_stage"],"Chưa xác định")
        st.caption("Khâu cần kiểm tra: "+stage)
    if phase=="continuous" and info.get("last_event_vn"):
        st.caption("Bản tin: "+info["last_event_vn"].replace("T"," ")[:19])
    if info.get("last_snapshot_vn"):
        st.caption("Snapshot: "+info["last_snapshot_vn"].replace("T"," ")[:19])
    if phase=="closed":
        date=completed_date()
        if date:
            st.caption("Phiên tham chiếu: "+date.strftime("%d/%m/%Y"))
            if not info.get("active"):
                try:
                    from src.app.pages import _market_parquet, _daily_history
                    from src.ingest.ssi_dashboard_close import missing_daily_symbols
                    books,_=_market_parquet(root,"data/processed/ssi_book_snapshots.parquet")
                    if books is not None and not books.empty and set(books.source)=={"ssi_fastconnect_v3_ws"} and set(books.data_kind)=={"live"}:
                        missing=missing_daily_symbols(_daily_history(root),books.symbol.unique(),date)
                        close_controller(root).request(missing,date,bulk=True)
                        st.caption("OHLCV phiên gần nhất: "+str(len(missing))+" mã còn thiếu")
                except (ValueError,KeyError,TypeError,OSError):
                    st.caption("Chưa kiểm tra được độ phủ OHLCV.")
