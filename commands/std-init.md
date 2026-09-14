---
name: std-init
description: 새 프로젝트를 회사 표준 구조와 필수 문서로 초기화한다 (기존 파일은 절대 덮어쓰지 않음)
allowed-tools: Bash(sh *), Bash(python3 *), Bash(python *), Read, AskUserQuestion
---

1. 먼저 `sh "${CLAUDE_PLUGIN_ROOT}/bin/py.sh" "${CLAUDE_PLUGIN_ROOT}/bin/autodocs" --root "$PWD" audit` 를 실행해 상태를 확인한다. `legacy` 면 이 명령 대신 `/std-adopt` 를 안내하고 멈춘다.
2. 인자에 `--name`, `--kind`, `--language` 가 모두 있으면 **묻지 말고 바로 실행**한다. `--api` / `--db` 는 생략 시 "아니오" 이며 따로 묻지 않는다. 세 필수 값 중 빠진 것이 있을 때만 AskUserQuestion 으로 빠진 것을 묻는다(이름은 영문·숫자·하이픈). 허용값은 `${CLAUDE_PLUGIN_ROOT}/standard/manifest.yaml` 의 `project_profile.schema` 를 Read 로 읽어 그대로 제시한다. preset 은 묻지 않는다 — 언어별 기본값이 있다.
3. 실행:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/bin/py.sh" "${CLAUDE_PLUGIN_ROOT}/bin/autodocs" --root "$PWD" init --name <name> --kind <kind> --language <language> [--api] [--db] $ARGUMENTS
```

4. 출력의 `+`(생성) / `=`(유지) 목록을 그대로 보여준다. `!` 경고가 있으면 함께 보여준다.
5. 생성된 `docs/context/project-context.md` 를 열어 `_TODO_`/`_이탤릭_` 자리를 사용자와 함께 채운다. 이 문서가 이후 모든 AI 작업의 출발점이다. README 의 프로젝트 목적도 같이 채운다.
6. 마지막에 `check` 를 실행해 compliant 를 확인한다.
