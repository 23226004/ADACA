# manifest.yaml 확정을 위한 결정 목록

`standard/manifest.yaml` 에서 `[D-xx]` 로 표시된 항목이다. 각 항목은 현재 manifest 에 **권장안이 임시로 들어가 있으며**, 결정되면 manifest 값을 확정하고 주석을 제거한다.

결정이 엔진(init/audit)의 동작을 직접 바꾸는 순서대로 배열했다. D-01 ~ D-05 가 결정되면 엔진 구현을 시작할 수 있다.

**현황 (2026-09-14):** D-01, D-02, D-03, D-04, D-05 확정. D-02(프리셋), D-06~D-10 은 열려 있으나 엔진 골격 구현을 막지 않는다 — 기본값으로 진행하고 확정 시 manifest 값만 바꾼다.

---

## D-01. 4계층 디렉터리 이름 — ✅ 확정: `foundation / platform / features / customization` (2026-09-14)

두 초안이 서로 다른 이름을 쓴다.

| 계층 | 제안서 예시 | Project Structure Standard | 권장 |
|---|---|---|---|
| L0 | `Core` | `foundation` | `foundation` |
| L1 | `Platform` | `platform` | `platform` |
| L2 | `Modules` | `features` | `features` |
| L3 | `Project` | `customization` | `customization` |

권장 근거: 소문자 단수/복수 혼용 없이 역할을 그대로 드러내고, `Project` 는 최상위 개념과 이름이 충돌한다. `Core` 는 "핵심 비즈니스"로 오해될 여지가 있다.

결정 필요: 위 권장안 채택 여부. 대소문자 규칙(C# 은 PascalCase 관례)은 D-02 프리셋에서 흡수 가능.

## D-02. 언어·프레임워크별 레이아웃 프리셋 — ✅ 확정 (2026-09-14): import 해석은 preset `import_roots` 기준 + 실제 존재하는 경로만 계층으로 인정. Python 기본 preset 은 `python-package`, `generic` 은 비Python 용(Python 에 쓰면 경고). 프레임워크 진입점은 `entry_dirs` 로 선언해 L2 진입점으로 취급

프레임워크가 구조를 강제하는 경우(SvelteKit `src/routes`, .NET 솔루션의 프로젝트 분리, Python 패키지 `src/{pkg}/`) 4계층을 어디에 두는지 정해야 한다. manifest 의 `structure.presets` 에 초안 4개(generic, python-package, dotnet-solution, sveltekit)를 넣었다.

결정 필요:
1. 1차 버전에서 지원할 프리셋 범위 (사내 주력 스택 기준. CAD Add-on = .NET, 웹 = Svelte + FastAPI 로 추정)
2. 프레임워크 강제 디렉터리(`src/routes` 등)를 "L2 의 얇은 진입점"으로 취급하는 원칙에 동의하는지

## D-03. 필수 / 조건부 / 선택 문서 구분 — ✅ 확정: 표 그대로, Requirements 는 required (2026-09-14)

문서 표준은 9종을 나열하지만 필수 여부를 명시하지 않는다. manifest 초안의 구분:

| 구분 | 문서 | 판정 기준 |
|---|---|---|
| required | README, Project Context, Requirements, Architecture, CHANGELOG | 항상 |
| conditional | API(OpenAPI) | `has_api == true` |
| conditional | Database | `has_database == true` |
| optional | Proposal, ADR, Release Note | AI 판단 또는 사람 요청 |

결정 필요: 이 구분에 동의하는지. 특히 **Requirements 를 required 로 둘지** — 작은 도구성 프로젝트에도 요구사항 명세서를 강제할지가 실무 부담을 좌우한다.

## D-04. Project Context 문서 신설 — ✅ 확정: `docs/context/project-context.md` required, 앱별 파일은 포인터 (2026-09-14)

제안서의 5축에는 Project Context 가 있으나 문서 표준 9종에는 대응 문서가 없다. manifest 는 `docs/context/project-context.md` 를 required 로 신설했고, `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` 는 이 문서를 가리키는 **포인터**로만 쓰도록 했다.

근거: 세 앱마다 규칙 본문을 따로 두면 반드시 어긋난다. 규칙은 한 곳, 어댑터 파일은 "여기를 읽어라" 한 줄.

결정 필요:
1. 신설 동의 여부와 경로 (`docs/context/project-context.md` vs 루트 `PROJECT_CONTEXT.md`)
2. README 와의 역할 분리 — README 는 사람용 진입점, Project Context 는 AI 용 작업 컨텍스트(현재 상태·작업 현황·용어집 포함)로 나누는 안

## D-05. 준수 마커와 상태 판정 — ✅ 확정: `.standard/project.yaml`, 4상태 (2026-09-14)

엔진이 신규/기존을 구분하려면 결정론적 신호가 필요하다. 초안은 `.standard/project.yaml` (프로젝트 프로필 + pin 된 표준 버전)을 마커로 쓰고, 4가지 상태를 둔다.

| 상태 | 조건 | 어댑터 동작 |
|---|---|---|
| new | 마커 없음, 코드 없음 | `init` |
| legacy | 마커 없음, 코드 있음 | `adopt` (AI 리팩토링 + 엔진 검증) |
| partial | 마커 있음, 위반 있음 | 위반 목록 기준 수정 |
| compliant | 마커 있음, 위반 없음 | 정상 작업 |

결정 필요: 마커 위치·이름, "코드 있음"의 판정 기준(예: `src/` 존재 또는 소스 파일 N개 이상).

## D-06. 문서 언어와 식별자 규칙

초안 예시는 본문 한국어 + 식별자·헤딩 키워드 영문(`REQ-001`, `Status`, `Added`)이다. manifest 는 이를 그대로 반영했다.

결정 필요: 이 혼용 원칙 확정 여부, ID 자릿수(`001` 3자리로 충분한지).

## D-07. 표준 버전 관리

표준 자체도 바뀐다. 프로젝트가 표준 버전을 pin 하지 않으면 `audit` 결과가 표준 개정 시점에 따라 달라진다.

결정 필요: SemVer 로 관리하고 프로젝트가 `.standard/project.yaml` 에 pin 하는 안. 표준 개정 시 마이그레이션 책임(엔진 `migrate` 명령 vs 수동).

## D-08. Release Note 위치

`docs/releases/v1.0.0.md` 파일로 둘지, GitHub Releases 를 원본으로 삼고 파일은 생성물로 볼지. GitHub Workflow 축이 정해지면 자연히 결정된다.

## D-09. `config/`, `tools/`, `.github/` 필수 여부

구조 표준에는 있으나 역할 정의가 없다. 초안은 optional. `.github/` 는 GitHub Workflow 축(브랜치 전략, PR 템플릿) 확정 후 required 로 올리는 것을 권장.

## D-10. Definition of Done

제안서 3축(Development Workflow)의 "제어해야 하는 부분"에 있으나 내용이 없다. manifest 에 4항목 초안(테스트 통과, check 통과, 문서 갱신, PR 템플릿)을 넣었다. 리뷰 승인 수 등은 GitHub Workflow 축과 함께 결정.

---

## 범위 밖으로 둔 것 (1차 버전)

- 모노레포 / 다중 패키지 프로젝트
- GitHub Workflow 축 상세 (브랜치 전략, 커밋 컨벤션, PR 템플릿) — 별도 문서로 작성 예정
- Codex / Gemini 어댑터 구현 — Claude 플러그인 완성 후
