"""L2 — 준수 상태 판정 (manifest.compliance.states)."""
from __future__ import annotations

from autodocs.foundation import Finding, Severity, Snapshot, State
from autodocs.features.profile import marker_rel

MIN_SOURCE_FILES = 1   # "코드 있음" 판정 기준 (D-05 후속 결정 시 manifest 로 이동)


def has_code(snapshot: Snapshot) -> bool:
    return snapshot.has_dir("src") or len(snapshot.source_files) >= MIN_SOURCE_FILES


def judge(manifest: dict, snapshot: Snapshot, findings: list[Finding]) -> State:
    if not snapshot.has_file(marker_rel(manifest)):
        return State.LEGACY if has_code(snapshot) else State.NEW
    if any(f.severity == Severity.ERROR for f in findings):
        return State.PARTIAL
    return State.COMPLIANT
