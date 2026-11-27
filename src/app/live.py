"""Dashboard controls and live status. Network operations stay in the worker."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import streamlit as st
from src.ingest.ssi_dashboard_live import DashboardLive
from src.ingest.ssi_dashboard_close import CloseWorker, market_phase, completed_date
import os

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
    phase=market_phase()
    text,tone=status_label(info)
    if os.getenv("EXITPLAN_SSI_AUTO","1")=="0":
        text,tone="Tự cập nhật đã tạm tắt","neutral"
    elif phase=="closed":
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
    if phase=="continuous" and info.get("last_event_vn"):
        st.caption("Bản tin: "+info["last_event_vn"].replace("T"," ")[:19])
    if info.get("last_snapshot_vn"):
        st.caption("Snapshot: "+info["last_snapshot_vn"].replace("T"," ")[:19])
    if phase=="closed":
        date=completed_date()
        if date:st.caption("Phiên tham chiếu: "+date.strftime("%d/%m/%Y"))
