---
name: std-check
description: PR 전 게이트. audit 와 같지만 error 가 있으면 실패(exit 1)한다
allowed-tools: Bash(sh *), Bash(python3 *), Bash(python *), Read
---

다음 명령을 실행하라.

```bash
sh "${CLAUDE_PLUGIN_ROOT}/bin/py.sh" "${CLAUDE_PLUGIN_ROOT}/bin/autodocs" --root "$PWD" check $ARGUMENTS
```

- exit 0: "표준 검사 통과" 한 줄만 보고한다.
- exit 1: error 항목마다 수정 방법을 제시하고, 사용자가 동의하면 수정한 뒤 다시 실행한다. 표준 위반을 우회하기 위해 `--override` 를 스스로 쓰지 않는다 — 그것은 사람이 사유를 적어 쓰는 탈출구다.
- exit 2: 엔진/설정 오류다. 메시지를 그대로 보여주고 멈춘다.
