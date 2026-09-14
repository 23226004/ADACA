# PROP-001 엔진 골격 v0.1.0 리뷰 결과와 수정 계획

- 작성일: 2026-09-14
- 상태: In Progress — 1·2단계 완료 + 재검증 2회(회귀 R1~R8, 입력 강건화 N1~N6) 반영 (2026-09-14), 3~5단계 남음
- 대상: `src/autodocs/` 첫 커밋 (78f5e1e)

## 요약

독립 리뷰(실험으로 재현 확인)에서 25건의 결함이 나왔다. 테스트 14건은 모두 통과하지만, 저장소가 스스로 내세운 원칙 중 세 가지가 실제로는 지켜지지 않고 있다.

| 원칙 | 주장 | 실제 |
|---|---|---|
| 비파괴 | init/adopt 는 덮어쓰지 않는다 | `.standard/project.yaml` 은 매번 덮어씀 |
| 읽기 1회 | 파일당 한 번만 읽는다 | CHANGELOG·architecture·database 각 2회 |
| 규칙은 manifest 에만 | 코드에 정책 없음 | `dependency_rules.allowed`·`applies_to` 는 무시되고, SKIP_DIRS·SOURCE_EXT·MIN_SOURCE_FILES·POINTER_MAX_LINES 등은 코드에 있음 |

## 결함 목록 (심각도 순)

### A. 보안 — root 밖으로 쓰기/읽기 (제로트러스트 위반)

1. manifest 의 `path:`, `pointer_file`, `layer_dirs`, `marker.path` 에 `../` 또는 절대경로를 넣으면 `--root` 밖에 파일 생성 (`fs.write_text`, `fs.ensure_dir` 에 가드 없음)
2. 대상 프로젝트의 깨진 심볼릭 링크(`CLAUDE.md → /outside`)를 따라가 외부에 파일 생성 (`path.exists()` 는 dangling symlink 에 False)
3. `template:` 로 임의 파일(`/etc/hostname`, `../x`)을 읽어 생성 문서에 삽입
4. preset 의 `{name}` placeholder 는 정제되지 않아 `--name ../../x` 로 탈출 가능

### B. 정확성 버그

5. `init`/`adopt` 가 `.standard/project.yaml` 을 항상 덮어쓰고 "created" 로 보고
6. `adopt --no-adapters` 가 무시됨 (cli 가 플래그를 안 넘김)
7. C05 오탐: generic/sveltekit preset 에서 `import platform`(stdlib), `from 'platform'`(npm) 이 L0→L1 상향 의존으로 보고됨. 기존 테스트가 이 오탐을 고정하고 있음
8. C05 누락: `from .. import features` 의 `names` 를 버려서 미검출
9. C05 정규식: TS side-effect import 미검출, C# `using X = …;`·`global using` 미검출, 주석 안 import 오탐
10. C05 가 조용히 통과: SyntaxError 시 파일 전체 무검사, `.java/.go/.rs` 는 항상 `[]`
13. 상태 판정: 빈 `src/` 만 있어도 legacy, `tests/` 파일 하나만 있어도 legacy; 프로필 `has_api: "no"` 가 truthy
21. `adopt` 미분류 목록에 `tests/`, `scripts/`, `src/routes/` 등 계층 이동 대상이 아닌 파일 포함
22. `Snapshot.has_file("/x")` 와 `read("/x")` 의 정규화 불일치 → 크래시
23. C01·C03 이 README/CHANGELOG 누락을 이중 보고; `%%{init}` 지시어·`graph TD` 있는 mermaid 미검출; 섹션 매칭이 부분 문자열
24. Python 3.10 `ast.parse` null byte → `ValueError` 미포착

### C. 원칙 위반 (SSOT)

11. `dependency_rules.allowed` 와 `checks[].applies_to` 를 코드가 읽지 않음 — manifest 를 바꿔도 동작 불변
12. 하드코딩 정책 상수: `SKIP_DIRS`(`bin`,`build` 가 모든 깊이에서 스킵 → `src/bin/` 무시), `SOURCE_EXT`, `MIN_SOURCE_FILES`, `POINTER_MAX_LINES`, `PLAN_REL`, `_FIELDS`(schema 복제), `$lib/` alias, `.gitkeep`, `C00`
19. 파일 중복 읽기 (Snapshot.read 캐시 없음, C08 은 Snapshot 우회)

### D. 견고성

14. 대상 프로젝트의 잘못된 `project.yaml`/`openapi.yaml`(타입 오류, YAML 문법 오류)이 트레이스백 exit 1
15. 잘못된 manifest(미지원 `when`, `severity: fatal`, 키 누락)도 트레이스백
16. `--root` 부재 → `state: new` exit 0 (오타를 조용히 통과); 파일이면 트레이스백
17. `--standard`/`AUTODOCS_STANDARD_DIR` 가 잘못되면 조용히 저장소 기본으로 폴백
18. 알 수 없는 preset → generic 으로 만들면서 project.yaml 엔 잘못된 이름 저장; 비ASCII 이름 → `src/project/`
20. Windows/macOS: 대소문자 무시 FS 에서 init/audit 모순; `✗ ↳` 가 cp949 에서 `UnicodeEncodeError`; 혼합 구분자
25. 종료 코드 충돌: 미포착 예외 = exit 1 = "위반 있음", argparse 오류 = exit 2 = "엔진 오류"

