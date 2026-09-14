# bkit 참조 노트 — autodocs 에 가져올 것과 가져오지 않을 것

- 대상: popup-studio-ai/bkit-claude-code v2.1.38 (Apache-2.0), 2026-09-14 소스 직접 분석
- 목적: Claude Code 플러그인 어댑터 설계와 엔진 수정 계획(PROP-001)에 반영할 메커니즘 추출
- 원칙: bkit 의 **메커니즘**(패키징·훅 계약·상태 감지·설정 해석·테스트)만 가져오고, PDCA 방법론·44 스킬·34 에이전트 같은 **내용과 규모**는 가져오지 않는다. autodocs 의 가치는 작고 결정론적이라는 데 있다.

## 1. 가져올 것

### 1.1 플러그인 패키징 — 컨벤션 디스커버리, 최소 manifest

`.claude-plugin/plugin.json` 은 `name / version / description` 정도만 두고, `skills/<name>/SKILL.md`, `commands/<name>.md`, `agents/<name>.md`, `hooks/hooks.json` 은 디렉터리 컨벤션으로 발견되게 한다. bkit 은 `displayName` 같은 신규 키가 구버전 Claude Code 에서 "Unrecognized key" 로 설치 실패를 냈다. 키를 늘릴수록 호환 리스크가 커진다.

SKILL.md frontmatter 의 `description` 은 항상 프롬프트에 상주하므로 짧게 유지한다(bkit 은 8개 언어 트리거를 넣었다가 토큰 비용 때문에 철회).

`context: fork` 스킬은 서브에이전트 경계에서 AskUserQuestion 이 제거된다. 사용자 확인이 필요한 `/std-adopt` 는 fork 를 쓰지 않는다.

### 1.2 hooks.json 계약 — 코드로 못박을 것

bkit 이 릴리스에 실어 보낸 결함들이 전부 hooks.json **설정** 오류였고, 6,398개 assertion 이 초록인 채로 살아남았다. 다음을 `tests/contract/test_hooks_json.py` 로 고정한다.

| 계약 | 내용 |
|---|---|
| timeout 단위 | **초**. 1~60 범위. (bkit 은 1000배 틀린 채 33개 버전을 지나 세션이 15분 멈추는 이슈를 냈다) |
| `if` | permission rule **정확히 하나**, `\|` 대체 불가. Write 용·Edit 용 핸들러를 따로 등록 |
| `if` 평가 이벤트 | PreToolUse / PostToolUse / PostToolUseFailure / PermissionRequest / PermissionDenied 에서만 |
| `matcher` | Stop, UserPromptSubmit 등 10개 이벤트에는 두지 않음 |
| `once` | hooks.json 에서는 무시됨 |
| command | 모두 `${CLAUDE_PLUGIN_ROOT}` 기준이며 실제 파일로 resolve 되어야 함 |

### 1.3 훅 출력 규약

대부분 이벤트에서 **bare stdout 은 모델에 도달하지 않는다**(디버그 로그로만 감). SessionStart 와 UserPromptSubmit 만 예외. 모델에게 전달하려면 `{"hookSpecificOutput": {"hookEventName": "...", "additionalContext": "..."}}`, 차단은 `{"decision": "block", "reason": "..."}`. Stop 에서 내용을 노출하는 유일한 스키마 유효 방법도 `decision: block` 이다.

훅 출력 상한은 10,000자(초과 시 파일로 빠지고 프리뷰만 남음). bkit 은 8,000자로 자체 캡을 걸고 `MANDATORY` 같은 우선 섹션을 먼저 확보한다. autodocs 의 audit 출력도 findings 가 많을 때 절단 규칙이 필요하다.

훅 입력 페이로드 키는 **추측하지 말고 실측**한다. bkit 은 존재하지 않는 키(`bypassPermissions`)를 읽어 가드가 한 번도 발화하지 않은 적이 있다. 실측 키: `cwd, hook_event_name, permission_mode, session_id, tool_input{file_path, content, command, old_string}, tool_name, transcript_path`.

### 1.4 "Guide, don't block" — 차단 등급 분리

