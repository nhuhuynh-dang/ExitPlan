# ExitPlan – Dashboard phân tích thanh lý danh mục

Giao diện Streamlit thuần **chỉ đọc file**, không gọi API, không truy cập tài khoản, không gửi lệnh. `src/analytics/planner.py` là bộ tính MILP thuần được giao diện gọi **chỉ khi nhấn “Tính phương án”**. Người dùng nhập thủ công mã và số lượng; dashboard dùng ảnh chụp ba mức giá mua đã lưu.

## SSI FastConnect V3 — nguồn dữ liệu chính thức

Khi SSI phê duyệt Market Data **read-only**, ExitPlan có sẵn script chuẩn:
`scripts/ssi_v3_sync.py`. Script hỗ trợ kiểm tra token, lấy danh sách toàn bộ mã HOSE/HNX/UPCOM,
tải OHLCV lịch sử và tính ADV, không đụng đến API giao dịch.

```powershell
py scripts/ssi_v3_sync.py --check
# Sau khi SSI cấp API Key/Secret và bạn đã đặt chúng qua $env: trong PowerShell:
py scripts/ssi_v3_sync.py --catalog
py scripts/ssi_v3_sync.py --history --symbols HPG VPB ACB --from-date 01/09/2026 --to-date 20/11/2026
```

**Chưa được cấp quyền thì --check chỉ báo trạng thái và KHÔNG tạo dữ liệu.**
Để xem thủ tục xin quyền, bảo vệ key và ý nghĩa từng file:
**[Hướng dẫn SSI FastConnect V3](docs/SSI_FASTCONNECT_SETUP.md)**.

OHLCV của SSI không phải snapshot bid/ask. Trang Lập phương án vẫn cần
dữ liệu quote real-time được SSI cấp quyền, kiểm tra schema và ghi riêng theo phiên.
Giao diện không tự giao dịch. Không đưa API Key, Secret hay token vào GitHub.

## Cài và chạy (Windows PowerShell)

```powershell
py -m pip install -r requirements.txt
py scripts/generate_synthetic.py
py -m pytest -q
py -m streamlit run src/app/app.py
```

Các file trong `data/` và `outputs/` được **sinh riêng bởi script**. Script phát sinh *dữ liệu giả lập có nhãn `data_kind="synthetic"`*, không được trình bày như dữ liệu thị trường thực. Trước khi chạy `generate_synthetic.py`, dashboard sẽ thông báo thiếu dữ liệu thay vì dùng fixture tự động. Để tùy chỉnh đường dẫn file, truy cập giao diện bằng URL có query `?advanced=1`.

## Các trang

Tổng quan · Lập phương án · So sánh phương án · Thanh khoản các mã · Dữ liệu & kết nối · Kiểm chứng · Phương pháp & giới hạn · Tải dữ liệu.

## Danh sách đầu vào cần có

| Đường dẫn | Trường chính | Bắt buộc |
|---|---|---|
| `data/processed/book_snapshots.parquet` | `ts_vn, symbol, bidPrice1..3, bidVol1..3, closePrice, totalTradingVolume, data_kind` | Có |
| `outputs/tables/liquidity_stats.parquet` | `symbol, adv, sigma, n_sessions, data_kind` | Tùy chọn; cần để tính π |
| `outputs/tables/plans.parquet` | `phuong_an, net, liquidity_cost, cost_bps, hhi, data_kind` | Tùy chọn; bản lưu chỉ để tham chiếu |
| `outputs/tables/frontier.parquet` | `lamb, net, cost, hhi, data_kind` | Tùy chọn |
| `outputs/tables/data_quality.csv` | `symbol, records, missing_pct, duplicate_pct, invalid_pct, data_kind` | Tùy chọn |
| `outputs/tables/validation_*.csv` | Bảng thử độ nhạy / replay đã tính bên ngoài | Tùy chọn |
| `outputs/tables/recorder_status.json` | `state, channel, last_update_vn, data_kind` | Tùy chọn |
| `outputs/tables/test_results.csv` | Báo cáo kiểm thử được ghi ngoài app | Tùy chọn; không sinh kết quả giả |

Nếu chưa có PyArrow: `py -m pip install pyarrow`. Các file `.parquet` được tạo bởi `generate_synthetic.py` khi đã cài requirements.

## Các lưu ý tài chính

