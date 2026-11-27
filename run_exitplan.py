"""Portable launcher. Run with py (Windows) or python3 (macOS/Linux)."""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
SSI_FILES = (
    "data/processed/ssi_book_snapshots.parquet",
    "data/processed/ssi_securities.parquet",
    "data/processed/ssi_history.parquet",
)
DEMO_BOOK = "data/processed/book_snapshots.parquet"


def venv_python(root):
    return root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def prepare_environment(root, reinstall=False):
    exe = venv_python(root)
    if not exe.is_file():
        print("Creating local Python environment...", flush=True)
        venv.EnvBuilder(with_pip=True).create(root / ".venv")
    requirements = root / "requirements.txt"
    digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
    stamp = root / ".venv" / "exitplan_requirements.sha256"
    if reinstall or not stamp.is_file() or stamp.read_text(encoding="utf-8").strip() != digest:
        print("Installing ExitPlan dependencies...", flush=True)
        subprocess.run([str(exe), "-m", "pip", "install", "-r", str(requirements)], cwd=root, check=True)
        stamp.write_text(digest, encoding="utf-8")
    return exe


def missing_ssi(root):
    return [name for name in SSI_FILES if not (root / name).is_file()]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Start ExitPlan using project-relative paths.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="Enable automatic SSI updates with your own environment credentials.")
    mode.add_argument("--demo", action="store_true", help="Explicitly generate labeled synthetic demo if no SSI files are present.")
    parser.add_argument("--reinstall", action="store_true", help="Reinstall dependencies.")
    args = parser.parse_args(argv)
    if sys.version_info < (3, 10):
        parser.error("Python 3.10+ is required; Python 3.11 or 3.12 is recommended.")
    missing = missing_ssi(ROOT)
    if args.demo and len(missing) != len(SSI_FILES):
        parser.error("SSI files exist. Use a separate clean project copy for synthetic demo.")
    if not args.demo and missing:
        parser.error("Missing SSI files:\n  " + "\n  ".join(missing) +
                     "\nUse the authorized research bundle, or explicitly run --demo in a clean copy.")
    if args.live and not (os.getenv("SSI_API_KEY") and os.getenv("SSI_API_SECRET")):
        parser.error("Set your own SSI_API_KEY and SSI_API_SECRET environment variables first.")
    try:
        exe = prepare_environment(ROOT, args.reinstall)
        env = dict(os.environ, EXITPLAN_SSI_AUTO="1" if args.live else "0")
        if args.demo and not (ROOT / DEMO_BOOK).is_file():
            subprocess.run([str(exe), str(ROOT / "scripts/generate_synthetic.py")],
                           cwd=ROOT, env=env, check=True)
        print("Opening ExitPlan: http://localhost:8501", flush=True)
        return subprocess.call([str(exe), "-m", "streamlit", "run", str(ROOT / "src/app/app.py"),
                                "--server.address", "127.0.0.1"], cwd=ROOT, env=env)
    except KeyboardInterrupt:
        return 130
    except (OSError, subprocess.CalledProcessError) as exc:
        print("Startup failed:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
