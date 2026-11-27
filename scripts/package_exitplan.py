"""Create a portable research ZIP locally, never upload data or credentials."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DATA = (
    "data/processed/ssi_book_snapshots.parquet",
    "data/processed/ssi_securities.parquet",
    "data/processed/ssi_history.parquet",
)
CODE_FILES = ("README.md", "requirements.txt", "run_exitplan.py", "config.json",
              "pytest.ini", ".streamlit/config.toml")
OPTIONAL_DATA = (
    "data/processed/ssi_dashboard_closes.parquet",
    "outputs/tables/ssi_liquidity_stats.parquet",
    "outputs/tables/ssi_ws_quality.json",
    "outputs/tables/validation_replay_ssi.csv",
    "outputs/tables/validation_replay_ssi_summary.json",
    "outputs/tables/validation_replay_ssi_20261127.csv",
    "outputs/tables/intraday_daily_analysis.csv",
    "outputs/tables/intraday_analysis_summary.csv",
)


def select_files(root):
    missing = [p for p in (*CODE_FILES, *REQUIRED_DATA) if not (root / p).is_file()]
    if missing:
        raise ValueError("Missing required files: " + ", ".join(missing))
    selected = set((*CODE_FILES, *REQUIRED_DATA))
    for folder in ("src", "scripts", "tests", "docs"):
        for p in (root / folder).rglob("*"):
            if p.is_file() and p.suffix in (".py", ".md") and not any(part.startswith(".") or part == "__pycache__" for part in p.relative_to(root).parts):
                selected.add(p.relative_to(root).as_posix())
    for path in OPTIONAL_DATA:
        if (root / path).is_file():
            selected.add(path)
    for pattern in ("data/processed/ssi_intraday_1m_*.parquet",
                    "outputs/tables/validation_*_ssi.csv",
                    "outputs/tables/validation_*_ssi_summary.json"):
        selected.update(p.relative_to(root).as_posix() for p in root.glob(pattern) if p.is_file())
    for name in selected:
        p = root / name
        if not p.resolve().is_relative_to(root.resolve()) or any(q.is_symlink() for q in [p, *p.parents] if q != root and q.is_relative_to(root)):
            raise ValueError("Refusing linked file: " + name)
    return sorted(selected)


def package(root, output):
    files = select_files(root)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    manifest = {}
    try:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for name in files:
                data = (root / name).read_bytes()
                archive.writestr("ExitPlan/" + name, data)
                manifest[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            archive.writestr("ExitPlan/PACKAGE_MANIFEST.json", json.dumps(manifest, indent=2))
        tmp.replace(output)
    finally:
        if tmp.exists():
            tmp.unlink()
    return len(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-ssi-data", action="store_true",
                        help="Confirm that you have permission to share the selected SSI data with the intended recipient.")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/ExitPlan_Submission.zip")
    args = parser.parse_args()
    if not args.include_ssi_data:
        parser.error("Only package SSI data if sharing is authorized; pass --include-ssi-data to confirm.")
    try:
        count = package(ROOT, args.output)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"Created {args.output.resolve()} ({count} files plus manifest). No .env, keys, raw logs, .git or virtual environment included.")


if __name__ == "__main__":
    main()
