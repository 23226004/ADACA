"""L2 — 준수 상태 판정 (manifest.compliance.states / code_detection)."""
from __future__ import annotations

from autodocs.foundation import Finding, Severity, Snapshot, State, norm_rel
from autodocs.features.profile import marker_rel

_DEFAULT_DETECTION = {"source_dirs": ["src"], "exclude_dirs": ["tests", "test", "docs", "tools", "config"], "min_source_files": 1}


def has_code(manifest: dict, snapshot: Snapshot) -> bool:
    """"코드 있음" 판정. manifest.compliance.code_detection 이 규칙을 정한다.

    - source_dirs 중 하나에 소스 파일이 하나라도 있으면 True (빈 src/ 는 코드 없음)
    - 그 외 위치의 소스 파일은 exclude_dirs 아래가 아니면 셈에 넣는다
    """
    rule = {**_DEFAULT_DETECTION, **manifest["compliance"].get("code_detection", {})}
    src_dirs = [norm_rel(d) for d in rule["source_dirs"]]
    excl = [norm_rel(d) for d in rule["exclude_dirs"]]
    n = 0
    for f in snapshot.source_files:
        if any(f.startswith(d + "/") for d in src_dirs):
            return True
        if not any(f.startswith(d + "/") for d in excl):
            n += 1
    return n >= rule["min_source_files"]


def judge(manifest: dict, snapshot: Snapshot, findings: list[Finding]) -> State:
    if not snapshot.has_file(marker_rel(manifest)):
        return State.LEGACY if has_code(manifest, snapshot) else State.NEW
    if any(f.severity == Severity.ERROR for f in findings):
        return State.PARTIAL
    return State.COMPLIANT
