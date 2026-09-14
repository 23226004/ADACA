# 프로젝트 컨텍스트 — $project_name

> AI 도구와 신규 참여자가 작업 전에 가장 먼저 읽는 문서. **현재 상태**만 적는다. 과거 이력은 ADR·CHANGELOG·Git 에서 찾는다.
> 갱신 시점: Release 완료, 작업 현황 변경, 용어·공통 규칙 변경.

## 프로젝트 요약

_한 문단. 목적, 사용자, 핵심 제약._

## 현재 상태

- 단계: _기획 / 개발 / 운영_
- 최신 버전: _v0.0.0_
- 최근 Release: _YYYY-MM-DD_

## 기술 스택

- 언어: $language
- 종류: $project_kind
- _프레임워크, DB, 외부 연동_

## 아키텍처 요약

계층 구조 (상세: `docs/architecture/architecture.md`)

$layer_dirs

의존성은 위→아래(L3 → L0)만 허용. 새 기능은 L2(features)에서 시작한다.

## 공통 규칙

- 코드와 문서는 같은 PR 에서 함께 변경한다. 변경 영향이 있는 문서만 갱신한다.
- API 계약은 `docs/api/openapi.yaml` 이 단일 원천이다. Markdown 에 중복 작성하지 않는다.
- 구조·ERD 는 Mermaid 로 그린다.
- 중요한 기술 결정은 `docs/adr/ADR-nnn.md` 로 남긴다 (이유와 대안 포함).
- 작업 시작: `autodocs audit` · 작업 종료: `autodocs check` 통과.

## 용어집

| 용어 | 정의 |
|---|---|
| _용어_ | _정의_ |

## 현재 작업 현황

| 항목 | 상태 | 비고 |
|---|---|---|
| _작업_ | _진행 중_ | _Issue #_ |

---
표준: AI Harness Engineering Standard v$standard_version · 생성일 $date
