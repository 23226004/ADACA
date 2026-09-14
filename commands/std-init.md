---
name: std-init
description: 새 프로젝트를 회사 표준 구조와 필수 문서로 초기화한다 (기존 파일은 절대 덮어쓰지 않음)
allowed-tools: Bash(python3 *), Bash(*/bin/autodocs *), Read, AskUserQuestion
---

1. 먼저 `"${CLAUDE_PLUGIN_ROOT}/bin/autodocs" --root "$PWD" audit` 를 실행해 상태를 확인한다. `legacy` 면 이 명령 대신 `/std-adopt` 를 안내하고 멈춘다.
2. 프로필이 인자로 주어지지 않았으면 AskUserQuestion 으로 묻는다. 물어볼 것은 프로젝트 이름(영문·숫자·하이픈), 종류(kind), 언어, API 제공 여부, 데이터베이스 사용 여부. 허용값은 `${CLAUDE_PLUGIN_ROOT}/standard/manifest.yaml` 의 `project_profile.schema` 를 읽어 그대로 제시한다. preset 은 묻지 않는다 — 언어별 기본값이 있다.
3. 실행:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/autodocs" --root "$PWD" init --name <name> --kind <kind> --language <language> [--api] [--db] $ARGUMENTS
```

4. 출력의 `+`(생성) / `=`(유지) 목록을 그대로 보여준다. `!` 경고가 있으면 함께 보여준다.
5. 생성된 `docs/context/project-context.md` 를 열어 `_TODO_`/`_이탤릭_` 자리를 사용자와 함께 채운다. 이 문서가 이후 모든 AI 작업의 출발점이다. README 의 프로젝트 목적도 같이 채운다.
6. 마지막에 `check` 를 실행해 compliant 를 확인한다.