- A giảm chi phí thanh khoản theo giá gần nhất; C giảm tổng bình phương giá trị tài sản còn lại; B lấy tổ hợp chuẩn hóa A/C với trọng số λ (hệ số tỉ lệ kỹ thuật 15); P xấp xỉ tỷ lệ bán danh mục.
- **HHI thực được tính sau nghiệm**; MILP dùng proxy tổng bình phương giá trị còn lại. Bài toán nguyên rời rạc theo lô `100` CP, giới hạn 12 mã, cần hội tụ của bộ giải; có thể xảy ra không đạt nghiệm trong thời gian giới hạn.
- Các lệnh lớn hơn độ sâu ba mức bid **không được định giá một giá khớp duy nhất**. Bảng khoảng bi quan–lạc quan chỉ là hai kịch bản có điều kiện; cận lạc quan giả định khối lượng vượt độ sâu bán được ở giá gần nhất, không phải bound chắc chắn của thị trường.
- `adv` phải do pipeline bên ngoài tính từ dữ liệu đủ số phiên và chuẩn đơn vị. Nếu không có ADV, tỷ lệ tham gia hiển thị `–`.
- Chế độ `synthetic` được gắn badge cảnh báo; dashboard không tự trộn nguồn `live/historical/synthetic`.
- Trang dữ liệu *không tự mở WebSocket*. Phần thu thập và lưu dữ liệu NEO thật cần một pipeline/recorder riêng, với xác thực, quản lý IP, rate-limit và lưu trữ trước khi nộp.
- `fee_rate_default`, `tax_rate_default`, `impact_coefficient` trong `config.json` cố ý là `null` cho đến khi được xác minh. Giao diện mặc định 0% và cho nhập giả định.
- **TODO về NEO:** xác minh số lượng đơn vị cổ phiếu, giá hiển thị và các trường khi ATO/ATC, mapping trong `src/data/schema.py`; xử lý giá string và `null` trước khi tạo Parquet.
- Trình mô phỏng này không triển khai đặt lệnh thật, xác suất khớp, thời gian xếp hàng hoặc market impact động.

## Cấu trúc

- `src/app/app.py`: cấu hình Streamlit, thanh bên và điều hướng.
- `src/app/theme.py`: pastel dark/light, CSS, SVG tự vẽ.
- `src/app/pages.py`: 8 trang, thiếu dữ liệu báo rõ.
- `src/app/components.py`: KPI cards, badge, bảng HTML, verdict, guide.
- `src/app/charts.py`: Plotly, tùy biến màu theo theme, xuất PNG.
- `src/app/fmt.py`: định dạng số Việt Nam.
- `src/data/schema.py`, `repository.py`: schema và đọc/chuẩn hóa file.
- `src/finance/engine.py`: mô phỏng độ sâu ba mức bid và khoảng vượt độ sâu.
- `src/analytics/planner.py`: MILP, phương án A/B/C/P và frontier.
- `scripts/generate_synthetic.py`: dữ liệu giả lập riêng có nhãn.
- `tests/`: kiểm thử hàm định dạng, HTML và tính toán.

**Công cụ phân tích học thuật, không phải khuyến nghị đầu tư.**


## Sửa giao diện v5
- Navigation sử dụng ký tự Unicode thay vì cú pháp `:material/...:`; khởi động lại đúng thư mục v5 để không còn menu cũ.
- Không dùng CSS ép font trên `button`, tránh làm Streamlit hiện tên biểu tượng Material dưới dạng chữ (`keyboard_double_arrow`, `arrow_right`, ...).
- Tăng kích thước chữ menu và bảng, điều chỉnh độ rộng sidebar, giữ màu pastel, Sáng/Tối.
- Khi thấy giao diện bản cũ: dừng mọi Streamlit đang chạy bằng Ctrl+C, mở terminal đúng thư mục v5 rồi chạy `py -m streamlit run src/app/app.py`; nhấn Ctrl+Shift+R để tải lại cache trình duyệt.
- Chế độ demo vẫn là synthetic. Không sử dụng dữ liệu này để chứng minh NEO API hoạt động thật.

## Bổ sung backend v6 — phần cốt lõi (chưa cần JWT)

**Mục tiêu:** thu thập/lưu dữ liệu `stockInfo` NEO có timestamp lúc nhận, kiểm tra chất lượng,
ước tính thanh khoản từ các phiên đã lưu, phát lại các snapshot và kiểm tra phương án MILP.
Streamlit vẫn **chỉ đọc** file; không gửi lệnh chứng khoán hoặc gọi NEO từ giao diện.

### Quy trình thử bằng dữ liệu mẫu hiện có

```powershell
py -m pip install -r requirements.txt
py scripts/generate_synthetic.py
py -m pytest -q
py scripts/validate_recorded.py --holdings HPG:5000 VPB:4000 ACB:3000 --target 100000000 --fee 0.0015 --tax 0.001
py -m streamlit run src/app/app.py
```

Tài liệu thử nghiệm trên dữ liệu synthetic chỉ kiểm tra **đúng chức năng**, không phải chứng minh
độ chính xác giao dịch ngoài thị trường.

### Khi có bản ghi stockInfo được thu từ kết nối hợp lệ

