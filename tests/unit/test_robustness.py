"""PROP-001 B/D: 비파괴, 플래그, 상태 판정, 잘못된 입력, 표준 위치, 종료 코드."""
import copy
import os

import pytest

from autodocs import cli
from autodocs.features import adopt, audit, init, state
from autodocs.foundation import AutodocsError, ProfileInvalid, State, StandardNotFound
from autodocs.platform import fs, standard


# --- 5. 마커 비파괴 -----------------------------------------------------------
def test_init_twice_keeps_first_profile(manifest, profile, tmp_path):
    from autodocs.features import profile as pm
    init.run(manifest, tmp_path, profile)
    other = pm.from_dict(manifest, {"name": "SECOND", "kind": "cli", "language": "csharp",
                                    "standard_version": manifest["standard"]["version"]})
    res = init.run(manifest, tmp_path, other)
    assert ".standard/project.yaml" in res.skipped and not res.created
    assert "name: demo" in (tmp_path / ".standard/project.yaml").read_text(encoding="utf-8")


# --- 6. adopt --no-adapters ---------------------------------------------------
def test_adopt_respects_no_adapters(manifest, profile, tmp_path):
    (tmp_path / "app.py").write_text("x=1", encoding="utf-8")
    adopt.run(manifest, tmp_path, profile, with_adapters=False)
    assert not (tmp_path / "CLAUDE.md").exists() and not (tmp_path / "AGENTS.md").exists()


# --- 13. 상태 판정 --------------------------------------------------------------
def test_empty_src_is_new(manifest, tmp_path):
    (tmp_path / "src").mkdir()
    assert audit.run(manifest, tmp_path).state == State.NEW


