# autodocs

## 프로젝트 목적

AI 코딩 도구(Claude, Codex, Gemini)로 작업하는 모든 프로젝트가 **같은 구조·같은 문서·같은 절차**를 따르게 하는 엔진이다.
사람이 만든 표준(`standard/manifest.yaml`)을 단일 원천으로 두고, 신규 프로젝트는 표준대로 생성하고(`init`), 기존 프로젝트는 표준으로 옮기는 계획을 만들며(`adopt`), 작업 전후에 준수 여부를 판정한다(`audit` / `check`).

## 주요 기능

- `autodocs audit` — 프로젝트를 한 번 스캔해 `new / legacy / partial / compliant` 상태와 위반 목록을 출력
- `autodocs init` — 표준 디렉터리·계층·필수 문서·AI 포인터 파일(CLAUDE.md 등) 생성. 기존 파일은 절대 덮어쓰지 않음
- `autodocs adopt` — 기존 프로젝트에 마커·문서를 만들고, 소스 파일의 계층 배치 계획(PROP-000)을 생성
- `autodocs check` — `audit` 와 같으나 error 가 있으면 exit 1 (PR 게이트·hook 용)
- 검사 항목(C01~C11)과 문서 종류·갱신 규칙은 코드가 아니라 manifest 에 선언되어 있다

## 기술 스택

- Python 3.10+ (표준 라이브러리 + PyYAML)
- 배포: hatchling (`standard/` 는 빌드 시에만 패키지에 복사 — 원본은 저장소 루트 한 곳)

## 실행 방법

```bash
pip install -e ".[dev]"
autodocs --root /path/to/project audit
autodocs --root /path/to/project init --name my-app --kind web --language python --api --db
pytest
```

소스 체크아웃에서 설치 없이 쓰려면 `PYTHONPATH=src python -m autodocs ...`.

## 문서 안내

| 문서 | 경로 | 용도 |
|---|---|---|
| **표준 (SSOT)** | `standard/manifest.yaml` | 문서 종류·구조·계층·검사 규칙 선언 |
| 표준 결정 목록 | `standard/DECISIONS.md` | 확정/미확정 결정 항목 |
| 문서 템플릿 | `standard/templates/` | init 이 생성하는 문서의 원본 |
| 근거 문서 | `ref/` | 표준의 사람용 설명서(초안) |
| 프로젝트 컨텍스트 | `docs/context/project-context.md` | AI·신규 참여자가 먼저 읽는 문서 |
| 아키텍처 | `docs/architecture/architecture.md` | 엔진의 4계층 구조 |
| 요구사항 | `docs/requirements/requirements.md` | 엔진이 만족해야 하는 요구 |
| 변경 이력 | `CHANGELOG.md` | 버전별 변경 |

이 프로젝트는 자신이 정의한 AI Harness Engineering Standard v0.1.0 을 스스로 따른다 (`.standard/project.yaml`, `autodocs audit` → compliant).
