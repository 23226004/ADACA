# PROP-002 엔진 구현에서 AI 가 내린 판단 목록 (검토 요청)

- 작성일: 2026-09-14
- 상태: Under Review
- 목적: 사용자가 명시적으로 결정한 것(D-01~D-05, bkit 참조 방향, 재검증 수용)을 제외하고, 구현 과정에서 AI 가 스스로 정한 판단을 전부 드러낸다. 각 항목은 그대로 두거나, 뒤집거나, DECISIONS.md 의 정식 결정으로 승격할 수 있다.
- 표기: **[판단]** 선택한 것 · **[대안]** 선택하지 않은 것 · **[근거]** 이유 · **[위치]** 코드/manifest

---

## A. 표준(manifest) 내용

### A1. 조건부 문서의 조건을 프로필 bool 플래그로
- [판단] API 문서는 `has_api == true`, DB 문서는 `has_database == true` 일 때만 필수. 프로젝트가 스스로 선언한다.
- [대안] 코드에서 자동 감지(라우터·마이그레이션 폴더 존재), 또는 항상 필수.
- [근거] 엔진은 판단하지 않는다는 원칙. 자동 감지는 adopt 의 "제안" 으로만 (bkit detectLevel 패턴, 미구현).
- [위치] manifest `docs.types.api.when`, `project_profile.schema.has_api`

### A2. Release Note 는 optional (D-08 미결정 상태의 기본값)
- [판단] `requirement: optional`. audit 가 존재를 요구하지 않는다.
- [대안] Release 를 하는 프로젝트 프로필 플래그(`does_release`)로 conditional.
- [위치] manifest `docs.types.release_note`

### A3. 프로필 스키마 필드와 enum 값
- [판단] `name, kind, language, has_api, has_database, layout_preset, standard_version`. kind 는 `cad-addon, web, desktop, cli, ai-agent, library, service`, language 는 `python, csharp, typescript, java, mixed`.
- [대안] kind 를 자유 문자열로; language 에 go/rust 추가; `team`/`owner` 같은 메타 필드.
- [근거] ref 문서의 예시(CAD Add-on, Web, Desktop, CLI, AI Agent)에서 뽑음. 사내 스택 확인 전 최소 집합.
- [위치] manifest `project_profile.schema`

### A4. preset 4개와 .NET 디렉터리 명명
- [판단] `generic / python-package / dotnet-solution / sveltekit`. .NET 은 `src/{Name}.Foundation` 처럼 프로젝트(.csproj) 단위 분리, namespace = 디렉터리명.
- [대안] .NET 을 단일 프로젝트 안의 폴더(`src/{Name}/Foundation`)로; FastAPI 전용 preset; Flutter preset.
- [근거] ref 문서가 "계층별 프로젝트 분리" 를 시사. 실제 사내 CAD Add-on 구조는 확인하지 못함.
- [위치] manifest `structure.presets`

### A5. `import_roots` 에 저장소 루트("") 포함
- [판단] `[src, ""]`. `import src.demo.features` 같은 루트 기준 import 도 해석.
- [대안] `src` 만. 루트 기준 import 는 어차피 권장 관례가 아니므로 무시.
- [근거] 4차 검증 A1 — 실무 코드에 존재하며 놓치면 상향 의존 누락.
- [위치] manifest `structure.presets.*.import_roots`

### A6. TypeScript bare specifier 는 항상 패키지
- [판단] `'platform'` 같은 bare specifier 는 alias 또는 `import_root/` 접두 경로형이 아니면 계층으로 해석하지 않는다.
- [대안] tsconfig `baseUrl` 을 읽어 해석.
- [근거] tsconfig 파싱은 범위 밖. 오탐(npm 패키지를 계층으로 오인)이 누락보다 나쁘다고 봄.
- [위치] `checks/structure.py Resolver.layer_of_import`, manifest 주석

