"""L2 — 문서 관련 검사 (C01, C02, C06, C07, C08, C10)."""
from __future__ import annotations

import re

from autodocs.features import layout
from autodocs.foundation import Context, Finding, Severity

_H = "docs"  # 임시 check_id — run_all 이 manifest id 로 교체
_MERMAID = re.compile(r"```mermaid\s*\n\s*(\w+)", re.M)


def _f(msg: str, path: str | None = None, hint: str | None = None) -> Finding:
    return Finding(_H, Severity.ERROR, msg, path, hint)


def _concrete_path(spec: dict) -> str | None:
    """`{id}` 같은 placeholder 가 있는 문서(proposal/adr)는 단일 파일이 아니므로 None."""
    p = spec["path"]
    return None if "{" in p else p


def _present_docs(ctx: Context, requirement: str) -> list[Finding]:
    out = []
    for key, spec in layout.required_docs(ctx.manifest, ctx.profile).items():
        if spec.get("requirement") != requirement:
            continue
        p = _concrete_path(spec)
        if p and not ctx.snapshot.has_file(p):
            out.append(_f(f"{spec['title']}({key}) 없음", p, f"autodocs init 또는 템플릿 {spec.get('template')} 로 생성"))
    return out


def required_docs_present(ctx: Context) -> list[Finding]:
    return _present_docs(ctx, "required")


def conditional_docs_present(ctx: Context) -> list[Finding]:
    return _present_docs(ctx, "conditional")


def doc_required_sections(ctx: Context) -> list[Finding]:
    out = []
    for key, spec in ctx.manifest["docs"]["types"].items():
        p = _concrete_path(spec)
        if not p or not spec.get("sections") or not ctx.snapshot.has_file(p) or spec.get("format") == "openapi":
            continue
        text = ctx.snapshot.read(p)
        headings = {h.strip() for h in re.findall(r"^#{1,3}\s+(.+?)\s*$", text, re.M)}
        for sec in spec["sections"]:
            if not any(sec in h for h in headings):
                out.append(_f(f"{key}: 섹션 '{sec}' 없음", p, f"'## {sec}' 헤딩 추가"))
    return out


def mermaid_block_present(ctx: Context) -> list[Finding]:
    out = []
    for key, spec in ctx.manifest["docs"]["types"].items():
        p = _concrete_path(spec)
        if not p or not ctx.snapshot.has_file(p):
            continue
        for want in spec.get("must_contain", []):
            kind, _, diagram = want.partition(":")
            if kind != "mermaid":
                continue
            found = set(_MERMAID.findall(ctx.snapshot.read(p)))
            if diagram not in found:
                out.append(_f(f"{key}: mermaid {diagram} 블록 없음", p, f"```mermaid\\n{diagram} ...``` 추가"))
    return out


def openapi_valid(ctx: Context) -> list[Finding]:
    """외부 validator 없이 최소 구조만 본다: openapi 3.x, info, paths."""
    from autodocs.platform import yaml_io  # L1 사용은 허용 (L2 → L1)

    out = []
    for key, spec in ctx.manifest["docs"]["types"].items():
        p = _concrete_path(spec)
        if spec.get("format") != "openapi" or not p or not ctx.snapshot.has_file(p):
            continue
        try:
            doc = yaml_io.load(ctx.snapshot.root / p)
        except Exception as e:  # noqa: BLE001 — YAML 오류는 그대로 보고
            out.append(_f(f"{key}: YAML 파싱 실패 — {e}", p))
            continue
        want = str(spec.get("openapi_version", "3"))
        if not str(doc.get("openapi", "")).startswith(want.split(".")[0]):
            out.append(_f(f"{key}: 'openapi: {want}' 선언 없음", p))
        for k in ("info", "paths"):
            if k not in doc:
                out.append(_f(f"{key}: 최상위 '{k}' 없음", p))
    return out


def changelog_has_unreleased_or_latest(ctx: Context) -> list[Finding]:
    spec = ctx.manifest["docs"]["types"].get("changelog")
    if not spec or not ctx.snapshot.has_file(spec["path"]):
        return []
    text = ctx.snapshot.read(spec["path"])
    if not re.search(r"^## \[", text, re.M):
        return [_f("changelog: '## [버전] - 날짜' 또는 '## [Unreleased]' 항목 없음", spec["path"])]
    return []