```powershell
py scripts/import_captured.py --input data/raw/neo_stockinfo.jsonl --kind live
py scripts/build_liquidity_stats.py --min-sessions 5
py scripts/validate_recorded.py --holdings HPG:5000 VPB:4000 --target 100000000
```

Raw NDJSON mỗi dòng: `{"received_at":"2026-11-18T09:31:05+07:00","message":{"channel":"stockInfo","data":{...}}}`.
`received_at` là **giờ máy ghi nhận sự kiện**, không phải thời điểm khớp lệnh do Sở công bố.
`--kind historical` dùng cho bản ghi lưu trữ quá khứ có timestamp; `live` cho log do recorder nhận mới;
`synthetic` chỉ dùng thử. Import không tự chuyển sang dữ liệu giả định khi có lỗi.

**Quan trọng:** Chạy `generate_synthetic.py` sẽ **ghi đè** bộ dữ liệu hiện có! Trước khi nhập dữ liệu thật,
hãy sao lưu `data/processed/` và `outputs/tables/`, hoặc làm việc trên bản sao thư mục dự án.
Để không lẫn nguồn, importer từ chối append khác nhãn `data_kind`.

### Bộ ghi WebSocket tách riêng (chưa được xác thực live)

`scripts/record_neo_ws.py` ghi NDJSON từ luồng `stockInfo`, không tự động tạo Parquet.
Sau khi có quyền NEO API, phải xác minh **endpoint TLS WSS chính thức**, IP whitelist và
cách xác thực WebSocket từ nhà cung cấp. Các cấu hình minh họa:

```powershell
$env:NEO_WS_URL="wss://<endpoint-TLS-duoc-VPBankS-xac-nhan>"
$env:NEO_JWT="<token-luu-cuc-bo-khong-chia-se>"
py scripts/record_neo_ws.py --symbols HPG VPB ACB --minutes 30
py scripts/import_captured.py --input data/raw/neo_stockinfo.jsonl --kind live
```

**TODO thực tế:** Tài liệu mà nhóm đã đọc ghi `ws://neoapi.vpbanks.com.vn/stock-stream/broker`,
không cho thấy chắc chắn endpoint `wss://` hay handshake JWT. Code **không tự suy đoán**
URL TLS; không gửi token qua WebSocket không mã hóa. Nếu VPBankS chỉ hỗ trợ `ws://`,
phải xác nhận phương án truy cập an toàn với nhà cung cấp, không bỏ chặn để gửi bí mật.
Kết nối được socket chưa chứng minh đã đăng ký thành công: cần nhận dữ liệu `stockInfo` hợp lệ.

`NEO_WS_AUTH_MESSAGE` (JSON) có thể được dùng cho cơ chế xác thực bằng message *nếu được tài liệu chính thức xác nhận*.
Không commit JWT, mật khẩu hoặc địa chỉ IP vào Git; không cho phép đặt lệnh thật.

### Chất lượng dữ liệu và giới hạn phương pháp

- `src/ingest/pipeline.py`: lọc sai kiểu (`ATO`/`ATC`), âm/NaN, từ chối trộn dữ liệu, xóa lặp `ts_vn+symbol`.
- `src/analytics/liquidity.py`: `adv` và `sigma` trả thiếu (`NaN`) khi chưa đủ 5 phiên. Nếu
  chỉ ghi một phần phiên, ADV chỉ là **proxy khối lượng lũy kế tới snapshot cuối**, không gọi ADV toàn phiên.
- `src/analytics/validation.py`: phát lại chỉ trên ảnh chụp **đủ đồng thời các mã**; không nội suy
  báo giá cũ, không giả mạo tỷ lệ khớp lệnh. `validation_replay_summary.json` báo thống kê ổn định.
- Mô hình MILP hiện tại dùng mục tiêu tập trung **proxy**, không tối ưu HHI chính xác. 3 mức bid
  là giả định thực hiện tại thời điểm chụp, chưa tính market impact ngoài phạm vi quan sát.
- `scripts/example_capture.jsonl` chỉ là minh họa định dạng và **dữ liệu giả định**, không phải log NEO thật.

Bộ thư viện ghi live dùng `websockets>=15,<17` (thêm trong requirements). Kết quả triển khai
live phụ thuộc xác thực/được cấp quyền của VPBankS và **chưa được kiểm thử kết nối thực tế**.

## SSI iBoard endpoint cộng đồng (chỉ để tham khảo lịch sử, có thể không còn hoạt động)

Bản này bổ sung **mã nguồn thật để tải và lưu** dữ liệu SSI iBoard theo tài liệu cộng đồng:
https://github.com/anhtri04/vnstock-java-kbs/blob/main/docs/SSI_API_DOCUMENTATION.md

**Không phải SSI FastConnect chính thức** và endpoint cộng đồng có thể trả `400/403` hoặc thay đổi. Không vượt bảo vệ truy cập; không tự thay dữ liệu trống bằng số giả. Tài liệu tác giả ghi thử ngày 02/06/2026, không bảo đảm hiện vẫn truy cập được.

