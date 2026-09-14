# 프로젝트 컨텍스트 — autodocs

> AI 도구와 신규 참여자가 작업 전에 가장 먼저 읽는 문서. **현재 상태**만 적는다. 과거 이력은 ADR·CHANGELOG·Git 에서 찾는다.

## 프로젝트 요약

회사 엔지니어링 표준(문서·구조·워크플로우)을 AI 코딩 도구가 실제로 따르게 만드는 도구.
세 층으로 나뉜다: (1) `standard/` — 도구 중립 표준 데이터(SSOT), (2) `src/autodocs/` — 결정론적 Python 엔진, (3) 앱별 얇은 어댑터(Claude plugin 먼저, Codex·Gemini 는 이후).
판단이 필요 없는 일(구조 생성, 검사)은 엔진이, 판단이 필요한 일(기존 코드의 계층 분류, 문서 내용 작성)은 AI가 한다.

## 현재 상태

- 단계: 개발 (엔진 v0.1.0 — PROP-001 리뷰 1~5단계 전부 반영, 어댑터 미착수)
- 최신 버전: 0.1.0 (미배포)
- 표준 버전: 0.1.0 — 결정 D-01~05 확정, D-06~10 열림 (`standard/DECISIONS.md`)

## 기술 스택

- Python 3.10+, PyYAML, pytest, hatchling
- 외부 서비스 연동 없음. 네트워크 사용 없음.

## 아키텍처 요약

계층 구조 (상세: `docs/architecture/architecture.md`)

- L0 foundation: `src/autodocs/foundation/` — 타입(계약)·예외·경로 정책(norm_rel/safe_path). 표준 라이브러리만.
- L1 platform: `src/autodocs/platform/` — 파일 시스템 스캔, YAML, 표준 위치 탐색·manifest 스키마 검증, import 추출
- L2 features: `src/autodocs/features/` — layout·profile·state·checks·init·adopt·audit·report
- L3 customization: `src/autodocs/customization/` — 비어 있음 (변형은 manifest 데이터로 표현)
- 진입점: `src/autodocs/cli.py` — argparse 디스패처, 판단 로직 없음

의존성은 위→아래(L3 → L0)만 허용. `autodocs check` 의 C05 가 이 저장소 자신에게도 적용된다.

## 공통 규칙

- **manifest 가 규칙의 원천이다.** 검사 항목·문서 종류·계층 이름을 코드에 하드코딩하지 않는다. 새 check 는 manifest 에 선언 + `features/checks/` 레지스트리에 등록, 둘 중 하나만 하면 테스트가 실패한다.
- 파일 시스템은 명령당 **한 번만** 걷는다 (`platform.fs.scan` → `Snapshot`). check 는 Snapshot 만 본다.
- `init` 은 기존 파일·마커를 절대 덮어쓰지 않는다. 엔진이 읽거나 쓰는 모든 경로는 `foundation.safe_path` 를 거친다 (manifest 값도 신뢰하지 않음). 심링크는 목적지가 root 안일 때만 허용.
- **대상 프로젝트의 입력은 엔진을 죽이지 않는다.** 잘못된 project.yaml, 권한 없는 파일, 심링크 루프, FIFO 는 finding 이 되지 exit 2 가 되지 않는다. exit 2 는 manifest·CLI·표준 위치 같은 엔진 쪽 문제에만.
- 엔진은 판단하지 않는다. "이 파일이 어느 계층인가" 같은 판단은 계획서(PROP-000)로 AI/사람에게 넘긴다.
- 코드와 문서는 같은 PR 에서 함께 변경한다. 작업 종료 전 `PYTHONPATH=src python -m autodocs check` 와 `pytest` 통과.

## 용어집

| 용어 | 정의 |
|---|---|
| manifest | `standard/manifest.yaml`. 표준의 기계 판독용 단일 원천 |
| 마커 | `.standard/project.yaml`. 프로젝트 프로필 + pin 된 표준 버전. 있으면 표준 적용 프로젝트 |
| 상태 | new(마커·코드 없음) / legacy(마커 없음, 코드 있음) / partial(마커 있음, 위반) / compliant |
| check | manifest `compliance.checks` 의 한 항목 (C01~C11). Snapshot 을 받아 Finding 목록을 돌려주는 순수 함수 |
| preset | 언어·프레임워크별 계층 디렉터리 배치와 import 해석 규칙 (`structure.presets`: layer_dirs, import_roots, aliases, entry_dirs) |
| 포인터 파일 | CLAUDE.md / AGENTS.md / GEMINI.md. 규칙 본문 없이 project-context 를 가리키기만 함 |
| adopt | 기존 프로젝트에 마커·문서·계층 디렉터리를 만들고 계층 배치 계획서를 내는 명령 |

## 현재 작업 현황

| 항목 | 상태 | 비고 |
|---|---|---|
| 엔진 골격 (init/adopt/audit/check, C01~C11) | 완료 | 단위 테스트 108개 |
| PROP-001 리뷰 수정 1~5단계 + 재검증 4회 | 완료 | `docs/proposals/PROP-001-engine-review.md` |
| 문서 템플릿 11종 | 완료 | `standard/templates/` |
| Claude Code 플러그인 (commands/skill/hook) | 다음 | manifest `adapters.claude` |
| Codex / Gemini 어댑터 | 예정 | Claude 완성 후 |
| 표준 결정 D-02, D-06~D-10 | 열림 | 기본값으로 진행 중 |

---
표준: AI Harness Engineering Standard v0.1.0
