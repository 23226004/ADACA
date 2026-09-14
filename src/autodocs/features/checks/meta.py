"""L2 — 메타 검사 (C09 표준 버전 pin, C11 어댑터 파일은 포인터인가)."""
from __future__ import annotations

from autodocs.foundation import Context, Finding, Severity

_H = "meta"


def _f(msg: str, path: str | None = None, hint: str | None = None) -> Finding:
    return Finding(_H, Severity.WARNING, msg, path, hint)


def standard_version_pinned(ctx: Context) -> list[Finding]:
    if ctx.profile is None:
        return []
    cur = ctx.manifest["standard"]["version"]
    if ctx.profile.standard_version != cur:
        return [_f(f"표준 버전 불일치: 프로젝트 {ctx.profile.standard_version} vs 현재 {cur}",
                   ctx.manifest["compliance"]["marker"]["path"], "변경점을 검토한 뒤 standard_version 을 갱신")]
    return []


def adapter_files_are_pointers(ctx: Context) -> list[Finding]:
    ctx_path = ctx.manifest["docs"]["types"]["project_context"]["path"]
    max_lines = ctx.manifest["compliance"]["pointer_max_lines"]
    out = []
    for name, ad in ctx.manifest.get("adapters", {}).items():
        p = ad.get("pointer_file")
        if not p or not ctx.snapshot.has_file(p):
            continue
        text = ctx.snapshot.read(p)
        if ctx_path not in text:
            out.append(_f(f"{p} 가 {ctx_path} 를 가리키지 않음", p, f"'{ctx_path} 를 먼저 읽어라' 한 줄 추가"))
        if text.count("\n") > max_lines:
            out.append(_f(f"{p} 가 {max_lines}줄을 넘음 — 규칙 본문은 project-context 에만", p))
    return out