### A7. "코드 있음" 판정 규칙
- [판단] `source_dirs`(src) 안에 소스 파일이 하나라도 있으면 코드 있음. 밖의 소스는 `exclude_dirs`(tests, docs, tools, config, scripts) 아래가 아닌 것만 세어 `min_source_files`(1) 이상이면 코드 있음. 빈 `src/` 는 코드 없음.
- [대안] 파일 수 임계값을 높게(예: 5); git 커밋 수로 판단; 항상 사람에게 물음.
- [위치] manifest `compliance.code_detection`, `features/state.py`

### A8. adopt 미분류 목록의 제외 범위
- [판단] `src` 이외 최상위 디렉터리 + `code_detection.exclude_dirs` + preset `entry_dirs`(sveltekit `src/routes`) 아래 파일은 계층 배치 대상이 아니므로 목록에서 제외. 루트의 `setup.py` 같은 파일은 남긴다.
- [대안] 전부 나열하고 사람이 지우게.
- [위치] `features/adopt.py _outside_scope`

### A9. 섹션 헤딩 매칭 규칙 (C06)
- [판단] 헤딩에서 선행 번호(`1.`, `1)`, `IV.`), 강조(`**`, `_`, `` ` ``), 후행 부제(` — `, ` - `, ` – `, `:`, `(`) 를 제거한 본문이 섹션명과 **정확히** 같아야 한다. 헤딩 깊이는 `###` 까지.
- [대안] 부분 문자열 포함(초기 구현 — `## ERD 미완성` 이 통과하는 문제), 또는 유사도.
- [위치] `checks/docs.py _norm_heading`, manifest `docs.section_heading_depth`

### A10. Mermaid 검사는 블록 종류 존재만 (C07)
- [판단] ` ```mermaid ` 블록 안 첫 키워드가 `flowchart`/`erDiagram` 인지만 본다. 문법 검증 없음. `%%{init}` 지시어는 건너뜀.
- [대안] mermaid-cli 로 렌더 검증.
- [근거] 외부 의존 없이 결정론적으로.
- [위치] `checks/docs.py mermaid_block_present`

### A11. OpenAPI 검사는 최소 구조만 (C08)
- [판단] YAML 파싱 가능 + `openapi: 3.x` + `info`, `paths` 존재. 
- [대안] openapi-spec-validator 도입.
- [근거] 의존성 최소화. 필요하면 `must_have` 를 늘리거나 별도 check 추가.
- [위치] manifest `docs.types.api.must_have`, `checks/docs.py openapi_valid`

### A12. 포인터 파일 최대 30줄 (C11)
- [판단] CLAUDE.md 등이 30줄을 넘으면 "규칙 본문을 중복 기술" 로 보고 경고.
- [대안] 줄 수 대신 특정 키워드(예: "규칙", "MUST") 검출; 제한 없음.
- [위치] manifest `compliance.pointer_max_lines`

### A13. 검사별 심각도 배정
- [판단] error: C01 C02 C03 C04 C05 C08 · warning: C06 C07 C09 C10 C11. 즉 "문서·디렉터리·계층이 있는가" 와 "의존 방향·OpenAPI 구조" 는 error 로 `check` 를 막고, "문서 내용의 형식" 은 경고.
- [대안] C05 를 warning 으로 시작해 점진 적용; C06 을 error 로.
- [위치] manifest `compliance.checks[].severity`

### A14. 표준 버전 불일치는 warning (C09)
- [판단] 프로젝트가 pin 한 표준 버전이 현재와 달라도 `check` 는 통과.
- [대안] major 가 다르면 error.
- [위치] `checks/meta.py standard_version_pinned`

### A15. 입력 오류 id `C00`
- [판단] 잘못된 project.yaml, 읽을 수 없는 디렉터리, 프로필 유래 오류는 `C00` 하나로 묶고 error.
- [대안] 검사별로 다른 id; C00 을 INFO 로.
- [위치] manifest `compliance.input_error_id`

### A16. 문서 템플릿의 섹션 구성과 문구
- [판단] 11개 템플릿의 섹션명·안내 문구·TODO 표기(`_이탤릭_`)를 ref 예시 기반으로 작성. project-context 에 "현재 작업 현황" 표를 두고, README 에 "문서 안내" 표를 둠.
- [대안] 더 짧게(헤딩만) 또는 더 길게(작성 가이드 포함).
- [위치] `standard/templates/*`

### A17. 문서 언어·ID 자릿수 (D-06 미결정 상태의 기본값)
- [판단] 본문 한국어, 식별자/헤딩 키워드 영문(`REQ-001`, `Status`, `Added`). ID 3자리.
- [위치] manifest `docs.language`, `docs.id_format`

---

## B. 엔진 설계

### B1. 엔진 자신이 4계층을 따른다 (dogfooding)
- [판단] `src/autodocs/{foundation,platform,features,customization}`. 작은 CLI 에는 과할 수 있지만 표준이 CLI 에도 적용됨을 증명.
- [대안] 평면 모듈 구조.
- [위치] 저장소 전체, `.standard/project.yaml` (preset python-package)

### B2. 의존성은 PyYAML 하나, 빌드는 hatchling, `standard/` 는 빌드 시에만 패키지에 복사
- [판단] SSOT 를 저장소 루트 한 곳에 두고 `force-include` 로 복사. 소스 체크아웃에서는 `PYTHONPATH=src` 로 실행.
- [대안] `standard/` 를 패키지 안으로 옮김(경로 단순) 또는 pip 로 표준을 별도 배포.
- [위치] `pyproject.toml`, `platform/standard.py locate`

### B3. 표준 위치 탐색: 명시(--standard/env)는 폴백 없음
- [판단] 명시된 경로에 manifest 가 없으면 오류. 자동 탐색은 소스 체크아웃 → 패키지 동봉본 순.
- [대안] 명시 실패 시 경고 후 기본값 사용.
- [근거] 리뷰 #17 — 사용자가 커스텀 표준을 쓴다고 믿은 채 다른 규칙으로 검사받는 것을 막음.
- [위치] `platform/standard.py`

### B4. Snapshot: `os.walk` 1회, 파일 내용은 캐시로 1회
- [판단] 명령당 디스크 스캔 1회. `read()` 는 dict 캐시. FIFO·소켓·디바이스는 파일로 치지 않음(읽기 블록 방지). 읽을 수 없는 디렉터리는 `errors` 로 기록해 C00 finding.
- [대안] check 마다 필요한 파일만 lazy 스캔; 캐시 없이 단순하게.
- [위치] `foundation/types.py Snapshot`, `platform/fs.py scan`

### B5. 경로 정책: 심링크는 최종 목적지가 root 안이면 허용
- [판단] 절대경로·`..`·null byte 는 입력에서 거부. 심링크는 resolve 결과가 root 안이면 "이미 있음" 으로 유지, 밖이면 PathEscape. 읽기·쓰기·템플릿 모두 동일 정책. 심링크 루프는 PathEscape.
- [대안] 심링크 전면 거부(2차 수정 — `CLAUDE.md -> AGENTS.md` 를 막아 회귀); 읽기는 허용하고 쓰기만 제한.
- [위치] `foundation/paths.py`

### B6. init/adopt 원자성은 "사전 검증" 으로, 롤백은 없음
- [판단] 쓰기 전에 모든 대상 (경로, 종류) 를 preflight 로 검증해 하나라도 문제면 아무것도 쓰지 않는다. 쓰기 도중의 I/O 실패(디스크 풀 등)는 롤백하지 않는다.
- [대안] 임시 디렉터리에 만든 뒤 이동; 실패 시 생성한 것 삭제.
- [위치] `platform/fs.py preflight`, `features/init.py targets`

### B7. init 은 마커를 포함해 아무것도 덮어쓰지 않으며 `--force` 가 없다
- [판단] 이미 있는 파일·디렉터리·`.standard/project.yaml` 은 그대로. 프로필 변경은 파일을 직접 편집.
- [대안] `--force` 또는 `autodocs profile set` 명령.
- [위치] `features/init.py`, `features/profile.py save`

### B8. 빈 디렉터리에 `.gitkeep`
- [판단] init 이 만든 빈 계층 디렉터리에 `.gitkeep` 을 둔다 (git 에 디렉터리가 남도록).
- [대안] 두지 않음 (git 이 빈 디렉터리를 무시하므로 `check` 가 clone 직후 실패).
- [위치] manifest `scan.keep_file`

### B9. adopt 는 코드를 옮기지 않고 계획서(PROP-000)만 만든다
- [판단] 결정론적으로 만들 수 있는 것(마커·문서·디렉터리)만 생성하고, 소스의 계층 배치는 표로 남겨 사람/AI 가 채운다.
- [대안] 휴리스틱(파일명·import 패턴)으로 자동 분류 제안.
- [근거] "엔진은 판단하지 않는다" — 이 원칙 자체가 AI 의 제안이었고 사용자가 CLI 엔진 방식에 동의한 것으로 수용.
- [위치] `features/adopt.py`

### B10. 종료 코드 0/1/2 와 argparse 오류의 매핑
- [판단] 0 통과 · 1 위반 · 2 엔진/사용 오류(모든 예외 포함). argparse 오류도 2. `--help` 는 0.
- [대안] 사용 오류를 64(EX_USAGE)로 분리; 위반 종류별 코드.
- [위치] `cli.py main`

### B11. `--override` 의 의미
- [판단] 위반이 있어도 exit 0. 사유는 stdout/stderr 와 `.standard/overrides.log` 에 남긴다(심링크면 거부). `AUTODOCS_STRICT=1|true|yes` 환경에서는 금지(exit 1). 사유가 빈 문자열이면 무효.
- [대안] override 를 별도 종료 코드(3)로 두어 CI 가 정책을 정하게; 로그를 남기지 않음; 저장소 밖(사용자 홈)에 기록.
- [근거] bkit 의 `--emergency-override` 패턴 + 3차 검증 R6(무흔적 남용).
- [위치] `cli.py _cmd_audit/_log_override`, manifest `compliance.override_log`

### B12. 오류의 경계: 대상 프로젝트 입력은 finding, 엔진 쪽 문제는 exit 2
- [판단] 잘못된 project.yaml/openapi.yaml, 권한 오류, root 밖 심링크 읽기, 심링크 루프, check 안의 ProfileInvalid 는 finding(C00 또는 해당 check). manifest 오류·표준 없음·--root 부재는 exit 2.
- [대안] 전부 exit 2(초기 구현); 전부 finding.
- [위치] `features/audit.py`, `features/checks/__init__.py run_all`

### B13. C05 는 파일당 목적지 계층별 1건만 보고
- [판단] 같은 파일에서 같은 계층으로 가는 import 가 여러 개여도 첫 번째만 보고. 출력이 짧아지지만 "다 고쳤다" 고 착각할 수 있음.
- [대안] 전부 보고; import 개수를 메시지에 표기.
- [위치] `checks/structure.py dependency_direction` (`seen`)

### B14. 대소문자만 다른 파일은 모든 OS 에서 거부
- [판단] `Readme.md` 가 있으면 Linux 에서도 `README.md` 생성을 거부(표준 이름 강제로 간주).
- [대안] 대소문자 무시 FS 에서만 거부; 경고만.
- [위치] `platform/fs.py _case_clash`

### B15. 파싱 실패·미지원 언어는 INFO
- [판단] SyntaxError·null byte·Java/Go/Rust 는 "검사에서 제외됨" INFO. error 도 아니고 무시도 아님.
- [대안] warning 으로 올려 눈에 띄게; 미지원 언어를 아예 `source_ext` 에서 뺌.
- [위치] `checks/structure.py`, manifest `scan.source_ext` 주석

### B16. import 해석 규칙의 세부
- [판단] dotted `a.b.c` 는 `a/b/c → a/b → a` 순으로 접두사를 내려가며 존재 확인(마지막 세그먼트가 심볼일 수 있음). .NET 을 위해 `a.b` 디렉터리명 형태도 시도. ESM `'../x.js'` 는 `x.ts/x.tsx` 로 매핑. 디렉터리 import 는 `index_files` 로 존재 확인.
- [대안] 언어별 전용 리졸버(Python importlib.util.find_spec, TS tsconfig).
- [위치] `checks/structure.py Resolver`, manifest `scan.index_files`

### B17. 비ASCII 프로젝트명은 placeholder 를 쓰는 preset 에서만 오류
- [판단] `법원산타` + generic → 정상. `법원산타` + python-package → `{package}` 를 만들 수 없어 ProfileInvalid(C00).
- [대안] 비ASCII 를 로마자로 변환; 항상 오류.
- [위치] `features/layout.py layer_dirs/_fill`

### B18. 이름 정제 규칙
- [판단] `{package}` = 소문자 snake(`cad-addon → cad_addon`), `{Name}` = 구분자 제거 + 첫 글자 대문자, 내부 대문자 보존(`CadAddon → CadAddon`, `my-API → MyAPI`).
- [위치] `features/layout.py _snake/_pascal`

### B19. init 이 포인터 파일 3개(CLAUDE.md, AGENTS.md, GEMINI.md)를 기본으로 생성
- [판단] manifest `adapters` 에 선언된 모든 앱의 포인터를 만든다. `--no-adapters` 로 끌 수 있음.
- [대안] 실제 쓰는 앱만 선택(`--adapters claude,codex`); 하나도 만들지 않고 어댑터가 만들게.
- [위치] `features/init.py`, manifest `adapters`

### B20. `--preset` 기본값은 언어별 `default_for`
- [판단] 생략하면 Python → python-package, C# → dotnet-solution, 그 외 generic. Python+generic 은 init/audit 에서 경고(C04 warning).
- [대안] 항상 명시 요구.
- [위치] `cli.py _profile`, `features/layout.py default_preset/preset_warning`

### B21. Report 의 ERROR 만 manifest severity 로 치환
- [판단] check 가 INFO/WARNING 으로 낸 finding 은 그대로 두고, ERROR 로 낸 것만 manifest 의 check severity 로 바꾼다.
- [대안] 전부 manifest severity 로 강제(초기 구현 — INFO 가 error 로 승격되는 문제).
- [위치] `features/checks/__init__.py run_all`

### B22. manifest 검증은 손으로 쓴 검사기
- [판단] jsonschema 같은 라이브러리 없이 필요한 구조·enum·참조·값 타입만 검사. 오류는 모아서 한 번에.
- [대안] JSON Schema 파일 + jsonschema 의존.
- [근거] 의존성 최소화. 대신 스키마가 코드에 있어 manifest 와 두 곳을 맞춰야 함.
- [위치] `platform/manifest_schema.py`

### B23. 템플릿 잔존 변수 경고는 소문자 snake_case 만
- [판단] 렌더 후 `$project_name` 같은 소문자 변수만 경고, `$HOME`/`$PATH` 는 무시.
- [위치] `features/init.py _LEFTOVER`

### B24. 출력 형식
- [판단] 텍스트 출력 아이콘은 ASCII(`x ! -`), JSON 은 `{state, ok, next, override, findings[]}`. 비UTF-8 콘솔에서는 `errors="replace"`.
- [위치] `features/report.py`, `cli.py main`

### B25. 테스트 범위
- [판단] 단위 테스트만(110건). 실제 Claude Code 세션 통합 테스트 없음. root 로 실행하면 권한 테스트 2건 skip.
- [대안] bkit 의 L6 "live-run 증거" 방식 — 어댑터 완성 후 검토.
- [위치] `tests/unit/`

---

## C. 프로세스 판단

### C1. 리뷰를 독립 에이전트에게 맡기고 재현 실험을 요구
- [판단] 코드를 쓴 AI 가 아닌 별도 리뷰어가 `/tmp` 에서 재현하게 하고, 4회 반복.
### C2. 리뷰에서 나온 항목을 단계별로 나눠 커밋
- [판단] 보안 → 버그 → 정책 이동 → C05 → 스키마 순. 커밋 3개(6177126, 7b5843c, ebfcc7a).
### C3. 설계상 수용한 한계를 문서에 남김
- [판단] 동적 import 미검출, 계층별 1건 보고, Linux 대소문자 거부 — PROP-001 "남은 것".

---

## 검토 방법 제안

항목 번호를 들어 "그대로 / 뒤집기 / D-xx 로 승격" 중 하나를 알려주시면 반영한다. 뒤집는 항목은 코드·manifest·테스트를 함께 바꾸고 PROP-001 과 같은 방식으로 재검증한다.
