# Changelog

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 를 따르고, 버전은 SemVer 를 따른다.
갱신 시점: PR Merge(Unreleased 에 추가), Release(버전 헤딩으로 확정).

## [Unreleased]

### Added

- 표준 SSOT `standard/manifest.yaml` v0.1.0 — 문서 10종, 4계층, 검사 C01~C11, 4상태
- 결정 목록 `standard/DECISIONS.md` (D-01·03·04·05 확정)
- 문서 템플릿 11종 `standard/templates/`
- 엔진 `src/autodocs/` — `audit` / `check` / `init` / `adopt`
- 단위 테스트 14개 (생명주기, 의존성 방향, manifest-코드 정합)
- 저장소 자체에 표준 적용 (dogfooding)

### Changed

- 엔진이 쓰거나 읽는 모든 상대 경로는 `norm_rel` / `fs.safe_path` 를 거친다 — 절대경로·`..`·심볼릭 링크·null byte 거부 (PROP-001 A)
- `.standard/project.yaml` 은 init/adopt 재실행 시 절대 덮어쓰지 않음
- "코드 있음" 판정 규칙을 manifest `compliance.code_detection` 으로 이동 (빈 src/, tests/ 만 있는 경우는 new)
- `--standard` / `AUTODOCS_STANDARD_DIR` 가 틀리면 폴백 없이 오류
- `check --override <사유>`: 위반이 있어도 exit 0, 사유를 출력에 남김 (긴급 탈출구)
- 종료 코드 확정: 0 통과 · 1 위반 · 2 엔진/사용 오류 (모든 예외 포함)
- `Snapshot.read` 캐시 — 파일당 디스크 읽기 1회
- 출력 아이콘을 ASCII 로 (cp949 콘솔 대응)

### Fixed

- `adopt --no-adapters` 가 무시되던 문제
- 잘못된 `project.yaml` / `openapi.yaml` (타입·YAML 문법) 이 트레이스백 대신 finding(C00/C08) 으로 보고됨
- 알 수 없는 `layout_preset`, 비ASCII 프로젝트 이름이 조용히 폴백되던 문제 → ProfileInvalid
- `adopt` 계획서의 미분류 목록에서 tests/·docs/·tools/ 제외
- C01·C03 이 README/CHANGELOG 누락을 이중 보고하던 문제
- `%%{init}` 지시어가 앞에 오면 mermaid 블록을 못 찾던 문제
- `has_file("/x")` 와 `read("/x")` 의 정규화 불일치
- (재검증 2·3차) 비ASCII 프로젝트명 generic preset 거부, root 내부 심링크 거부와 반쪽 초기화, 읽기 경로 심링크 미검사, `$HOME` 잔존 변수 오탐, `--override` 무흔적, code_detection 기본값 이중화, 심링크 루프 크래시, FIFO 블록, 권한 오류 크래시, C00 중복, `AUTODOCS_STRICT=0` 오해석, 섹션 헤딩 과잉 엄격
