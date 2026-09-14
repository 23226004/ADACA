#!/usr/bin/env python3
"""PostToolUse(Write|Edit on docs/**/*.md) — 방금 쓴 표준 문서의 형식 문제를 조언한다. 차단하지 않는다.

hooks.json 의 `if` 로 docs/ 아래 .md 만 걸리지만, 방어적으로 다시 확인한다.
해당 파일에 대한 finding 만 골라 additionalContext 로 전달한다.
"""
from pathlib import Path

from _common import emit, find_root, guarded, read_payload, run_audit


def main() -> None:
    payload = read_payload()
    fp = (payload.get("tool_input") or {}).get("file_path")
    if not fp:
        return
    root = find_root(payload)
    try:
        rel = Path(fp).resolve().relative_to(root).as_posix()
    except ValueError:
        return
    if not rel.endswith(".md"):
        return
    _, report = run_audit(root)
    mine = [f for f in report.findings if f.path == rel]
    if not mine:
        return
    lines = [f"[autodocs] {rel} 에 대한 표준 검사 결과 ({len(mine)}건):"]
    for f in mine[:8]:
        lines.append(f"  {f.severity.value}: [{f.check_id}] {f.message}" + (f" — {f.fix_hint}" if f.fix_hint else ""))
    emit({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "\n".join(lines)}})


guarded(main)