### E. 테스트 공백

cli 전체(종료 코드, --json, 플래그), init 재실행, 경로 탈출·심링크, 잘못된 입력, C06~C11 개별 케이스, `imports.py` 정규식, 읽기 1회 회귀 테스트, 저장소 자체 self-check.

## 수정 계획

진행: ✅ 1단계, ✅ 2단계 (+ 14·19·21·22·23 일부 선반영). 테스트 14 → 81건.

### 재검증 이력

- **2차 (1·2단계 적용 후)**: 25건 중 13 FIXED, 5 PARTIAL, 7 DEFERRED(3~5단계, 현재도 재현). 새 회귀 8건 발견:
  R1 비ASCII 이름이 generic preset 에서도 거부 + 기존 프로젝트 audit 이 exit 2 → placeholder 가 있을 때만 정제, check 내 ProfileInvalid 는 C00 finding.
  R2 root 안의 정상 심링크(`CLAUDE.md -> AGENTS.md`) 거부 + 중단 시 반쪽 초기화 → 정책을 "링크 목적지가 root 안이면 유지, 밖이면 거부" 로 바꾸고 init/adopt 가 쓰기 전 모든 대상을 preflight.
  R3 읽기는 root 밖 심링크를 따라감 → 읽기도 같은 정책. R4 standard 안 심링크 템플릿 → 같은 정책. R5 `$HOME` 잔존 변수 오탐 → 소문자 변수만.
  R6 `--override` 흔적 없음 → `.standard/overrides.log` 기록 + `AUTODOCS_STRICT=1` 금지. R7 code_detection 코드 기본값 이중화 → 제거(누락 시 ManifestInvalid). R8 = R1.
- **3차 (회귀 수정 후)**: R1~R8 전부 FIXED. 입력 강건화 6건 추가 발견·수정:
  N1 심링크 루프 → RuntimeError 가 아니라 PathEscape. N2 대상 프로젝트 문제로 audit 전체가 exit 2 → check 내 AutodocsError 는 해당 check 의 finding.
  N3 C00 중복 → 동일 finding 1회. N4 preflight 가 종류 불일치(디렉터리 자리에 파일)를 못 봄 → (rel, kind) 검증, adopt 의 PLAN_REL 포함.
  N5 `AUTODOCS_STRICT=0` 도 금지 → "1/true/yes" 만. N6 FIFO 에서 영구 블록·권한 없는 파일/디렉터리 크래시 → scan 은 일반 파일·심링크만, 읽기 실패와 읽을 수 없는 디렉터리는 finding.
  섹션 헤딩 매칭은 번호·강조·후행 부제/콜론을 무시하도록 정규화. overrides.log 가 심링크면 거부.
  테스트 결함 3건 수정(공허한 읽기 1회 단언, 표준 경로 격리, C00 중복 미검출).
- **남은 것**: #7~10·24 (C05, 4단계), #11·12 잔여 상수 (3단계), #15 manifest 스키마·#20 대소문자 무시 FS (5단계), #21 sveltekit `src/routes` (4단계 entry_dirs).

| 단계 | 범위 | 핵심 변경 |
|---|---|---|
| 1 | A 전부 + 22 | `fs` 에 단일 경로 가드 `safe_path(root, rel)` (resolve + is_relative_to + symlink 거부). manifest·profile·CLI 에서 온 모든 경로가 이 함수를 거친다. `template_path` 도 standard_dir 하위로 제한 |
| 2 | 5, 6, 13, 16, 17, 18, 25 | 마커 존재 시 skip; adopt 플래그 전달; `has_code` 를 manifest 규칙으로; `--root` 검증; explicit standard 는 폴백 금지; preset 검증; `cli.main` 이 모든 예외를 exit 2 로 |
| 3 | 11, 12, 19 | manifest 에 `scan.skip_dirs / source_ext`, `compliance.code_detection`, `adapters.pointer_max_lines`, preset `import_roots / entry_dirs` 추가. `dependency_rules.allowed` 를 실제로 읽음. `Snapshot.read` 캐시 |
| 4 | 7~10, 21, 23, 24 | C05 리졸버 재작성: import 는 preset 의 `import_roots` 기준으로만 해석하고, 해석된 경로가 Snapshot 에 존재할 때만 계층으로 인정. `names` 처리, 정규식 보강, 파싱 실패는 INFO. adopt 제외 목록 |
| 5 | 14, 15, 20 | `yaml_io` 에서 YAMLError → AutodocsError; manifest·profile 스키마 검증; 출력 ASCII 폴백 |
| 6 | E | 각 단계마다 회귀 테스트 추가. 목표 40건+ |

## 참고

- 리뷰 방법: 독립 에이전트가 소스 전체를 읽고 `/tmp` 에서 재현 실험. "확인" 표시는 실제 재현된 항목.
