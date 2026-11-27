# SSI tự động trong ExitPlan

Khởi chạy bằng `py -m streamlit run src/app/app.py` trong cùng môi trường PowerShell đã cấu hình SSI_API_KEY và SSI_API_SECRET. Không nhập khóa vào UI, không commit khóa.

- Không cần bấm kết nối, ngắt kết nối hoặc làm mới. Thanh bên kiểm tra trạng thái mỗi 5 giây và tự khởi động bộ ghi trong khung thu thập liên tục 09:15–11:30, 13:00–14:30 (UTC+7, lịch 2026).
- Mỗi đợt ghi tối đa khoảng 60 giây / 50 MiB, mở lại WebSocket giữa các đợt, dùng token hiện tại và xác thực lại khi gặp lỗi kết nối. Sau lỗi cuối cùng, tự thử lại với khoảng nghỉ 120 giây nếu vẫn trong phiên và có dashboard đang mở. Bộ ghi dừng ở cuối khung, sau tối đa 90 phút mỗi lượt hoặc khi không còn UI polling (kiểm tra lease ở ranh giới đợt). Không gọi API theo từng thao tác.
- Chỉ báo nhận bản tin cần có sự kiện mới trong 20 giây và worker đang hoạt động. Dữ liệu giá hiển thị là snapshot đã qua kiểm tra, không phải tick-by-tick. Nếu snapshot chung quá 120 giây trong phiên, hiển thị cảnh báo; ngoài giờ chỉ mô phỏng trên sổ lệnh đã ghi.
- Nghỉ trưa và giai đoạn đầu/cuối phiên: sử dụng snapshot gần nhất. Sau 15:15 UTC+7, trước giờ mở cửa, ngày nghỉ: lấy OHLCV ngày của phiên đã hoàn thành gần nhất cho các mã đang xem hoặc nắm giữ. 15:15 là buffer vận hành, không phải tuyên bố SSI luôn hoàn tất dữ liệu đúng giờ đó. REST chưa trả giá đúng phiên thì hiển thị giá ngày cũ có ghi ngày hoặc thiếu dữ liệu; thử lại sau 5 phút, không tự tạo giá.
- Giá đóng cửa lưu riêng tại data/processed/ssi_dashboard_closes.parquet, giữ nguyên đơn vị API. Không đưa giá đóng cửa vào sổ lệnh, không thay giá tham chiếu dùng trong MILP hay thay file OHLCV phục vụ ADV20/Sigma20.
- Tổng quan và bảng giá tham chiếu cập nhật riêng mỗi 15 giây. Trang lập phương án đọc snapshot mới khi thao tác; các phương án đã tính giữ timestamp và quote gốc nếu không thay đổi. Tính lại để dùng snapshot chung mới.
- Import dùng hệ số hiện có và chế độ append, ghi file nguyên tử, khóa ghi giữa các importer. File raw được lưu riêng. Không ghi đè OHLCV hoặc kết quả thực nghiệm.
- Chỉ dùng một instance dashboard trên máy cá nhân. Nếu muốn thu thập bằng terminal, tắt dashboard hoặc đặt `$env:EXITPLAN_SSI_AUTO="0"` trước khi khởi chạy Streamlit. Đặt lại `$env:EXITPLAN_SSI_AUTO="1"` để bật tự động. Không chạy đồng thời bộ ghi thủ công với worker tự động.
- Khi đóng dashboard, nếu tiến trình bị dừng đột ngột, file raw có thể import thủ công bằng --input và --append. Không đặt lệnh thật.
- Lịch tự động hiện chỉ hỗ trợ 2026; cần cập nhật lịch khi sang năm. Kiểm thử offline không xác nhận quyền API, độ trễ hoặc nhận sự kiện thực tế.
