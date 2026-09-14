"""L2 — Report 렌더링 (text / json). 출력 형식만 담당하며 판단 로직은 없다."""
from __future__ import annotations

import json
from dataclasses import asdict

from autodocs.foundation import Report, Severity

_ICON = {Severity.ERROR: "✗", Severity.WARNING: "!", Severity.INFO: "·"}
_NEXT = {
    "new": "→ `autodocs init` 으로 표준 구조와 필수 문서를 생성하세요.",
    "legacy": "→ `autodocs adopt` 로 마커·문서를 만들고 docs/proposals/PROP-000 계획을 채우세요.",
    "partial": "→ 아래 error 항목을 해결하면 compliant 가 됩니다.",
    "compliant": "→ 표준을 충족합니다. 작업 후 `autodocs check` 를 실행하세요.",
}


def text(report: Report) -> str:
    lines = [f"state: {report.state.value}", _NEXT[report.state.value], ""]
    for f in report.findings:
        loc = f"  ({f.path})" if f.path else ""
        lines.append(f"{_ICON[f.severity]} [{f.check_id}] {f.message}{loc}")
        if f.fix_hint:
            lines.append(f"      ↳ {f.fix_hint}")
    n_err = len(report.errors)
    n_warn = sum(1 for f in report.findings if f.severity == Severity.WARNING)
    lines += ["", f"{n_err} error(s), {n_warn} warning(s)"]
    return "\n".join(lines)


def json_str(report: Report) -> str:
    return json.dumps({"state": report.state.value,
                       "ok": report.ok,
                       "findings": [asdict(f) for f in report.findings]},
                      ensure_ascii=False, indent=2, default=str)
