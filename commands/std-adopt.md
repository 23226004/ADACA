---
name: std-adopt
description: 기존 프로젝트에 표준 마커·문서·계층 디렉터리를 만들고, 소스 파일의 계층 배치 계획서(PROP-000)를 생성한다. 코드는 옮기지 않는다
allowed-tools: Bash(python3 *), Bash(*/bin/autodocs *), Read, Glob, AskUserQuestion
---

이 명령은 두 단계로 나뉜다. **1단계는 엔진이 결정론적으로, 2단계는 사람과 AI 가 판단해서** 한다.

## 1단계 — 엔진

1. 프로필을 확보한다. 인자에 `--name`, `--kind`, `--language` 가 모두 있으면 묻지 않는다. 빠진 값은 저장소를 훑어(pyproject.toml, package.json, *.csproj, routers/, migrations/ 등) **제안**하고 AskUserQuestion 으로 확인받는다. `--api` / `--db` 는 근거(라우터·마이그레이션 폴더)가 보일 때만 제안한다.
2. 실행:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/autodocs" --root "$PWD" adopt --name <name> --kind <kind> --language <language> [--api] [--db] $ARGUMENTS
```

3. 생성된 `docs/proposals/PROP-000-adopt-standard.md` 를 연다. "미분류 소스 파일" 표가 계층 배치 대상이다.

## 2단계 — 계획서 채우기 (코드 이동은 아직 하지 않는다)

4. 표의 각 파일에 대해 목적지 계층과 이유를 제안한다. 판단 원칙은 `${CLAUDE_PLUGIN_ROOT}/standard/manifest.yaml` 의 `structure.layers[].role` 과 `change_resolution_order`: 가능하면 L2(features), 외부 시스템 접근은 L1(platform), 프로젝트 고유 설정은 L3(customization), 공통 기반만 L0(foundation).
5. 제안을 표에 채워 넣고 사용자에게 검토를 요청한다. **파일 이동·import 수정은 사용자가 계획서를 승인한 뒤 별도 작업으로** 한다.
6. 이동을 실행할 때는 계층 하나씩 옮기고 매번 `check` 를 돌려 C05(의존성 방향) 위반을 확인한다.
