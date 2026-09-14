"""PROP-001 재검증에서 나온 회귀 R1~R8."""
import copy
import os

import pytest

from autodocs import cli
from autodocs.features import adopt, audit, init
from autodocs.features import profile as pm
from autodocs.foundation import ManifestInvalid, PathEscape, State
from autodocs.platform import fs, standard


def _prof(manifest, **kw):
    base = {"name": "demo", "kind": "cli", "language": "python", "standard_version": manifest["standard"]["version"]}
    return pm.from_dict(manifest, {**base, **kw})


# R1 — 비ASCII 이름은 placeholder 를 쓰는 preset 에서만 문제. generic 은 정상, audit 은 죽지 않는다.
def test_korean_name_works_with_generic_preset(manifest, tmp_path):
    res = init.run(manifest, tmp_path, _prof(manifest, name="법원산타"))
    assert "README.md" in res.created
    assert audit.run(manifest, tmp_path).state == State.COMPLIANT


def test_korean_name_with_package_preset_is_finding_not_crash(manifest, tmp_path):
    init.run(manifest, tmp_path, _prof(manifest))
    y = tmp_path / ".standard/project.yaml"
    y.write_text(y.read_text(encoding="utf-8").replace("name: demo", "name: 법원산타").replace("layout_preset: generic", "layout_preset: python-package"), encoding="utf-8")
    rep = audit.run(manifest, tmp_path)                     # exit 2 가 아니라 partial + C00, 그리고 C00 은 한 번만
    c00 = [f for f in rep.findings if f.check_id == "C00"]
    assert rep.state == State.PARTIAL and len(c00) == 1
    assert any(f.check_id == "C01" for f in rep.findings) is False   # 나머지 check 도 정상 실행됨 (README 는 있으니 C01 없음)


# R2 — root 안의 정상 심링크는 "이미 있음" 으로 유지. 중단 없음.
def test_symlink_inside_root_is_kept(manifest, tmp_path):
    (tmp_path / "AGENTS.md").write_text("mine", encoding="utf-8")
    (tmp_path / "CLAUDE.md").symlink_to("AGENTS.md")
    res = init.run(manifest, tmp_path, _prof(manifest))
    assert "CLAUDE.md" in res.skipped and (tmp_path / "CLAUDE.md").is_symlink()
    assert (tmp_path / ".standard/project.yaml").exists()  # 끝까지 진행됨


def test_dangling_symlink_inside_root_is_kept(manifest, tmp_path):
    (tmp_path / "CLAUDE.md").symlink_to("does-not-exist.md")
    res = init.run(manifest, tmp_path, _prof(manifest))
    assert "CLAUDE.md" in res.skipped and not (tmp_path / "does-not-exist.md").exists()


def test_init_is_atomic_on_escape(manifest, tmp_path):
    """하나라도 root 밖이면 아무것도 쓰지 않는다 (반쪽 초기화 방지)."""
    m = copy.deepcopy(manifest)
    m["adapters"]["gemini"]["pointer_file"] = "../outside.md"   # 어댑터는 마지막에 쓰이지만 preflight 가 먼저 막는다
    with pytest.raises(PathEscape):
        init.run(m, tmp_path, _prof(manifest))
    assert not (tmp_path / "README.md").exists() and not (tmp_path / "docs").exists()


# R3 — 읽기도 root 밖 심링크는 거부
def test_read_through_outside_symlink_is_rejected(manifest, tmp_path):
    init.run(manifest, tmp_path, _prof(manifest))
    (tmp_path / "README.md").unlink()
    (tmp_path / "README.md").symlink_to("/etc/hostname")
    snap = fs.scan(tmp_path, manifest["scan"])
    assert snap.has_file("README.md")
    with pytest.raises(PathEscape):
        snap.read("README.md")


# R4 — standard 안의 심링크 템플릿: 목적지가 standard 안이면 허용, 밖이면 거부
def test_template_symlink_policy(manifest, tmp_path):
    std = tmp_path / "std"; (std / "templates").mkdir(parents=True)
    (std / "manifest.yaml").write_text((standard.locate(None) / "manifest.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    (std / "templates/real.md").write_text("# $project_name\n", encoding="utf-8")
    (std / "templates/README.md").symlink_to("real.md")
    m = standard.load_manifest(std)
    assert standard.template_path(m, "templates/README.md").read_text(encoding="utf-8").startswith("#")
    (std / "templates/evil.md").symlink_to("/etc/hostname")
    with pytest.raises(PathEscape):
        standard.template_path(m, "templates/evil.md")


# R5 — 셸 변수는 잔존 변수 경고에서 제외
def test_leftover_warning_ignores_shell_vars(manifest, tmp_path):
    std = tmp_path / "std"; (std / "templates").mkdir(parents=True)
    (std / "manifest.yaml").write_text((standard.locate(None) / "manifest.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    (std / "templates/README.md").write_text("# $project_name\nexport PATH=$HOME/bin:$PATH\n$unknown_var\n", encoding="utf-8")
    m = standard.load_manifest(std)
    proj = tmp_path / "p"; proj.mkdir()
    res = init.run(m, proj, _prof(m))
    assert any("unknown_var" in w for w in res.warnings) and not any("HOME" in w for w in res.warnings)


# R6 — override 는 흔적을 남기고, AUTODOCS_STRICT 에서는 금지
def test_override_logs_and_strict_forbids(tmp_path, capsys, monkeypatch):
    std = str(standard.locate(None)); root = str(tmp_path)
    assert cli.main(["--standard", std, "--root", root, "check", "--override", "hotfix"]) == 0
    log = (tmp_path / ".standard/overrides.log").read_text(encoding="utf-8")
    assert "hotfix" in log and "[C01]" in log
    monkeypatch.setenv("AUTODOCS_STRICT", "1")
    assert cli.main(["--standard", std, "--root", root, "check", "--override", "hotfix"]) == 1
    assert "AUTODOCS_STRICT" in capsys.readouterr().err


# R7 — code_detection 은 manifest 에만. 누락이면 ManifestInvalid
def test_missing_code_detection_is_manifest_error(manifest, tmp_path):
    m = copy.deepcopy(manifest); del m["compliance"]["code_detection"]
    with pytest.raises(ManifestInvalid):
        audit.run(m, tmp_path)


# 21 잔여 — scripts/ 도 adopt 목록에서 제외
def test_adopt_excludes_code_detection_exclude_dirs(manifest, tmp_path):
    (tmp_path / "scripts").mkdir(); (tmp_path / "scripts/deploy.py").write_text("", encoding="utf-8")
    (tmp_path / "app.py").write_text("", encoding="utf-8")
    _, rel = adopt.run(manifest, tmp_path, _prof(manifest))
    plan = (tmp_path / rel).read_text(encoding="utf-8")
    assert "`app.py`" in plan and "deploy.py" not in plan


# 23 잔여 — 섹션 헤딩은 정확히 일치해야 한다
def test_section_match_is_exact(manifest, tmp_path):
    init.run(manifest, tmp_path, _prof(manifest, has_database=True))
    p = tmp_path / "docs/database/database.md"
    p.write_text(p.read_text(encoding="utf-8").replace("## ERD\n", "## ERD 미완성\n"), encoding="utf-8")
    rep = audit.run(manifest, tmp_path)
    assert any(f.check_id == "C06" and "ERD" in f.message for f in rep.findings)
