"""L2 — adopt: 기존(legacy) 프로젝트를 표준으로 옮기기 위한 **계획**을 만든다.

코드를 옮기는 판단(이 파일이 L1 인가 L2 인가)은 AI/사람이 한다. 엔진은
  1) 마커·문서·디렉터리처럼 결정론적으로 만들 수 있는 것은 init 과 같은 방식으로 생성하고
  2) 계층 밖 소스 파일 목록을 계획서(PROP-000)로 내놓는다.
계획서는 docs/proposals/ 에 두어 Proposal 문서로 취급한다 (합의 후 실행).
"""
from __future__ import annotations

from pathlib import Path

from autodocs.features import init, layout
from autodocs.features.checks.structure import _Resolver
from autodocs.foundation import Profile
from autodocs.platform import fs

PLAN_REL = "docs/proposals/PROP-000-adopt-standard.md"


def run(manifest: dict, root: Path, profile: Profile, *, with_adapters: bool = True) -> tuple[init.InitResult, str]:
    snap_before = fs.scan(root)
    res = init.run(manifest, root, profile, with_adapters=with_adapters)
    resolver = _Resolver(layout.layer_dirs(manifest, profile))
    unclassified = sorted(f for f in snap_before.source_files
                          if resolver.layer_of_path(f) is None and not _outside_scope(manifest, f))
    if fs.write_text(root, PLAN_REL, _plan(manifest, profile, unclassified)):
        res.created.append(PLAN_REL)
    else:
        res.skipped.append(PLAN_REL)
    return res, PLAN_REL


def _outside_scope(manifest: dict, rel: str) -> bool:
    """tests/, docs/, tools/ 등 src 가 아닌 최상위 디렉터리의 파일은 계층 배치 대상이 아니다."""
    for d in layout.top_level_dirs(manifest):
        if d != "src" and rel.startswith(d + "/"):
            return True
    return False


def _plan(manifest: dict, profile: Profile, unclassified: list[str]) -> str:
    layers = manifest["structure"]["layers"]
    dirs = layout.layer_dirs(manifest, profile)
    guide = "\n".join(f"| {l['id']} | `{dirs[l['id']]}/` | {', '.join(l['role'])} |" for l in layers)
    files = "\n".join(f"| `{f}` |  |  |" for f in unclassified) or "| (없음) |  |  |"
    return f"""# PROP-000 표준 구조 도입 (adopt)

## 제안 배경

기존 프로젝트 `{profile.name}` 을 AI Harness Engineering Standard v{manifest['standard']['version']} 구조로 옮긴다.
`autodocs adopt` 가 마커·필수 문서·계층 디렉터리는 생성했고, **소스 파일의 계층 배치는 아래 표를 채워 합의한 뒤 실행**한다.

## 제안 내용

### 계층 기준

| 계층 | 디렉터리 | 역할 |
|---|---|---|
{guide}

### 미분류 소스 파일 ({len(unclassified)}개)

각 파일의 목적지 계층과 이유를 채운다. 판단 원칙: 가능하면 L2(features), 프로젝트 고유 설정은 L3, 외부 시스템 접근은 L1, 공통 기반만 L0.
tests/, docs/, tools/ 아래 파일은 계층 배치 대상이 아니므로 목록에 없다.

| 파일 | 목적지 계층 | 이유 |
|---|---|---|
{files}

## 기대 효과

- 모든 프로젝트가 동일한 구조를 가져 AI/개발자의 탐색·수정 범위가 명확해진다.
- `autodocs check` 로 의존성 방향 위반을 자동 검출할 수 있게 된다.

## 예상 영향 범위

- import 경로 전면 변경 → 테스트 전체 실행 필요
- 빌드/패키징 설정(경로 참조) 변경

## 참고 자료

- standard/manifest.yaml (structure.layers, dependency_rules)
"""
