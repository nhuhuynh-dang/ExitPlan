# Kết nối SSI FastConnect V3 (Market Data chỉ đọc)

> Trạng thái hiện tại: đang chờ SSI cấp quyền. Những script dưới đây **chưa xác nhận**
> kết nối được với tài khoản của bạn. Không lưu API Key/Secret vào GitHub.

## 1. Xin cấp quyền và kiểm tra kích hoạt

1. Đăng nhập <https://developers.ssi.com.vn/> → **Bảng điều khiển**.
2. Tìm **Quản lý API Key** và trạng thái dịch vụ FastConnect/Market Data.
3. Nếu thấy nút tạo key và dịch vụ đã kích hoạt, chọn key dành riêng cho **ExitPlan**, chỉ
   cấp **quyền đọc Market Data** (không chọn Trading, không cần OTP đặt lệnh).
4. Nếu chỉ thấy mẫu *“Đăng ký trải nghiệm FastConnect V3”* hoặc trạng thái đang xét
   duyệt, chưa thể lấy token. Đăng ký một lần, theo dõi email và liên hệ SSI:
   **1900 54 54 71** để xác minh tài khoản và quyền Market Data.
5. SSI có tài liệu mô tả đăng ký tự phục vụ qua portal, nhưng trang Registration
   cũng hướng dẫn liên hệ SSI/chi nhánh để kích hoạt: trạng thái thực tế trong
   tài khoản và phản hồi SSI là căn cứ cuối cùng.

Tài liệu chính thức:
- <https://developers.ssi.com.vn/docs/getting-started/registration>
- <https://developers.ssi.com.vn/docs/getting-started/api-keys>
- <https://developers.ssi.com.vn/docs/api-reference/auth-token>
- <https://developers.ssi.com.vn/docs/api-reference/data-securitiesByBoard>
- <https://developers.ssi.com.vn/docs/api-reference/data-ohlc>
- <https://developers.ssi.com.vn/docs/api-reference/subscribeUnsubscribeMarketData>

## 2. Chuẩn bị môi trường (PowerShell / VS Code)

Trong thư mục gốc ExitPlan:

```powershell
git pull origin main
py -m pip install -r requirements.txt
py scripts/ssi_v3_sync.py --check
```

Nếu chưa có key, script chỉ báo **CHƯA CÓ API** và không ghi dữ liệu. Đây là hành
vi đúng, không phải lỗi của dashboard.

**Sau khi SSI thực sự cấp key**, cấu hình **trong Terminal của máy riêng**, không
dán vào chat, không đưa vào file tracked, không chụp màn hình chứa khóa:

```powershell
$env:SSI_API_KEY = "KEY_DO_SSI_CAP"
$env:SSI_API_SECRET = "SECRET_DO_SSI_CAP"
py scripts/ssi_v3_sync.py --check
```

Script chỉ gọi:
- `POST https://api.ssi.com.vn/api/v3/auth/token` với apiKey/apiSecret, **không truyền OTP**;
- `GET /api/v3/data/securitiesByBoard?board=HOSE|HNX|UPCOM`.

Kết nối thất bại (401/403/429) sẽ dừng và không gán nhãn dữ liệu thật giả.
Token chỉ được giữ trong RAM của script. Script không đặt, sửa hoặc hủy lệnh.

## 3. Lấy danh sách toàn bộ mã cổ phiếu được tài khoản SSI hỗ trợ

```powershell
py scripts/ssi_v3_sync.py --catalog
```

Khi có quyền, file tạo ra:
`data/processed/ssi_securities.parquet`, với cột mã, sàn, tên, lô giao dịch.
Số mã thực tế phụ thuộc vào kết quả API, loại chứng khoán và quyền tài khoản.

## 4. Tải OHLCV chính thức và tính ADV 20 phiên

```powershell
py scripts/ssi_v3_sync.py --history --symbols HPG VPB ACB --from-date 01/09/2026 --to-date 20/11/2026
```

File tạo ra nếu **tất cả mã** có dữ liệu hợp lệ:

- `data/raw/ssi_fastconnect_v3_ohlcv.csv` (bản gốc đã chuẩn hóa);
- `data/processed/ssi_history.parquet` (trang SSI của dashboard đọc);
- `outputs/tables/ssi_liquidity_stats.parquet` (ADV và độ lệch chuẩn lợi suất).

Trường `data_kind=historical` và `source=ssi_fastconnect_v3` giúp truy vết nguồn.
Thời gian theo ngày, OHLCV giữ nguyên **đơn vị giá SSI trả về**; không tự quy đổi
sang VND khi chưa xác minh. ADV là khối lượng cổ phiếu/ngày, chỉ báo cáo khi đủ
20 phiên mỗi mã.

**Cực kỳ quan trọng:** các nến OHLCV không chứa `bidPrice1..3`,
`bidVol1..3`. Script V3 **không ghi đè**
`data/processed/book_snapshots.parquet` và **không tự tạo sổ lệnh**. Mô hình
thanh lý chỉ tính khi đã có snapshot giá mua/khối lượng mua thật được xác minh.

## 5. Sau khi kết nối lịch sử: bổ sung real-time order book

SSI FastConnect V3 Market Data WebSocket sử dụng `wss://stream.ssi.com.vn`;
topic `quote.<MÃ>` mang thông tin bid/ask. Cần:

1. Quyền WebSocket DATA/quote từ SSI và schema/đơn vị giá, khối lượng thực tế;
2. Script ghi **thô** message có timestamp lúc nhận, rồi mới ánh xạ bid/ask;
3. Kiểm tra khối lượng ba mức, mã sàn, ATO/ATC, stale quotes và dữ liệu rỗng;
4. Lưu snapshot đã chuẩn hóa, có nhãn `data_kind=live` và nguồn `ssi_fastconnect_v3`;
5. Thu thập nhiều phiên giao dịch trước khi thử nghiệm & đánh giá.

Cần đối chiếu schema quote nhận từ kết nối **thực** trước khi xây converter;
không được suy ra ba mức bid bằng giá đóng cửa hay dữ liệu giả lập.

## 6. Lỗi thường gặp

- **Không có key:** SSI chưa kích hoạt Market Data → dùng --check và chờ quyền.
- **401/403:** xác thực, key, quyền hoặc môi trường chưa đúng → kiểm tra portal/liên hệ SSI.
- **429:** chạm rate limit → giảm tần suất; script dừng, không bypass.
- **HTTP 400 endpoint iBoard cộng đồng:** đó **không phải** bằng chứng FastConnect V3 lỗi.
  Không tiếp tục phụ thuộc `statistics/company/ssmi/stock-info` cho dự án.
- **Có lịch sử nhưng không có phương án:** đó là đúng vì chưa có sổ lệnh quote.
- **Thiếu pyarrow:** chạy `py -m pip install -r requirements.txt`.

Không commit file `.env`, `secrets.toml`, token, file raw nhạy cảm hoặc thông tin tài khoản.