def test_only_tests_is_new(manifest, tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_a.py").write_text("", encoding="utf-8")
    assert audit.run(manifest, tmp_path).state == State.NEW


def test_source_in_src_is_legacy(manifest, tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/a.py").write_text("", encoding="utf-8")
    assert audit.run(manifest, tmp_path).state == State.LEGACY


def test_code_detection_rule_comes_from_manifest(manifest, tmp_path):
    m = copy.deepcopy(manifest)
    m["compliance"]["code_detection"] = {"source_dirs": ["lib"], "exclude_dirs": [], "min_source_files": 3}
    (tmp_path / "a.py").write_text("", encoding="utf-8")
    assert not state.has_code(m, fs.scan(tmp_path))          # 1 < 3
    (tmp_path / "lib").mkdir(); (tmp_path / "lib/b.py").write_text("", encoding="utf-8")
    assert state.has_code(m, fs.scan(tmp_path))              # lib/ 에 있음


# --- 21. adopt 미분류 목록에서 tests/ 제외 --------------------------------------
def test_adopt_plan_excludes_non_layer_dirs(manifest, profile, tmp_path):
    (tmp_path / "tests/unit").mkdir(parents=True)
    (tmp_path / "tests/unit/test_a.py").write_text("", encoding="utf-8")
    (tmp_path / "app.py").write_text("", encoding="utf-8")
    _, plan_rel = adopt.run(manifest, tmp_path, profile)
    plan = (tmp_path / plan_rel).read_text(encoding="utf-8")
    assert "`app.py`" in plan and "test_a.py" not in plan


# --- 14. 잘못된 project.yaml → finding, 크래시 아님 -----------------------------
@pytest.mark.parametrize("body", ["name: [1, 2]\nkind: web\nlanguage: python\nstandard_version: '0.1.0'\n",
                                  "name: x\nkind: web\nlanguage: python\nstandard_version: '0.1.0'\nhas_api: 'no'\n",
                                  "name: x\nkind: web\nlanguage: python\nstandard_version: '0.1.0'\nlayout_preset: nope\n",
                                  "name: x\n  bad: [yaml\n", "- just\n- a list\n"])
def test_bad_project_yaml_is_a_finding(manifest, tmp_path, body):
    (tmp_path / ".standard").mkdir()
    (tmp_path / ".standard/project.yaml").write_text(body, encoding="utf-8")
    rep = audit.run(manifest, tmp_path)
    assert rep.state == State.PARTIAL and any(f.check_id == "C00" for f in rep.findings)


def test_bad_openapi_is_a_finding(manifest, profile, tmp_path):
    init.run(manifest, tmp_path, profile)
    (tmp_path / "docs/api/openapi.yaml").write_text("- a\n- b\n", encoding="utf-8")
    rep = audit.run(manifest, tmp_path)
    assert any(f.check_id == "C08" for f in rep.findings)


# --- 15. 잘못된 manifest → AutodocsError -----------------------------------------
def test_unsupported_when_expr_is_engine_error(manifest, profile, tmp_path):
    m = copy.deepcopy(manifest)
    m["docs"]["types"]["api"]["when"] = "profile.has_api and True"
    with pytest.raises(AutodocsError):
        init.run(m, tmp_path, profile)


def test_manifest_missing_top_key_is_engine_error(tmp_path):
    (tmp_path / "manifest.yaml").write_text("standard: {version: '1'}\n", encoding="utf-8")
    with pytest.raises(AutodocsError):
        standard.load_manifest(tmp_path)


# --- 16/17/18. root · standard · preset ---------------------------------------
def test_missing_root_is_engine_error(tmp_path):
    with pytest.raises(AutodocsError):
        fs.scan(tmp_path / "nope")
    f = tmp_path / "file.txt"; f.write_text("", encoding="utf-8")
    with pytest.raises(AutodocsError):
        fs.scan(f)


def test_explicit_standard_does_not_fall_back(tmp_path, monkeypatch):
    with pytest.raises(StandardNotFound):
        standard.locate(tmp_path / "nowhere")
    monkeypatch.setenv("AUTODOCS_STANDARD_DIR", str(tmp_path / "nowhere"))
    with pytest.raises(StandardNotFound):
        standard.locate(None)


def test_unknown_preset_is_profile_error(manifest):
    from autodocs.features import profile as pm
    with pytest.raises(ProfileInvalid):
        pm.from_dict(manifest, {"name": "x", "kind": "cli", "language": "python",
                                "standard_version": "0.1.0", "layout_preset": "does-not-exist"})


def test_non_ascii_name_is_profile_error_for_package_preset(manifest, tmp_path):
    from autodocs.features import profile as pm
    prof = pm.from_dict(manifest, {"name": "법원산타", "kind": "cli", "language": "python",
                                   "standard_version": "0.1.0", "layout_preset": "python-package"})
    with pytest.raises(ProfileInvalid):
        init.run(manifest, tmp_path, prof)


# --- 25. 종료 코드 ---------------------------------------------------------------
def _std():
    from tests.unit.conftest import REPO
    return str(REPO / "standard")


def test_cli_exit_codes(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("AUTODOCS_STANDARD_DIR", raising=False)
    root = str(tmp_path)
    assert cli.main(["--standard", _std(), "--root", root, "audit"]) == 0                  # new, 위반이어도 audit 는 0
    assert cli.main(["--standard", _std(), "--root", root, "check"]) == 1                  # 위반
    assert cli.main(["--standard", _std(), "--root", root, "check", "--override", "bootstrap"]) == 0
    assert "OVERRIDE" in capsys.readouterr().err
    assert cli.main(["--standard", _std(), "--root", root + "/nope", "audit"]) == 2        # 엔진 오류
    assert cli.main(["--standard", str(tmp_path / "x"), "--root", root, "audit"]) == 2     # 표준 없음
    assert cli.main(["--standard", _std(), "--root", root, "bogus"]) == 2                  # 사용 오류
    assert cli.main(["--standard", _std(), "--root", root, "init", "--name", "d", "--kind", "cli",
                     "--language", "python", "--preset", "nope"]) == 2                     # 프로필 오류
    assert cli.main(["--standard", _std(), "--root", root, "init", "--name", "d", "--kind", "cli", "--language", "python"]) == 0
    assert cli.main(["--standard", _std(), "--root", root, "check", "--json"]) == 0
    assert '"state": "compliant"' in capsys.readouterr().out


# --- 19. 읽기 1회 ------------------------------------------------------------------
def test_each_file_read_at_most_once(manifest, profile, tmp_path, monkeypatch):
    """같은 파일을 여러 check 가 읽어도 디스크 read_text 는 파일당 정확히 1회."""
    from collections import Counter
    from pathlib import Path
    init.run(manifest, tmp_path, profile)
    snap = fs.scan(tmp_path)
    calls = Counter()
    real = Path.read_text
    monkeypatch.setattr(Path, "read_text", lambda self, *a, **k: (calls.update([str(self)]), real(self, *a, **k))[1])
    from autodocs.features import checks
    from autodocs.foundation import Context
    checks.run_all(Context(manifest=manifest, snapshot=snap, profile=profile))
    assert calls and max(calls.values()) == 1, calls
