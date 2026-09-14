"""L6 — 실제 Claude Code 세션에서 훅이 발화했다는 증거(live-run.json)가 현재 hooks.json 과 일치하는가.

bkit 의 'live-run freshness' 패턴 (ref/bkit-reference-notes.md 1.12): 이 테스트는 훅이 지금 동작한다는 증명이 아니라,
**이 hooks.json 에 대해** 사람이 실세션 검증을 했다는 증명이다. hooks.json 을 바꾸면 실세션을 다시 돌려 live-run.json 을 갱신해야 한다.
"""
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_live_run_matches_current_hooks_json():
    ev = json.loads((REPO / "tests/contract/live-run.json").read_text(encoding="utf-8"))
    cur = hashlib.sha256((REPO / "hooks/hooks.json").read_bytes()).hexdigest()
    assert ev["hooks_json_sha256"] == cur, (
        "hooks.json 이 실세션 검증 이후 바뀌었습니다. `claude -p ... --plugin-dir` 로 다시 검증하고 "
        "tests/contract/live-run.json 의 hooks_json_sha256 과 observed 를 갱신하세요."
    )
    for ev_name in ("SessionStart", "PostToolUse(Write docs/**/*.md)", "Stop"):
        assert ev["observed"].get(ev_name), ev_name
