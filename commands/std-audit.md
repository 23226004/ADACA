---
name: std-audit
description: 현재 프로젝트의 표준 준수 상태(new / legacy / partial / compliant)와 위반 목록을 본다
allowed-tools: Bash(python3 *), Bash(*/bin/autodocs *), Read
---

다음 명령을 실행하고 결과를 그대로 보여준 뒤, 상태에 따른 다음 행동을 한 줄로 안내하라. 결과를 요약하거나 재해석하지 말 것.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/autodocs" --root "$PWD" audit $ARGUMENTS
```

- `new` 이면 `/std-init`, `legacy` 이면 `/std-adopt` 를 제안한다.
- `partial` 이면 error 항목만 골라 어떤 파일을 만들거나 고쳐야 하는지 목록으로 정리한다. 고치기 전에 사용자에게 확인한다.
- `compliant` 이면 아무것도 제안하지 않는다.
