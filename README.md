# autodocs

## 프로젝트 목적

AI 코딩 도구(Claude, Codex, Gemini)로 작업하는 모든 프로젝트가 **같은 구조·같은 문서·같은 절차**를 따르게 하는 엔진이다.
사람이 만든 표준(`standard/manifest.yaml`)을 단일 원천으로 두고, 신규 프로젝트는 표준대로 생성하고(`init`), 기존 프로젝트는 표준으로 옮기는 계획을 만들며(`adopt`), 작업 전후에 준수 여부를 판정한다(`audit` / `check`).

## 주요 기능

- `autodocs audit` — 프로젝트를 한 번 스캔해 `new / legacy / partial / compliant` 상태와 위반 목록을 출력
- `autodocs init` — 표준 디렉터리·계층·필수 문서·AI 포인터 파일(CLAUDE.md 등) 생성. 기존 파일은 절대 덮어쓰지 않음
- `autodocs adopt` — 기존 프로젝트에 마커·문서를 만들고, 소스 파일의 계층 배치 계획(PROP-000)을 생성
- `autodocs check` — `audit` 와 같으나 error 가 있으면 exit 1 (PR 게이트·hook 용). `--override <사유>` 는 긴급 탈출구
- 종료 코드: 0 통과 · 1 위반 · 2 엔진/사용 오류
- 검사 항목(C01~C11)과 문서 종류·갱신 규칙은 코드가 아니라 manifest 에 선언되어 있다

## 기술 스택

- Python 3.10+ (표준 라이브러리 + PyYAML)
- 배포: hatchling (`standard/` 는 빌드 시에만 패키지에 복사 — 원본은 저장소 루트 한 곳)

## 실행 방법

### Claude Code 플러그인으로 (권장)

이 저장소가 곧 플러그인이다 (`.claude-plugin/plugin.json`, `commands/`, `skills/`, `hooks/`, `bin/`).

```bash
claude --plugin-dir ~/projects/autodocs        # 개발 중: 세션 한정 로드
claude plugin validate ~/projects/autodocs      # 구조 검증
```

실세션 검증(Claude Code 2.1.270, `tests/contract/live-run.json`): `${CLAUDE_PLUGIN_ROOT}` 치환, SessionStart 주입, PostToolUse 조언, Stop 1회 알림 모두 확인됨. hooks.json 을 바꾸면 freshness 테스트가 재검증을 요구한다.

세션이 시작되면 SessionStart 훅이 `audit` 를 돌려 상태(new/legacy/partial/compliant)와 다음 행동을 컨텍스트로 주입한다.
그 뒤 `/std-init`(신규), `/std-adopt`(기존), `/std-audit`, `/std-check` 를 쓴다. 작업 절차는 `standard-workflow` 스킬이 안내한다.
`docs/**/*.md` 를 쓰면 PostToolUse 훅이 그 문서의 형식 문제만 조언하고(차단 없음), 턴이 끝날 때 Stop 훅이 error 가 남아 있으면 세션당 한 번 알린다.

### CLI 로

```bash
"~/projects/autodocs/bin/autodocs" --root /path/to/project audit      # 설치 없이, 저장소의 엔진·표준 사용
pip install -e ".[dev]" && autodocs --root /path/to/project audit    # 또는 설치
autodocs --root /path/to/project init --name my-app --kind web --language python --api --db
pytest
```

## 문서 안내

| 문서 | 경로 | 용도 |
|---|---|---|
| **표준 (SSOT)** | `standard/manifest.yaml` | 문서 종류·구조·계층·검사 규칙 선언 |
| 표준 결정 목록 | `standard/DECISIONS.md` | 확정/미확정 결정 항목 |
| 문서 템플릿 | `standard/templates/` | init 이 생성하는 문서의 원본 |
| Claude 플러그인 | `.claude-plugin/`, `commands/`, `skills/`, `hooks/`, `bin/` | 엔진 위의 얇은 어댑터. 규칙 본문 없음 |
| bkit 참조 노트 | `ref/bkit-reference-notes.md` | 어댑터 설계에서 가져온 것/가져오지 않은 것 |
| 근거 문서 | `ref/` | 표준의 사람용 설명서(초안) |
| 프로젝트 컨텍스트 | `docs/context/project-context.md` | AI·신규 참여자가 먼저 읽는 문서 |
| 아키텍처 | `docs/architecture/architecture.md` | 엔진의 4계층 구조 |
| 요구사항 | `docs/requirements/requirements.md` | 엔진이 만족해야 하는 요구 |
| 변경 이력 | `CHANGELOG.md` | 버전별 변경 |

이 프로젝트는 자신이 정의한 AI Harness Engineering Standard v0.1.0 을 스스로 따른다 (`.standard/project.yaml`, `autodocs audit` → compliant).
