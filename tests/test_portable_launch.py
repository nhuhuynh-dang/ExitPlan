"""Portable launcher and submission packaging checks without installing or networking."""
import json
from pathlib import Path
import zipfile
import pytest

import run_exitplan as launcher
from scripts import package_exitplan as bundle


def make_files(root, names):
    for name in names:
        p=root/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text("test fixture",encoding="utf-8")


def test_launcher_resolves_inputs_relative_to_project(tmp_path,monkeypatch):
    root=tmp_path/"folder with spaces"
    root.mkdir()
    make_files(root,launcher.SSI_FILES)
    monkeypatch.chdir(tmp_path)
    assert launcher.missing_ssi(root)==[]
    (root/launcher.SSI_FILES[0]).unlink()
    assert launcher.missing_ssi(root)==[launcher.SSI_FILES[0]]


def test_portable_package_keeps_required_data_and_excludes_secrets(tmp_path):
    root=tmp_path/"project"
    root.mkdir()
    make_files(root,(*bundle.CODE_FILES,*bundle.REQUIRED_DATA,"src/app/app.py",
                     "data/raw/private.jsonl",".env",".streamlit/secrets.toml",
                     ".venv/secret.py","src/__pycache__/temp.py",
                     "data/processed/ssi_intraday_1m_example.parquet"))
    target=tmp_path/"out.zip"
    bundle.package(root,target)
    with zipfile.ZipFile(target) as z:
        names=set(z.namelist())
        manifest=json.loads(z.read("ExitPlan/PACKAGE_MANIFEST.json"))
        assert "ExitPlan/run_exitplan.py" in names
        assert all("ExitPlan/"+p in names for p in bundle.REQUIRED_DATA)
        assert "ExitPlan/data/processed/ssi_intraday_1m_example.parquet" in names
        assert not any(".env" in p or "secrets.toml" in p or "data/raw/" in p
                       or "__pycache__" in p for p in names)
        assert set(manifest)=={p.removeprefix("ExitPlan/") for p in names
                               if not p.endswith("PACKAGE_MANIFEST.json")}


def test_package_rejects_missing_research_data(tmp_path):
    make_files(tmp_path,bundle.CODE_FILES)
    with pytest.raises(ValueError,match="Missing required files"):
        bundle.package(tmp_path,tmp_path/"out.zip")
    assert not (tmp_path/"out.zip").exists()


def test_offline_launcher_does_not_pass_live_mode(tmp_path,monkeypatch):
    make_files(tmp_path,launcher.SSI_FILES)
    monkeypatch.setattr(launcher,"ROOT",tmp_path)
    monkeypatch.setattr(launcher,"prepare_environment",lambda *a:Path("test-python"))
    observed={}
    def fake_call(args,**kwargs):
        observed.update(kwargs)
        return 0
    monkeypatch.setattr(launcher.subprocess,"call",fake_call)
    assert launcher.main([])==0
    assert observed["cwd"]==tmp_path
    assert observed["env"]["EXITPLAN_SSI_AUTO"]=="0"