Chạy tại thư mục có `requirements.txt`:

```powershell
py -m pip install -r requirements.txt
py scripts/fetch_ssi_history.py --symbols HPG VPB ACB --from-date 01/09/2026 --to-date 20/11/2026
py -m streamlit run src/app/app.py
```

Mở trang **SSI · Dữ liệu lịch sử** để xem giá đóng cửa và ADV. Script xuất:
- `data/raw/ssi_iboard_ohlcv.csv` (UTF-8 BOM)
- `data/processed/ssi_history.parquet`
- `outputs/tables/ssi_liquidity_stats.parquet` (ADV 20 phiên, độ lệch chuẩn lợi suất)

Tệp `book_snapshots.parquet` **không** bị ghi đè, nhằm bảo toàn ranh giới giữa OHLCV và sổ lệnh. Nếu muốn trình diễn các trang tối ưu khi chưa có bid/ask thực, chạy `py scripts/generate_synthetic.py` **trước** để tạo dữ liệu demo có nhãn synthetic. Lệnh synthetic có thể ghi đè dữ liệu sổ lệnh đang lưu, không chạy nó trên bản đã ghi thị trường thật.

**Giới hạn:** Chỉ có giá/volume theo ngày, không có WebSocket hay độ sâu bid 3 tầng. Dữ liệu SSI được gắn `source=ssi_iboard_community_doc`, `data_kind=historical`. Không được trình bày phần tối ưu dùng demo là kết quả ứng dụng sổ lệnh thật. Nếu API trả lỗi HTTP 400, lỗi từ máy chủ có thể do tham số, quyền hoặc thay đổi API; chương trình không suy đoán nguyên nhân và không ghi đè lịch sử cũ khi tất cả yêu cầu thất bại.

## SSI V3 — quy trình sổ lệnh mới (HOSE, dữ liệu chỉ đọc)

REST đã được người dùng kiểm tra: 2226 mã và 177 nến ngày. WebSocket SUBSCRIBE OK nhưng chưa nhận quote/trade thật ngoài giờ giao dịch. Không coi đăng ký là bằng chứng dữ liệu live.

1. Giữ biến môi trường API Key/Secret trên máy cá nhân. Chạy trong khớp lệnh liên tục:

```powershell
py scripts/record_ssi_v3_ws.py --symbols HPG VPB ACB --minutes 5
```

2. Kiểm tra dòng Market sample, so sánh bid/ask và trade với bảng giá SSI, xác nhận đơn vị CP của khối lượng ngày và tick. Tài liệu SSI ví dụ quote 45.45 nhưng trade 45500; không tự suy ra đơn vị của bản tin thật. Lệnh sau CHỈ là ví dụ khi xác nhận đúng các hệ số:

```powershell
py scripts/import_ssi_ws.py --symbols HPG VPB ACB --quote-price-factor 1000 --trade-price-factor 1 --volume-factor 1 --history-volume-factor 1
```

Importer chỉ nhận full book 3 bid/ask hợp lệ, ghép dữ liệu theo thời điểm nhận trong cùng phiên liên tục HOSE (quote tối đa 5 giây, trade tối đa 60 giây), không nội suy hoặc nhìn trước. Tần suất đánh giá tối thiểu 5 giây giữa các nhóm. Từ chối dữ liệu lệch đơn vị lớn; không có nhóm hợp lệ thì không ghi đè. Lưu riêng data/processed/ssi_book_snapshots.parquet và outputs/tables/ssi_ws_quality.json. Không chạy generate_synthetic.py trên dữ liệu thật. Không coi thời điểm nhận dữ liệu là thời điểm khớp thực tế.

3. Dashboard tự ưu tiên file SSI nếu tồn tại; file lỗi không tự fallback sang demo. ADV20 tính từ 20 phiên OHLCV trước ngày snapshot và độ lệch chuẩn của 20 lợi suất (21 giá). Dữ liệu lịch sử riêng ở trang SSI. Kiểm chứng theo snapshot đã ghi, không kiểm chứng khớp lệnh thật:

```powershell
py scripts/validate_recorded.py --holdings HPG:5000 VPB:4000 ACB:3000 --target 100000000 --fee 0.0015 --tax 0.001 --interval-seconds 60
py -m streamlit run src/app/app.py
```

Mức phí/thuế là giả định ví dụ, cần xác minh. Kết quả SSI lưu riêng validation_replay_ssi.csv. Phương án C vẫn tối ưu proxy tập trung, không phải tối ưu HHI trực tiếp. Chưa xác minh schema/đơn vị thật, chưa kiểm thử end-to-end với dữ liệu live. Tài liệu: https://developers.ssi.com.vn/en/docs/api-reference/subscribeUnsubscribeMarketData
