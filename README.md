# ExitPlan — Dashboard hỗ trợ lập phương án thanh lý danh mục

**Smart Portfolio Exit | Đồ án Gói phần mềm ứng dụng cho tài chính 1**

ExitPlan là ứng dụng hỗ trợ nhà đầu tư cá nhân xây dựng phương án bán cổ phiếu để thu về một khoản tiền ròng mục tiêu, đồng thời cân nhắc chi phí thanh khoản và mức độ tập trung của danh mục còn lại.

Ứng dụng được phát triển bằng Python và Streamlit, sử dụng dữ liệu thị trường từ SSI FastConnect V3 và mô hình tối ưu hóa nguyên tuyến tính hỗn hợp (MILP). ExitPlan phục vụ phân tích và mô phỏng học thuật, không kết nối tài khoản giao dịch, không đặt lệnh thật và không đưa ra khuyến nghị đầu tư.

**Nguyên tắc sử dụng:** Nhà đầu tư và giảng viên không cần tài khoản SSI, API Key hay Secret. Quyền truy xuất dữ liệu thị trường là trách nhiệm của bên vận hành ExitPlan.

## 1. Hướng dẫn chạy lần đầu

### Dành cho người nhận đồ án

1. Cài Python 3.11 hoặc 3.12 từ [python.org](https://www.python.org/downloads/). Trên Windows, chọn cài Python Launcher hoặc thêm Python vào PATH.
2. Giải nén `ExitPlan_Submission.zip` và mở terminal tại thư mục `ExitPlan` chứa `run_exitplan.py`.
3. Chạy một lệnh:

**Windows (PowerShell):**

```powershell
py run_exitplan.py
```

**macOS / Linux:**

```bash
python3 run_exitplan.py
```

Launcher tự tạo môi trường `.venv` và cài các thư viện từ `requirements.txt` ở lần đầu (cần Internet để tải thư viện), sau đó mở Streamlit tại **http://localhost:8501**. Các lần sau tái sử dụng môi trường riêng. Không cần API Key SSI để xem dữ liệu thực đã lưu. Mặc định launcher tắt kết nối API để tái lập kết quả offline; dữ liệu được đọc theo đường dẫn tương đối trong thư mục dự án, không phụ thuộc máy người thực hiện đồ án. Nhấn Ctrl+C để dừng.

Nếu Linux chưa có mô-đun venv, cài gói Python venv phù hợp với bản phân phối. Nếu cần cài lại thư viện, thêm `--reinstall` vào lệnh launcher.

### Dành cho người chuẩn bị bài nộp

Trên máy đã có dữ liệu SSI của đồ án, dừng dashboard và chỉ đóng gói khi được phép chia sẻ dữ liệu với người nhận:

```powershell
py scripts/package_exitplan.py --include-ssi-data
```

File kết quả: `dist/ExitPlan_Submission.zip`. Gói chứa mã nguồn, tài liệu, ba tệp SSI bắt buộc (snapshot, danh mục, OHLCV), các kết quả SSI có sẵn được chọn lọc và manifest SHA-256. Không chứa API Key, Secret, token, .env, thư mục .git, .venv hoặc raw logs. Không tự tải lên GitHub. Giải nén ZIP sang một thư mục khác và thử launcher trước khi gửi.

### Nếu chỉ tải mã nguồn từ GitHub

```powershell
git clone https://github.com/nhuhuynh-dang/ExitPlan.git
cd ExitPlan
```

GitHub không chứa đầy đủ dữ liệu SSI cục bộ. Để chạy bằng dữ liệu thực, dùng gói nghiên cứu được phép chia sẻ do bên vận hành chuẩn bị. Người dùng không cần tự khởi tạo SSI. Ba tệp tối thiểu là:

| Tệp | Vai trò |
| --- | --- |
| `data/processed/ssi_book_snapshots.parquet` | Sổ lệnh SSI đã chuẩn hóa |
| `data/processed/ssi_securities.parquet` | Danh mục chứng khoán |
| `data/processed/ssi_history.parquet` | OHLCV ngày |

Chỉ để thử chức năng nếu không có quyền hoặc dữ liệu SSI, có thể chạy `py run_exitplan.py --demo` (macOS/Linux: `python3 run_exitplan.py --demo`) trong bản sao riêng không có sổ lệnh và danh mục SSI. Demo được gắn nhãn synthetic và không đại diện cho dữ liệu thị trường thật. Launcher không tự chuyển sang dữ liệu giả khi thiếu hoặc lỗi dữ liệu SSI.

**Chạy thủ công (nếu cần):**

```powershell
py -m pip install -r requirements.txt
$env:EXITPLAN_SSI_AUTO = "0"
py -m pytest -q
py -m streamlit run src/app/app.py
```

Để cập nhật mã nguồn trong thư mục Git hiện có, dừng ứng dụng rồi chạy `git pull origin main`. Chế độ cập nhật trực tuyến chỉ dành cho bên vận hành ở mục 3.

## 2. Hướng dẫn sử dụng nhanh

1. Vào **Tổng quan** để kiểm tra nguồn dữ liệu, số mã và thời điểm snapshot.
2. Vào **Lập phương án**, tìm mã cổ phiếu, xem thông tin, nhập số lượng sở hữu và bấm **Thêm vào danh mục**.
3. Nhập mục tiêu tiền ròng, phí, thuế và mức ưu tiên λ, sau đó bấm **Tính phương án**.
4. Vào **Kết quả & so sánh** để xem A/B/C/P, chi tiết lượng bán, HHI, chi phí và tiền ròng. Bấm **Tính đường đánh đổi λ** nếu cần phân tích bổ sung.
5. Xem **Rủi ro thanh khoản** và **Lịch sử giá** để kiểm tra độ sâu sổ lệnh, ADV20, Sigma20 và dữ liệu lịch sử. Có thể xuất CSV ở các trang tương ứng.

Ví dụ dùng thử (giả định, không phải danh mục khuyến nghị):

| Thông số | Giá trị |
| --- | ---: |
| HPG | 5.000 CP |
| VPB | 4.000 CP |
| ACB | 3.000 CP |
| Mục tiêu tiền ròng | 100.000.000 đồng |
| Phí bán | 0,15% |
| Thuế | 0,10% |
| Mức ưu tiên λ | 0,5 |

Chỉ chọn các mã có snapshot chung hợp lệ. Nếu nút tính bị khóa, kiểm tra số lượng nắm giữ, độ sâu sổ lệnh và điều kiện bán theo lô 100 CP. Nếu mục tiêu vượt khả năng thanh lý, hệ thống báo thiếu hụt thay vì giả định bán được ngoài nguồn lực hiện có.

## 3. Hạ tầng dữ liệu SSI (chỉ dành cho bên vận hành)

Người dùng và giảng viên bỏ qua toàn bộ mục này. Bên vận hành quản lý quyền **Market Data chỉ đọc**, cấu hình khóa ở backend và cung cấp dữ liệu đã xử lý theo phạm vi được phép. Với bản ZIP, mọi phép tính chạy cục bộ trên dữ liệu đã lưu; dữ liệu không tự cập nhật nếu không có hạ tầng kết nối.

Nếu triển khai dịch vụ trực tuyến, Streamlit có thể phục vụ nhiều người dùng qua một máy chủ quản lý tập trung. Máy chủ nhận dữ liệu từ SSI và người dùng chỉ truy cập giao diện qua trình duyệt, không nhập khóa riêng. Cần xác nhận quyền cung cấp dữ liệu cho người dùng, triển khai HTTPS và kiểm soát truy cập trước khi công bố. Phiên bản đồ án hiện tại chưa triển khai máy chủ công khai.

### Cấu hình bảo mật

Trên máy của bên vận hành, trong cùng cửa sổ PowerShell dùng để chạy backend:

```powershell
$env:SSI_API_KEY = "KEY_DO_SSI_CAP"
$env:SSI_API_SECRET = "SECRET_DO_SSI_CAP"
py scripts/ssi_v3_sync.py --check
```

Thay giá trị minh họa bằng khóa của chính người vận hành. Không đưa khóa, secret hoặc token lên GitHub, báo cáo hoặc video demo.

### Khởi tạo kho dữ liệu SSI nếu chưa có

Chạy khi ứng dụng đã dừng:

```powershell
py scripts/ssi_v3_sync.py --catalog
py scripts/record_ssi_v3_ws.py --all-market --minutes 5 --max-mb 64
```

Bộ ghi cần được chạy trong khung thu thập của thị trường. Sau khi nhận quote/trade thật, đối chiếu đơn vị giá và khối lượng với SSI, rồi import file vừa ghi. Ví dụ dưới đây sử dụng hệ số 1 như cấu hình bộ dữ liệu nghiên cứu đã quan sát; phải kiểm tra lại trước khi áp dụng cho nguồn mới:

```powershell
py scripts/import_ssi_ws.py --all-market --append --input data/raw/ssi_ws/TEN_FILE_THUC_TE.jsonl --quote-price-factor 1 --trade-price-factor 1 --volume-factor 1 --history-volume-factor 1
```

Thay `TEN_FILE_THUC_TE.jsonl` bằng tên file do bộ ghi tạo. Import toàn thị trường giới hạn 128 MiB đầu vào mỗi lượt; chia file lớn theo ranh giới dòng JSONL và giữ bản gốc. Dùng `--append` để tích lũy thay vì thay thế snapshot.

Bổ sung OHLCV ngày còn thiếu (ví dụ cho dữ liệu ngày 27/11/2026):

```powershell
py scripts/ssi_market_history.py --missing-book-history --strict-calendar --from-date 01/09/2026 --to-date 26/11/2026 --dry-run
py scripts/ssi_market_history.py --missing-book-history --strict-calendar --from-date 01/09/2026 --to-date 26/11/2026 --delay 2
```

Điều chỉnh khoảng ngày theo ngày snapshot cần phân tích. Nếu token hết hạn, chạy lại script cùng khoảng ngày để tiếp tục từ checkpoint. Không tự nội suy phiên bị thiếu.

### Bật chế độ cập nhật tự động

Chỉ bên vận hành thực hiện sau khi có danh mục và snapshot SSI hợp lệ cùng hệ số quy đổi đã lưu:

```powershell
$env:EXITPLAN_SSI_AUTO = "1"
py -m streamlit run src/app/app.py
```

- Trong khung thu thập 09:15–11:30 và 13:00–14:30 (UTC+7), hệ thống tự nhận bản tin SSI, chuẩn hóa và tích lũy snapshot theo đợt khoảng 60 giây.
- Nghỉ trưa và giai đoạn đầu/cuối phiên sử dụng snapshot gần nhất. Sau 15:15 hoặc ngoài ngày giao dịch, hệ thống bổ sung OHLCV của ngày giao dịch hoàn thành gần nhất; nếu SSI chưa có dữ liệu mới, ghi rõ ngày dữ liệu hiện có.
- Giá đóng cửa chỉ dùng làm tham chiếu, không thay thế sổ lệnh dùng cho mô phỏng thanh lý. Phương án đã tính được gắn với snapshot gốc.
- Không chạy bộ ghi thủ công đồng thời với bộ ghi tự động của dashboard. Chế độ tự động hiện sử dụng lịch năm 2026 và chưa được xác nhận end-to-end trong phiên thật sau lần nâng cấp gần nhất.

Chi tiết vận hành: [SSI tự động trong ExitPlan](docs/SSI_DASHBOARD_LIVE.md). Tài liệu API: [SSI Developer Portal](https://developers.ssi.com.vn/).

## 4. Phương pháp và chức năng chính

| Phương án | Mục tiêu |
| --- | --- |
| A — Chi phí thấp | Giảm chi phí thanh khoản |
| B — Cân bằng | Cân bằng chi phí và mức tập trung bằng λ |
| C — Giảm tập trung | Giảm đại lượng đại diện cho mức tập trung |
| P — Theo tỷ lệ | Xấp xỉ thanh lý theo tỷ lệ danh mục |

MILP lựa chọn lượng bán rời rạc theo lô 100 CP, tối đa 12 mã, giới hạn bởi số lượng sở hữu và độ sâu ba mức giá mua quan sát được. Tiền ròng bằng doanh số khớp mô phỏng trừ phí và thuế. HHI được tính sau khi tìm nghiệm; B và C tối ưu đại lượng đại diện cho mức tập trung, không trực tiếp tối ưu HHI.

ADV20 sử dụng 20 phiên khối lượng giao dịch; Sigma20 sử dụng 20 lợi suất từ 21 giá đóng cửa trước ngày snapshot, có kiểm tra lịch giao dịch. Thiếu dữ liệu hợp lệ được hiển thị rõ thay vì thay bằng giá trị giả.

## 5. Kiểm chứng và tái lập kết quả

Kiểm thử tự động:

```powershell
py -m pytest -q
```

Phát lại phương án B trên sổ lệnh SSI đã lưu (phí và thuế dưới đây là giả định nghiên cứu):

```powershell
py scripts/validate_recorded.py --holdings HPG:5000 VPB:4000 ACB:3000 --target 100000000 --fee 0.0015 --tax 0.001 --lambda-weight 0.5 --interval-seconds 60
```

Sao lưu kết quả replay cũ trước khi chạy lại vì script cập nhật tệp kết quả cùng tên. Replay chỉ sử dụng thời điểm có đủ sổ lệnh đồng bộ, không đo tỷ lệ khớp lệnh thật.

**Mốc thực nghiệm đã ghi nhận ngày 27/11/2026:**

| Chỉ tiêu | Kết quả |
| --- | ---: |
| Bản ghi snapshot theo mã và thời điểm | 17.408 |
| Mã có snapshot | 461 |
| Mã đủ lịch sử ADV20 và Sigma20 theo kiểm tra lịch | 406 |
| Dữ liệu OHLCV 1 phút (ACB, HPG, VPB) | 6.740 nến / 10 ngày giao dịch |
| Replay phương án B, mục tiêu 100 triệu đồng | 67/67 thời điểm hợp lệ đạt mục tiêu |
| Kiểm thử tự động, xác nhận ngày 28/11/2026 | 134 bài đạt |

Đây là mốc tham chiếu đã ghi nhận, không phải số liệu cố định của ứng dụng. Replay có 53 thời điểm bị bỏ qua do thiếu snapshot đồng bộ; 100% chỉ tính trên 67 thời điểm hợp lệ của một ngày thu thập. Dữ liệu intraday OHLCV 10 ngày không tương đương sổ lệnh WebSocket 10 ngày.

## 6. Cấu trúc dự án

```text
ExitPlan/
├── src/
│   ├── app/          # Streamlit, giao diện, biểu đồ, cache
│   ├── ingest/       # SSI REST/WebSocket, chuẩn hóa dữ liệu
│   ├── data/         # Schema, kho dữ liệu, lọc cổ phiếu
│   ├── finance/      # Mô phỏng bán theo độ sâu sổ lệnh
│   └── analytics/    # MILP, ADV20, Sigma20, kiểm chứng
├── scripts/          # Thu thập, import, replay và demo
├── data/             # Dữ liệu lưu cục bộ
├── outputs/          # Bảng kết quả và kiểm tra chất lượng
├── tests/            # Kiểm thử tự động
├── docs/             # Hướng dẫn kỹ thuật
├── requirements.txt
└── README.md
```

Luồng xử lý: **SSI REST/WebSocket → kiểm tra và chuẩn hóa → Parquet → cache → mô hình tài chính/MILP → dashboard và CSV.**

## 7. Giới hạn và sử dụng có trách nhiệm

- Snapshot phản ánh độ sâu ba mức mua tại thời điểm quan sát; không mô hình hóa hàng đợi lệnh, tác động giá động hoặc khớp lệnh thực tế.
- Cập nhật WebSocket theo đợt, không phải bảng giá tick-by-tick liên tục; phụ thuộc quyền SSI, kết nối và chất lượng dữ liệu.
- Hệ số quy đổi giá/khối lượng phải được đối chiếu với nguồn SSI. Mức phí và thuế là giả định người dùng nhập.
- Không trộn dữ liệu thật và dữ liệu giả lập. Không tự dựng sổ lệnh từ OHLCV, không tự tạo dữ liệu thiếu.
- Không chia sẻ dữ liệu thị trường ngoài phạm vi được cấp phép; không đưa API Key, Secret hoặc token vào mã nguồn.

**Công cụ phân tích học thuật, không phải khuyến nghị đầu tư.**
