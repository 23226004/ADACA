"""hooks.json 계약 — bkit 이 릴리스에 실어 보낸 설정 결함을 코드로 막는다 (ref/bkit-reference-notes.md 1.2).

- HC-EVENT   : Claude Code 가 아는 이벤트 이름만
- HC-TIMEOUT : timeout 은 초 단위 정수/실수, 1~60
- HC-IF-ONE  : `if` 는 permission rule 하나 (`|` 대체 없음, 형식 Tool(pattern))
- HC-IF-EVENT: `if` 는 툴 이벤트에서만
- HC-MATCHER : matcher 를 지원하지 않는 이벤트에 matcher 금지
- HC-ONCE    : hooks.json 에서 `once` 는 무시되므로 선언 금지
- HC-CMD     : 모든 command 는 ${CLAUDE_PLUGIN_ROOT} 를 참조하고 실제 파일로 resolve 되어야 함
- HC-SHAPE   : 최상위 "hooks" 키, 각 이벤트는 [{matcher?, hooks:[{type, command, timeout}]}]
"""
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HOOKS = REPO / "hooks" / "hooks.json"

CC_HOOK_EVENTS = {
    "SessionStart", "Setup", "UserPromptSubmit", "UserPromptExpansion", "PreToolUse", "PermissionRequest",
    "PermissionDenied", "PostToolUse", "PostToolUseFailure", "PostToolBatch", "Notification", "MessageDisplay",
    "SubagentStart", "SubagentStop", "TaskCreated", "TaskCompleted", "Stop", "StopFailure", "TeammateIdle",
    "InstructionsLoaded", "ConfigChange", "CwdChanged", "DirectoryAdded", "FileChanged", "WorktreeCreate",
    "WorktreeRemove", "PreCompact", "PostCompact", "Elicitation", "ElicitationResult", "SessionEnd",
    "PreModelSwitch", "PostModelSwitch",
}
IF_EVALUATED_ON = {"PreToolUse", "PostToolUse", "PostToolUseFailure", "PermissionRequest", "PermissionDenied"}
NO_MATCHER_EVENTS = {"UserPromptSubmit", "PostToolBatch", "Stop", "TeammateIdle", "TaskCreated", "TaskCompleted",
                     "WorktreeCreate", "WorktreeRemove", "MessageDisplay", "CwdChanged"}
_IF_RULE = re.compile(r"^[A-Za-z_]+\([^()|]+\)$")


@pytest.fixture(scope="module")
def cfg() -> dict:
    return json.loads(HOOKS.read_text(encoding="utf-8"))


def _entries(cfg):
    for event, groups in cfg["hooks"].items():
        for g in groups:
            for h in g["hooks"]:
                yield event, g, h


def test_shape(cfg):
    assert set(cfg) <= {"description", "hooks"} and isinstance(cfg["hooks"], dict)
    for event, g, h in _entries(cfg):
        assert set(g) <= {"matcher", "hooks"}, (event, g.keys())
        assert h["type"] == "command" and isinstance(h["command"], str)
        assert set(h) <= {"type", "command", "timeout", "if"}, (event, h.keys())


def test_events_are_known(cfg):
    assert set(cfg["hooks"]) <= CC_HOOK_EVENTS


def test_timeout_is_seconds_in_range(cfg):
    for event, _, h in _entries(cfg):
        assert "timeout" in h, (event, h["command"])
        assert isinstance(h["timeout"], (int, float)) and 1 <= h["timeout"] <= 60, (event, h["timeout"])


def test_if_is_single_rule_on_tool_events_only(cfg):
    for event, _, h in _entries(cfg):
        if "if" not in h:
            continue
        assert event in IF_EVALUATED_ON, f"`if` 는 {event} 에서 평가되지 않음"
        assert "|" not in h["if"] and _IF_RULE.match(h["if"]), h["if"]


def test_no_matcher_on_unsupported_events(cfg):
    for event, g, _ in _entries(cfg):
        if event in NO_MATCHER_EVENTS:
            assert "matcher" not in g, event


def test_once_not_declared(cfg):
    for _, _, h in _entries(cfg):
        assert "once" not in h


def test_commands_resolve_to_plugin_files(cfg):
    for event, _, h in _entries(cfg):
        refs = re.findall(r'\$\{CLAUDE_PLUGIN_ROOT\}/([^"\s]+)', h["command"])
        assert refs, f"{event}: ${{CLAUDE_PLUGIN_ROOT}} 미참조 — {h['command']}"
        for r in refs:
            assert (REPO / r).is_file(), f"{event}: {REPO / r} 없음"
        assert h["command"].startswith("sh "), f"{event}: 훅은 bin/py.sh 를 통해 실행해야 함 (Windows 의 python3 부재 대응)"
        assert "\\" not in h["command"]


def test_plugin_json_minimal_keys():
    pj = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert set(pj) <= {"name", "version", "description", "author"} and pj["name"] == "autodocs"
    assert re.match(r"^[a-z0-9-]+$", pj["name"])


def test_commands_and_skill_exist_and_have_frontmatter():
    for name in ("std-init", "std-adopt", "std-audit", "std-check"):
        text = (REPO / "commands" / f"{name}.md").read_text(encoding="utf-8")
        assert text.startswith("---\n") and f"name: {name}\n" in text and "description:" in text
        assert 'sh "${CLAUDE_PLUGIN_ROOT}/bin/py.sh" "${CLAUDE_PLUGIN_ROOT}/bin/autodocs"' in text
    skill = (REPO / "skills" / "standard-workflow" / "SKILL.md").read_text(encoding="utf-8")
    assert skill.startswith("---\n") and "name: standard-workflow" in skill
    assert (REPO / "bin" / "autodocs").stat().st_mode & 0o111, "bin/autodocs 는 실행 가능해야 함"


def test_manifest_adapter_declaration_matches_plugin():
    """manifest adapters.claude 가 약속한 커맨드/스킬/훅이 실제로 있다."""
    import yaml
    m = yaml.safe_load((REPO / "standard" / "manifest.yaml").read_text(encoding="utf-8"))
    provides = {k: v for d in m["adapters"]["claude"]["provides"] for k, v in d.items()}
    for c in provides["commands"]:
        assert (REPO / "commands" / f"{c}.md").is_file(), c
    for s in provides["skills"]:
        assert (REPO / "skills" / s / "SKILL.md").is_file(), s


def test_marketplace_json_points_at_this_repo():
    """marketplace.json 은 이 저장소 자신을 플러그인으로 선언하고, 버전은 plugin.json 과 같아야 한다."""
    mk = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    pj = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert mk["name"] == "adaca" and mk["owner"]["name"]
    (entry,) = [p for p in mk["plugins"] if p["name"] == "autodocs"]
    assert entry["source"] == "./" and "\\" not in entry["source"]
    assert entry["version"] == pj["version"], "plugin.json 과 marketplace.json 의 version 이 다르면 사용자에게 갱신이 전달되지 않음"
    for f in ("install.sh", "install.ps1"):
        text = (REPO / f).read_text(encoding="utf-8")
        assert "23226004/ADACA" in text and '"adaca"' in text and '"autodocs"' in text
