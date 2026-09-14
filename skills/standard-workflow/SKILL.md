---
name: standard-workflow
description: 회사 엔지니어링 표준(AI Harness Engineering Standard)이 적용된 프로젝트에서 작업할 때 따르는 절차. `.standard/project.yaml` 이 있는 프로젝트에서 기능 구현·수정·문서 작업을 시작할 때, 또는 어떤 문서를 갱신해야 하는지 판단할 때 사용한다.
---

# 표준 작업 절차

규칙의 원천은 `${CLAUDE_PLUGIN_ROOT}/standard/manifest.yaml` 이다. 이 문서는 그 요약이며, 충돌하면 manifest 가 우선한다.

## 작업 시작

1. `docs/context/project-context.md` 를 읽는다. 프로젝트 규칙·현재 상태·용어집은 이 문서가 단일 원천이다. CLAUDE.md 는 포인터일 뿐이다.
2. `"${CLAUDE_PLUGIN_ROOT}/bin/autodocs" --root "$PWD" audit` 를 실행한다. `compliant` 가 아니면 먼저 그 문제를 사용자에게 알린다 (`new` → /std-init, `legacy` → /std-adopt).
3. 작업과 관련된 문서를 읽는다: `docs/requirements/requirements.md`(무엇을), `docs/architecture/architecture.md`(구조), 관련 `docs/adr/`.

## 영향 범위 판단 — 어떤 문서를 갱신하는가

**변경 영향이 있는 문서만** 갱신한다. 모든 문서를 손대지 않는다. manifest `docs.types.*.update_triggers` 기준:

| 이런 변경이면 | 이 문서를 |
|---|---|
| 요구사항 추가·변경·삭제 | `docs/requirements/requirements.md` (REQ-nnn) |
| 계층·모듈 책임·외부 연동·주요 데이터 흐름 변경 | `docs/architecture/architecture.md` (Mermaid 포함) |
| Endpoint·Schema·인증·오류 응답 변경 | `docs/api/openapi.yaml` — Markdown 에 중복 작성 금지 |
| Table·Column·Relation·Index 변경 | `docs/database/database.md` (Mermaid ERD) |
| Framework 도입·DB 변경·인증 방식·구조 변경·핵심 통신 방식 | `docs/adr/ADR-nnn.md` — 이유와 대안을 함께 |
| 타인 담당 기능·UI/UX·업무 프로세스·여러 모듈 영향·사전 합의 필요 | `docs/proposals/PROP-nnn.md` 먼저, 구현은 합의 후 |
| 프로젝트 목적·주요 기능·실행 방법·기술 스택 | `README.md` |
| Release·작업 현황·용어·공통 규칙 | `docs/context/project-context.md` |
| PR Merge | `CHANGELOG.md` `[Unreleased]` |

갱신 대상이 아닌 것: 단순 클래스 추가, 작은 기능 구현, 변수명 변경, 작은 버그 수정.

## 구현

- 새 코드는 **L2(features)** 에서 시작한다. 프로젝트 고유 설정은 L3, 외부 시스템 접근은 L1, 공통 기반만 L0.
- 의존성은 위→아래만 (L3 → L2 → L1 → L0). L0 는 상위를 모른다. 위반은 `check` 의 C05 가 잡는다.
- 계층 디렉터리는 `.standard/project.yaml` 의 `layout_preset` 이 정한다 (manifest `structure.presets`).

## 작업 종료

1. 테스트를 실행한다.
2. 영향 받은 문서를 갱신했는지 위 표로 다시 확인한다. 코드와 문서는 같은 PR 에 들어간다.
3. `"${CLAUDE_PLUGIN_ROOT}/bin/autodocs" --root "$PWD" check` 를 실행해 통과시킨다. `--override` 는 사람이 사유를 적어 쓰는 탈출구이며 AI 가 스스로 쓰지 않는다.
4. `CHANGELOG.md` 의 `[Unreleased]` 에 한 줄 추가한다.
