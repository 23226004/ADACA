#!/usr/bin/env python3
"""SessionStart — 프로젝트 준수 상태를 세션 컨텍스트로 주입한다.

SessionStart 에서는 plain stdout 이 그대로 Claude 의 컨텍스트가 된다.
new/legacy 면 어떤 커맨드를 쓸지, partial 이면 무엇이 빠졌는지 첫 메시지 전에 알게 한다.
"""
from _common import emit, find_root, guarded, read_payload, run_audit, summarize

_CMD = {"new": "/std-init", "legacy": "/std-adopt", "partial": "/std-audit", "compliant": None}


def main() -> None:
    payload = read_payload()
    root = find_root(payload)
    _, report = run_audit(root)
    text = summarize(report)
    cmd = _CMD.get(report.state.value)
    if cmd:
        text += f"\n권장: {cmd} 를 실행하거나 사용자에게 제안하세요."
    text += "\n작업 절차는 standard-workflow 스킬을 따르세요. 규칙의 원천은 docs/context/project-context.md 와 플러그인의 standard/manifest.yaml 입니다."
    emit(text=text)


guarded(main)
