# SSI trực tuyến trong ExitPlan

Khởi chạy từ thư mục dự án bằng `py -m streamlit run src/app/app.py` trong cùng môi trường PowerShell đã cấu hình SSI_API_KEY và SSI_API_SECRET. Không nhập khóa vào UI, không commit khóa.

- Thanh bên: **Kết nối SSI**, **Ngắt kết nối SSI**, **Làm mới dữ liệu**.
- Ngoài khung thu thập (09:15–11:30, 13:00–14:30, lịch 2026): nút Kết nối kiểm tra xác thực token, không mở WebSocket và không tạo dữ liệu giả. Bấm kết nối lại trong phiên.
- Trong khung thu thập: mỗi đợt tối đa khoảng 60 giây / 50 MiB, WebSocket đăng ký quote/trade trên ba sàn. Bộ ghi mở lại kết nối giữa các đợt, sử dụng token hiện có; xác thực lại khi đợt kết nối lỗi. Không gọi API theo từng lần thao tác.
- Chỉ báo nhận bản tin cần có sự kiện gần nhất trong 20 giây và worker còn hoạt động. Trạng thái socket mở/chờ dữ liệu khác với đã nhận bản tin. Dữ liệu hiển thị là snapshot đã qua kiểm tra, không phải tick-by-tick; độ trễ gồm thời gian thu thập, chuẩn hóa và làm mới.
- Import sử dụng hệ số đang lưu trong bộ snapshot SSI hiện có, chế độ append, ghi file nguyên tử, khóa ghi giữa các importer. Các hệ số vẫn cần đối chiếu nguồn như trước. File gốc từng đợt nằm trong data/raw/ssi_ws; không ghi đè OHLCV hay kết quả thực nghiệm.
- Tổng quan cập nhật riêng mỗi 15 giây trong lúc worker hoạt động. Các trang khác cập nhật khi thao tác hoặc bấm Làm mới dữ liệu. Phương án cũ giữ timestamp và quote đã tính nếu snapshot đó không đổi; bấm Tính phương án để dùng dữ liệu mới.
- Dừng tại cuối khung thu thập, tối đa 90 phút mỗi lần chạy, hoặc sau 3 đợt thất bại liên tiếp. Không để bộ ghi dòng lệnh và worker dashboard cùng đăng ký thị trường; chỉ dùng một instance dashboard trên máy cá nhân. Worker dùng chung giữa các phiên trình duyệt của cùng server.
- Ngắt kết nối trước khi tắt Streamlit; đợi bộ ghi lưu xong. Nếu dừng tiến trình đột ngột, file raw đã ghi vẫn có thể được import thủ công bằng --input và --append.
- Không đặt lệnh thật. Kiểm thử offline không xác nhận quyền API, latency hoặc khả năng nhận sự kiện trong phiên thật.
