"""3차 검증 N1~N6: 대상 프로젝트의 어떤 입력도 엔진을 죽이거나 블록시키지 않는다."""
import os

import pytest

from autodocs import cli
from autodocs.features import audit, init
from autodocs.features import profile as pm
from autodocs.foundation import AutodocsError, PathEscape, State
from autodocs.platform import fs
from tests.unit.conftest import REPO


def _prof(manifest):
    return pm.from_dict(manifest, {"name": "demo", "kind": "cli", "language": "python", "standard_version": manifest["standard"]["version"]})


def test_symlink_loop_is_path_escape_not_runtime_error(manifest, tmp_path):
    (tmp_path / "README.md").symlink_to("README.md")
    with pytest.raises(PathEscape):
        fs.safe_path(tmp_path, "README.md")
    rep = audit.run(manifest, tmp_path)                 # audit 는 죽지 않고 finding 으로
    assert rep.state == State.NEW


def test_fifo_is_not_a_file(manifest, tmp_path):
    os.mkfifo(tmp_path / "README.md")
    snap = fs.scan(tmp_path)
    assert not snap.has_file("README.md")               # read 로 블록되지 않는다
    assert audit.run(manifest, tmp_path).state == State.NEW


@pytest.mark.skipif(os.geteuid() == 0, reason="root 는 권한 검사를 무시한다")
def test_unreadable_file_is_a_finding(manifest, tmp_path):
    init.run(manifest, tmp_path, _prof(manifest))
    (tmp_path / "README.md").chmod(0)
    try:
        rep = audit.run(manifest, tmp_path)
        assert any("읽기 실패" in f.message for f in rep.findings)
    finally:
        (tmp_path / "README.md").chmod(0o644)


@pytest.mark.skipif(os.geteuid() == 0, reason="root 는 권한 검사를 무시한다")
def test_unreadable_dir_is_a_finding_not_missing_docs(manifest, tmp_path):
    init.run(manifest, tmp_path, _prof(manifest))
    (tmp_path / "docs").chmod(0)
    try:
        rep = audit.run(manifest, tmp_path)
        assert any(f.check_id == "C00" and "docs" in f.message for f in rep.findings)
    finally:
        (tmp_path / "docs").chmod(0o755)


def test_file_in_place_of_dir_aborts_before_writing(manifest, tmp_path):
    (tmp_path / "tests").write_text("not a dir", encoding="utf-8")
    with pytest.raises(AutodocsError):
        init.run(manifest, tmp_path, _prof(manifest))
    assert not (tmp_path / "docs").exists() and not (tmp_path / "README.md").exists()   # 원자성


def test_dir_in_place_of_file_aborts(manifest, tmp_path):
    (tmp_path / "README.md").mkdir()
    with pytest.raises(AutodocsError):
        init.run(manifest, tmp_path, _prof(manifest))


def test_outside_symlink_read_is_finding_not_crash(manifest, tmp_path):
    init.run(manifest, tmp_path, _prof(manifest))
    (tmp_path / "README.md").unlink()
    (tmp_path / "README.md").symlink_to("/etc/hostname")
    rep = audit.run(manifest, tmp_path)
    assert rep.state == State.PARTIAL and any("root 밖" in f.message for f in rep.findings)


@pytest.mark.parametrize("heading", ["## 1. 프로젝트 목적", "## 프로젝트 목적:", "## **프로젝트 목적**",
                                     "## 프로젝트 목적 - 개요", "## 프로젝트 목적(요약)", "## 프로젝트 목적 – 부제"])
def test_heading_normalization_accepts_common_forms(manifest, tmp_path, heading):
    init.run(manifest, tmp_path, _prof(manifest))
    p = tmp_path / "README.md"
    p.write_text(p.read_text(encoding="utf-8").replace("## 프로젝트 목적\n", heading + "\n"), encoding="utf-8")
    rep = audit.run(manifest, tmp_path)
    assert not any(f.check_id == "C06" and "프로젝트 목적" in f.message for f in rep.findings)


def test_strict_env_zero_means_off(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTODOCS_STRICT", "0")
    assert cli.main(["--standard", str(REPO / "standard"), "--root", str(tmp_path), "check", "--override", "r"]) == 0


def test_overrides_log_symlink_is_rejected(tmp_path, monkeypatch):
    monkeypatch.delenv("AUTODOCS_STRICT", raising=False)
    (tmp_path / ".standard").mkdir()
    (tmp_path / ".standard/overrides.log").symlink_to("../README.md")
    assert cli.main(["--standard", str(REPO / "standard"), "--root", str(tmp_path), "check", "--override", "r"]) == 2
    assert not (tmp_path / "README.md").exists()
