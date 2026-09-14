"""훅 스크립트를 실제 subprocess 로 실행한다 (Claude Code 가 하는 방식과 같이 stdin JSON, stdout 결과).

원칙: 어떤 입력에도 exit 0 (fail-open), 출력 상한, Stop 은 세션당 1회.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HOOKS = REPO / "hooks"


def run_hook(name: str, payload, env: dict | None = None) -> tuple[int, str, str]:
    data = payload if isinstance(payload, str) else json.dumps(payload)
    p = subprocess.run([sys.executable, str(HOOKS / name)], input=data, capture_output=True, text=True,
                       env={**os.environ, **(env or {})}, timeout=30)
    return p.returncode, p.stdout, p.stderr


def _init(root: Path) -> None:
    subprocess.run([sys.executable, str(REPO / "bin" / "autodocs"), "--root", str(root), "init",
                    "--name", "hp", "--kind", "cli", "--language", "python"], check=True, capture_output=True)


# --- SessionStart ------------------------------------------------------------------
def test_session_start_new_project(tmp_path):
    code, out, _ = run_hook("session_start.py", {"cwd": str(tmp_path), "session_id": "s"})
    assert code == 0 and "state: new" in out and "/std-init" in out


def test_session_start_compliant(tmp_path):
    _init(tmp_path)
    code, out, _ = run_hook("session_start.py", {"cwd": str(tmp_path), "session_id": "s"})
    assert code == 0 and "state: compliant" in out and "/std-" not in out


def test_session_start_finds_root_from_subdir(tmp_path):
    _init(tmp_path)
    sub = tmp_path / "src" / "hp" / "features"
    code, out, _ = run_hook("session_start.py", {"cwd": str(sub)})
    assert code == 0 and "state: compliant" in out


def test_session_start_output_is_bounded(tmp_path):
    for i in range(300):   # 많은 소스 → legacy, error 다수
        (tmp_path / f"m{i}.py").write_text("", encoding="utf-8")
    code, out, _ = run_hook("session_start.py", {"cwd": str(tmp_path)})
    assert code == 0 and len(out) < 8000


@pytest.mark.parametrize("payload", ["", "not json", "{}", '{"cwd": "/nonexistent/x"}'])
def test_session_start_fail_open(payload):
    code, _, _ = run_hook("session_start.py", payload)
    assert code == 0


# --- PostToolUse --------------------------------------------------------------------
def test_post_write_reports_only_that_file(tmp_path):
    _init(tmp_path)
    doc = tmp_path / "docs" / "architecture" / "architecture.md"
    doc.write_text("# 없음\n", encoding="utf-8")
    code, out, _ = run_hook("post_write.py", {"cwd": str(tmp_path), "tool_name": "Write", "tool_input": {"file_path": str(doc)}})
    assert code == 0
    d = json.loads(out)["hookSpecificOutput"]
    assert d["hookEventName"] == "PostToolUse" and "architecture.md" in d["additionalContext"]
    assert "README" not in d["additionalContext"]


def test_post_write_silent_when_clean_or_not_md(tmp_path):
    _init(tmp_path)
    ok = tmp_path / "docs" / "requirements" / "requirements.md"
    code, out, _ = run_hook("post_write.py", {"cwd": str(tmp_path), "tool_input": {"file_path": str(ok)}})
    assert code == 0 and out == ""
    code, out, _ = run_hook("post_write.py", {"cwd": str(tmp_path), "tool_input": {"file_path": str(tmp_path / "src/hp/features/a.py")}})
    assert code == 0 and out == ""


# --- Stop -------------------------------------------------------------------------------
def test_stop_blocks_once_per_session(tmp_path):
    _init(tmp_path)
    (tmp_path / "README.md").unlink()
    env = {"CLAUDE_PLUGIN_DATA": str(tmp_path / "_data")}
    code, out, _ = run_hook("stop.py", {"cwd": str(tmp_path), "session_id": "s1", "stop_hook_active": False}, env)
    d = json.loads(out)
    assert code == 0 and d["decision"] == "block" and d["hookSpecificOutput"]["hookEventName"] == "Stop"
    assert "[C01]" in d["reason"]
    code, out, _ = run_hook("stop.py", {"cwd": str(tmp_path), "session_id": "s1"}, env)
    assert code == 0 and out == ""                      # 같은 세션 두 번째: 침묵
    code, out, _ = run_hook("stop.py", {"cwd": str(tmp_path), "session_id": "s2"}, env)
    assert json.loads(out)["decision"] == "block"        # 다른 세션: 다시 1회
    assert not (tmp_path / ".standard" / "s1.notified").exists()   # 프로젝트 안에는 아무것도 쓰지 않음


def test_stop_respects_active_guard_and_ok(tmp_path):
    _init(tmp_path)
    (tmp_path / "README.md").unlink()
    code, out, _ = run_hook("stop.py", {"cwd": str(tmp_path), "session_id": "s", "stop_hook_active": True})
    assert code == 0 and out == ""
    (tmp_path / "README.md").write_text("# hp\n", encoding="utf-8")
    code, out, _ = run_hook("stop.py", {"cwd": str(tmp_path), "session_id": "s3"}, {"CLAUDE_PLUGIN_DATA": str(tmp_path / "_d")})
    assert code == 0 and out == ""                      # error 없음(README 섹션은 warning) → 침묵


def test_stop_silent_on_non_standard_project(tmp_path):
    (tmp_path / "a.py").write_text("", encoding="utf-8")
    code, out, _ = run_hook("stop.py", {"cwd": str(tmp_path), "session_id": "s"})
    assert code == 0 and out == ""
