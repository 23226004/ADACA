#!/usr/bin/env python3
"""Stop — 턴이 끝날 때 check 를 돌려 error 가 있으면 **세션당 한 번** Claude 에게 알린다.

- stop_hook_active 가 true 면 이미 Stop 훅이 돌고 있는 것 → 아무것도 하지 않음 (무한 루프 방지)
- Stop 에서 모델에게 내용을 전달하는 유일한 방법이 decision:block 이므로 그것을 쓰되,
  같은 세션에서 두 번째부터는 조용히 통과시킨다 (bkit 이 겪은 "훅이 턴을 계속 붙잡는" 문제 방지).
- 마커는 CLAUDE_PLUGIN_DATA(없으면 시스템 임시 디렉터리)에 session_id 별로 둔다. 프로젝트 안에는 아무것도 쓰지 않는다.
"""
import os
import tempfile
from pathlib import Path

from _common import emit, find_root, guarded, read_payload, run_audit, summarize


def _marker(session_id: str) -> Path:
    base = Path(os.environ.get("CLAUDE_PLUGIN_DATA") or tempfile.gettempdir()) / "autodocs-stop"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{session_id or 'nosession'}.notified"


def main() -> None:
    payload = read_payload()
    if payload.get("stop_hook_active"):
        return
    root = find_root(payload)
    if not (root / ".standard" / "project.yaml").is_file():   # 표준 적용 프로젝트가 아니면 침묵
        return
    _, report = run_audit(root)
    if report.ok:
        return
    marker = _marker(str(payload.get("session_id", "")))
    if marker.exists():
        return
    marker.touch()
    reason = summarize(report, limit=5) + "\n표준 위반이 남아 있습니다. 수정하거나, 사용자에게 알린 뒤 /std-check 로 확인하세요. (이 알림은 세션당 한 번만 표시됩니다)"
    emit({"decision": "block", "reason": reason,
          "hookSpecificOutput": {"hookEventName": "Stop", "decision": "block", "reason": reason}})


guarded(main)