bkit `pre-write.js` 는 10단계 파이프라인이지만 실제로 차단하는 것은 **보안 규칙 3개뿐**이다: `DENIED_PATH`, `SYMLINK_ESCAPE`, `NULL_BYTE`. 나머지(컨벤션, 영향 범위, 정책)는 전부 additionalContext 로 조언한다. `PATH_TRAVERSAL` 을 일부러 뺀 이유가 기록돼 있다 — cwd 밖이면 무조건 발화해서 `/tmp` 스크래치 쓰기까지 막았기 때문.

autodocs 적용: 엔진의 `safe_path` 가드(PROP-001 A)는 **엔진 자신이 쓰는 경로**에만 적용하고, PreToolUse 훅은 AI 의 Write 를 차단하지 않는다. 훅은 "이 파일은 L0 인데 L2 를 import 하려는 것 같다" 수준의 조언만 한다. 차단은 PR 게이트(`check`)에서.

### 1.5 SessionStart 설계

- 상태 감지는 **마커 파일**로(bkit: `.bkit/state/pdca-status.json`, autodocs: `.standard/project.yaml`). 코드베이스 스캔은 마커 없을 때만 → 우리 `audit` 가 이미 이 구조.
- 모든 단계를 `try/except` 로 감싸 **fail-open**. 세션 시작을 막느니 기능 하나가 죽는 게 낫다.
- timeout 10초. 무거운 일은 지연 로드. stdin 은 유계 읽기.
- 주입 내용: 상태(new/legacy/partial/compliant) + 다음 행동 한 줄 + error 요약. 첫 실행이면 first-run 마커로 온보딩 1회.
- 감지 결과를 `CLAUDE_ENV_FILE` 에 export 해 후속 훅 서브프로세스에 전파(재스캔 방지).

### 1.6 프로젝트 유형 자동 감지 (`detectLevel` 패턴)

루트 1-depth `readdir` 한 번으로 마커 파일을 보고 분류한다. autodocs 의 `adopt` 가 `--language / --preset` 기본값을 자동 제안하는 데 그대로 쓴다.

| 마커 | 추론 |
|---|---|
| `pyproject.toml`, `requirements.txt` | language=python, preset=python-package |
| `*.sln`, `*.csproj` | language=csharp, preset=dotnet-solution |
| `svelte.config.js` + `package.json` | language=typescript, preset=sveltekit |
| `package.json` | language=typescript, preset=generic |
| `openapi.yaml` / `routers/` / `controllers/` | has_api 제안 |
| `alembic/`, `migrations/`, `*.sql`, `prisma/` | has_database 제안 |

이건 **제안**이며 최종 값은 사람이 확정한다(엔진은 판단하지 않는다 원칙 유지). manifest 에 `detection.markers` 로 선언.

### 1.7 다중 후보 경로 (`findDoc` 패턴)

```json
"design": ["docs/02-design/features/{feature}.design.md", "docs/02-design/{feature}.design.md", "docs/design/{feature}.md"]
```

후보를 순서대로 `access` 해 첫 성공을 채택. **기존 프로젝트의 제각각인 폴더 구조를 흡수하는 가장 싼 방법**. autodocs manifest 의 `docs.types.*.path` 를 문자열 또는 리스트로 허용하고, `init` 은 첫 후보에 생성, `audit` 은 아무 후보나 있으면 통과, `adopt` 는 발견된 위치를 계획서에 기록한다.

### 1.8 Docs-Code Sync — "선언 = 실측"

bkit `docs-code-sync.js` 는 문서에 적힌 숫자(스킬 44개, 훅 21개…)와 파일시스템 실측치를 대조한다. README/CHANGELOG 는 릴리스 스냅샷이므로 **의도적으로 제외**하고 plugin.json 만 대상.

autodocs 적용: C12 `declared_vs_measured` — architecture.md 의 계층 매핑 ↔ 실제 디렉터리, project-context 의 "최신 버전" ↔ pyproject/package.json 버전, CHANGELOG 최신 헤딩 ↔ 패키지 버전. 점진적 롤아웃(`enforce` 집합에 든 항목만 error, 나머지 warning)도 함께.

### 1.9 탈출구

`check-self-dogfood.sh` 는 `--bootstrap-mode` 와 `--emergency-override <reason>` 을 제공한다. 회사 리포 전체에 `check` 를 PR 게이트로 걸면 반드시 필요하다. `autodocs check --override "<사유>"` 는 통과시키되 사유를 출력과 exit code(0 이 아닌 별도 코드)에 남긴다.

