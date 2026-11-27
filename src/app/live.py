"""Dashboard controls and live status. Network operations stay in the worker."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import streamlit as st
from src.ingest.ssi_dashboard_live import DashboardLive

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


@st.fragment(run_every=5)
def sidebar_live(root):
    worker=controller(root)
    info=worker.snapshot()
    text,tone=status_label(info)
    # Native text and controls remain readable in both themes.
    st.markdown("**SSI FastConnect**")
    icon={"success":":material/check_circle:","warning":":material/warning:","neutral":":material/sensors:"}[tone]
    st.caption(text)
    if info.get("rest_verified"):
        st.caption("Đã xác thực token Market Data trong lần chạy này.")
    if info.get("last_event_vn"):
        st.caption("Bản tin: "+info["last_event_vn"].replace("T"," ")[:19])
    if info.get("last_snapshot_vn"):
        st.caption("Snapshot đã lưu: "+info["last_snapshot_vn"].replace("T"," ")[:19])
    if info.get("active"):
        if st.button("Ngắt kết nối SSI",key="ep_live_stop",icon=":material/stop:",use_container_width=True,
                     disabled=info.get("state")=="stopping"):
            worker.stop()
            st.rerun()
    else:
        if st.button("Kết nối SSI",key="ep_live_start",icon=icon,use_container_width=True):
            worker.start()
            st.rerun()
    if st.button("Làm mới dữ liệu",key="ep_live_refresh",icon=":material/refresh:",use_container_width=True):
        st.rerun()
