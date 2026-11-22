# ExitPlan v4 – sửa giao diện

- Thay nhãn `:material/...:` trong `st.radio` bằng emoji hiển thị trực tiếp; Streamlit không render shortcode icon trong nhãn radio.
- Giới hạn lại CSS sidebar, không áp `color` lên mọi node con; bổ sung trạng thái chọn và brand header.
- Bỏ can thiệp cỡ chữ gốc `html` khiến các control khó dự đoán.
- Chuẩn hóa giá trên biểu đồ Tổng quan về gốc 100 để so sánh các mã có mệnh giá khác nhau (chỉ thay hiển thị, không ghi đè dữ liệu).
- Xóa tiêu đề Chất lượng dữ liệu trùng.
- Thêm `pytest.ini` để chạy kiểm thử khi đứng trong thư mục dự án.

Chưa xác nhận render trên trình duyệt trong môi trường tạo file; nếu thấy layout sai ở bản Streamlit cụ thể, gửi ảnh và phiên bản `py -m streamlit version`.