### 1.10 설정 우선순위 — bkit 의 실수를 피한다

bkit 은 프로젝트 `bkit.config.json` 이 있으면 플러그인 기본값을 **통째로 무시**(first-wins). 누락 키가 코드 기본값으로 떨어져 드리프트가 생겼다. autodocs 는 회사 manifest 를 기준으로 `.standard/project.yaml` 이 **허용된 키만 deep-merge** 하게 한다(허용 키 목록도 manifest 에 선언).

### 1.11 템플릿 변수 린터

bkit 은 `{{var}}` 와 `{UPPER}` 를 섞어 쓴 템플릿 6개가 치환되지 않은 채 생성 문서로 새어 나갔다. autodocs `init` 은 렌더 후 잔존 `$identifier` 를 검출해 warning 을 내고, 템플릿 디렉터리 전체를 검사하는 테스트를 둔다.

### 1.12 테스트 — 등록되지 않은 테스트는 문서다

bkit 은 통과하지만 어느 러너에도 등록되지 않은 테스트 148개를 발견했다. 그중 하나가 실제 드리프트를 잡고 있었다. 또 `continue-on-error: true` 로 11개 버전 동안 아무것도 검증하지 않은 strict 검사가 있었다. autodocs 는 pytest 가 `tests/` 전체를 자동 수집하고, CI 에는 advisory 스텝을 두지 않는다.

L6 "live-run freshness": 실제 Claude Code 세션에서 훅이 발화했다는 증거(관측 이벤트, hooks.json SHA-256)를 커밋하고, hooks.json 해시가 바뀌면 CI 가 빨간불. 어댑터 완성 후 도입 검토.

## 2. 가져오지 않을 것

- PDCA 방법론, 44 스킬, 34 에이전트, 22 훅 이벤트, MCP 서버 2개, 195 lib 모듈. autodocs 는 커맨드 4개·스킬 1개·훅 3개 이내로 유지한다.
- 매 Write 마다 도는 10단계 파이프라인. autodocs 훅은 Write 시점에 엔진을 돌리지 않는다(SessionStart 1회 + Stop/PR 게이트).
- match-rate 기반 자동 반복 수정. 판단은 사람/AI, 엔진은 검증만.
- 세션 제목 변경, 대시보드, 토큰 예산 — 범위 밖.

## 3. bkit 에 없어서 autodocs 가 직접 설계해야 하는 것

- **기존 프로젝트 adopt**: bkit 에는 실행 가능한 brownfield 플로우가 없다(CUSTOMIZATION-GUIDE 의 4단계 산문뿐). 우리 `adopt` + PROP-000 계획서가 차별점.
- **계층 의존성 규칙**: bkit 의 "domain purity" 는 `lib/domain` 에 Node 내장 모듈 금지 하드코딩 하나. 일반 계층 행렬 검사(C05)는 우리가 새로 만든 것이 맞다.
- **프로젝트별 템플릿 오버라이드**: bkit 에 없음. 회사 표준 + 팀 오버라이드가 필요하면 새로 설계.
- **도구 중립 SSOT**: bkit 은 Claude Code 전용. Codex/Gemini 어댑터를 같은 manifest 위에 얹는 구조는 우리 것.

## 4. PROP-001 수정 계획에 반영

| PROP-001 단계 | bkit 참조로 추가·변경되는 것 |
|---|---|
| 1 (보안 가드) | 가드는 엔진 쓰기 경로에만. 훅에서는 차단하지 않음 (1.4) |
| 2 (버그·종료코드) | `--override <reason>` 탈출구 추가 (1.9) |
| 3 (manifest 로 정책 이동) | `docs.types.*.path` 리스트 허용 (1.7), `detection.markers` (1.6), `project_overrides.allowed_keys` (1.10) |
| 4 (C05 재작성) | 변경 없음 — bkit 에 참고할 것 없음 |
| 5 (입력 검증) | 렌더 후 잔존 변수 검출 (1.11) |
| 6 (테스트) | hooks.json 계약 테스트 (1.2), C12 declared-vs-measured (1.8) |
| 어댑터 (신규) | 1.1 / 1.3 / 1.5 전부 |
