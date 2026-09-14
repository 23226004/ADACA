"""L2 — audit: 스캔 한 번 → 프로필 → 모든 check → 상태 판정."""
from __future__ import annotations

from pathlib import Path

from autodocs.features import checks, profile as profile_mod, state
from autodocs.foundation import AutodocsError, Context, Finding, Report, Severity
from autodocs.platform import fs


def run(manifest: dict, root: Path) -> Report:
    snap = fs.scan(root, manifest["scan"])
    c00 = manifest["compliance"]["input_error_id"]
    findings: list[Finding] = []
    try:
        prof = profile_mod.load(manifest, snap)
    except AutodocsError as e:   # 잘못된 project.yaml 은 크래시가 아니라 finding
        prof = None
        findings.append(Finding(c00, Severity.ERROR, str(e), profile_mod.marker_rel(manifest)))
    findings += [Finding(c00, Severity.ERROR, f"디렉터리를 읽을 수 없음: {d}", d) for d in snap.errors]
    ctx = Context(manifest=manifest, snapshot=snap, profile=prof)
    findings += checks.run_all(ctx)
    st = state.judge(manifest, snap, findings)
    return Report(state=st, findings=tuple(findings), next_action=manifest["compliance"]["states"][st.value]["next"])
