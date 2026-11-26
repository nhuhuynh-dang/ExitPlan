"""SSI FastConnect V3 official read-only downloader for ExitPlan.

Examples (run from project root on Windows):
    py scripts/ssi_v3_sync.py --check
    py scripts/ssi_v3_sync.py --catalog
    py scripts/ssi_v3_sync.py --history --symbols HPG VPB ACB --from-date 01/09/2026 --to-date 20/11/2026

Requires SSI_API_KEY and SSI_API_SECRET environment variables; prints NO tokens.
Never orders or reads customer account assets.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path
import os
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ingest.ssi_fastconnect_v3 import (
    ALLOWED_BOARDS, SSIAuthError, SSIReadOnlyClient, SSIResponseError,
    normalize_ohlc,
)
from src.ingest.ssi_iboard import liquidity_from_history


def parse_date(value):
    for pattern in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            pass
    raise argparse.ArgumentTypeError("Ngày phải có dạng DD/MM/YYYY hoặc YYYY-MM-DD")


def _save_parquet(df, path):
    """Only publish a non-empty verified dataframe; do not write on failed HTTP."""
    if df is None or df.empty:
        raise ValueError("Không ghi file dữ liệu trống.")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    try:
        df.to_parquet(temp, index=False)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _save_csv(df, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    try:
        df.to_csv(temp, index=False, encoding="utf-8-sig")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description="SSI FastConnect V3 Market Data (read-only)")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="Kiểm tra xác thực và danh sách mã SSI")
    action.add_argument("--catalog", action="store_true", help="Lưu danh sách chứng khoán 3 sàn")
    action.add_argument("--history", action="store_true", help="Tải OHLCV daily, tính ADV")
    parser.add_argument("--symbols", nargs="+", default=["HPG", "VPB", "ACB"])
    parser.add_argument("--from-date", type=parse_date, default=date.today() - timedelta(days=75))
    parser.add_argument("--to-date", type=parse_date, default=date.today())
    parser.add_argument("--pages", type=int, default=30)
    args = parser.parse_args(argv)
    if args.from_date > args.to_date:
        parser.error("--from-date không được lớn hơn --to-date")
    if args.pages < 1 or args.pages > 200:
        parser.error("--pages chỉ nhận 1..200")
    if not (os.getenv("SSI_API_KEY") and os.getenv("SSI_API_SECRET")):
        print("CHƯA CÓ API: Chờ SSI cấp SSI_API_KEY và SSI_API_SECRET; không gọi endpoint thử nghiệm.")
        print("Xem docs/SSI_FASTCONNECT_SETUP.md để kiểm tra phê duyệt và cách cấu hình an toàn.")
        return 2

    client = SSIReadOnlyClient()
    try:
        client.authenticate()
        print("Đã xác thực SSI FastConnect V3 Market Data (không gửi OTP, không có quyền đặt lệnh).")
        if not args.catalog and not args.history:
            for board in ALLOWED_BOARDS:
                records = client.securities_by_board(board)
                print(f"{board}: {len(records)} mã được API trả về")
            print("Kết nối xác thực và truy vấn danh sách mã thành công.")
            return 0

        if args.catalog:
            all_rows = []
            for board in ALLOWED_BOARDS:
                items = client.securities_by_board(board)
                for item in items:
                    all_rows.append({
                        "symbol": str(item.get("symbol", "")).strip().upper(),
                        "board": str(item.get("board") or board).upper(),
                        "name": item.get("symbolNameVi") or item.get("symboNameVi") or "",
                        "lotSize": item.get("lotSize"),
                        "stockType": item.get("stockType"),
                        "firstTradingDate": item.get("firstTradingDate"),
                        "lastTradingDate": item.get("lastTradingDate"),
                        "source": "ssi_fastconnect_v3",
                    })
                print(f"{board}: {len(items)} mã")
            df = pd.DataFrame(all_rows).drop_duplicates(["symbol", "board"])
            _save_parquet(df, ROOT / "data/processed/ssi_securities.parquet")
            print(f"Đã lưu danh sách {len(df)} mã (nguồn SSI V3 thật).")
            return 0

        records = []
        symbols = sorted(set(str(sym).strip().upper() for sym in args.symbols))
        for sym in symbols:
            candles = client.ohlc_daily(sym, args.from_date, args.to_date,
                                        max_pages=args.pages)
            if not candles:
                raise SSIResponseError(
                    f"{sym}: chưa có dữ liệu trong khoảng ngày đã chọn. "
                    "Không ghi file từng phần hoặc tự sinh nến."
                )
            records.extend(candles)
            print(f"{sym}: {len(candles)} nến ngày")

        history = normalize_ohlc(records)
        if set(history["symbol"]) != set(symbols):
            raise SSIResponseError("Bản ghi hợp lệ không đủ các mã đã yêu cầu. Không ghi file.")
        # Preserve earlier symbols/dates when downloading a new subset.
        previous_path = ROOT / "data/processed/ssi_history.parquet"
        if previous_path.exists():
            previous = pd.read_parquet(previous_path)
            if set(previous["source"]) != {"ssi_fastconnect_v3"} or set(previous["data_kind"]) != {"historical"}:
                raise SSIResponseError("File lịch sử cũ không cùng nguồn SSI V3; không ghi đè.")
            history = pd.concat([previous, history], ignore_index=True).drop_duplicates(["symbol", "tradingDate"], keep="last").sort_values(["symbol", "tradingDate"])
        from src.analytics.ssi_history_stats import asof_history_stats
        stats = asof_history_stats(history)
        stats["source"] = "ssi_fastconnect_v3"
        # Historical bars ONLY: never overwrite book_snapshots.parquet.
        _save_parquet(history, ROOT / "data/processed/ssi_history.parquet")
        _save_parquet(stats, ROOT / "outputs/tables/ssi_liquidity_stats.parquet")
        _save_csv(history, ROOT / "data/raw/ssi_fastconnect_v3_ohlcv.csv")
        print(f"OK: kho lịch sử có {len(history)} nến SSI chính thức, {history.symbol.nunique()} mã.")
        print("KHÔNG có bidPrice/bidVol; chưa được dùng làm bằng chứng WebSocket/sổ lệnh.")
        return 0
    except (SSIAuthError, SSIResponseError, ValueError, OSError, ImportError) as exc:
        # Never output a requests.Response or secret/token.
        print("SSI V3 chưa thành công:", str(exc))
        print("Không tạo dữ liệu giả hoặc giả mạo kết nối khi có lỗi.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
