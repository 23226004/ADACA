"""L2 — Report 렌더링 (text / json). 출력 형식만 담당하며 판단 로직은 없다."""
from __future__ import annotations

import json
from dataclasses import asdict

from autodocs.foundation import Report, Severity

_ICON = {Severity.ERROR: "x", Severity.WARNING: "!", Severity.INFO: "-"}


def text(report: Report, *, override: str | None = None) -> str:
    lines = [f"state: {report.state.value}", f"-> {report.next_action}", ""]
    for f in report.findings:
        loc = f"  ({f.path})" if f.path else ""
        lines.append(f"{_ICON[f.severity]} [{f.check_id}] {f.message}{loc}")
        if f.fix_hint:
            lines.append(f"      -> {f.fix_hint}")
    n_err = len(report.errors)
    n_warn = sum(1 for f in report.findings if f.severity == Severity.WARNING)
    lines += ["", f"{n_err} error(s), {n_warn} warning(s)"]
    if override and n_err:
        lines.append(f"OVERRIDE: {override}")
    return "\n".join(lines)


def json_str(report: Report, *, override: str | None = None) -> str:
    return json.dumps({"state": report.state.value,
                       "ok": report.ok,
                       "next": report.next_action,
                       "override": override if (override and not report.ok) else None,
                       "findings": [asdict(f) for f in report.findings]},
                      ensure_ascii=False, indent=2, default=str)
