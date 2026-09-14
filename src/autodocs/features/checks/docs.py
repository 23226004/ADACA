"""L2 — 문서 관련 검사 (C01, C02, C06, C07, C08, C10)."""
from __future__ import annotations

import re

from autodocs.features import layout
from autodocs.foundation import AutodocsError, Context, Finding, Severity
from autodocs.platform import yaml_io

_H = "docs"  # 임시 check_id — run_all 이 manifest id 로 교체
_MERMAID = re.compile(r"```mermaid[^\n]*\n(?:\s*%%[^\n]*\n)*\s*(\w+)", re.M)


def _f(msg: str, path: str | None = None, hint: str | None = None) -> Finding:
    return Finding(_H, Severity.ERROR, msg, path, hint)


_concrete_path = layout.doc_path


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
        depth = ctx.manifest["docs"]["section_heading_depth"]
        headings = {_norm_heading(h) for h in re.findall(rf"^#{{1,{depth}}}\s+(.+?)\s*$", text, re.M)}
        for sec in spec["sections"]:
            if _norm_heading(sec) not in headings:
                out.append(_f(f"{key}: 섹션 '{sec}' 없음", p, f"'## {sec}' 헤딩 추가"))
    return out


_HEAD_NUM = re.compile(r"^(?:\d+[.)]|[IVX]+\.)\s*")
_HEAD_TAIL = re.compile(r"\s*(?:[—–\-:(].*)?$")   # ' — 부제', ' - 부제', ':', '(…)' 제거


def _norm_heading(h: str) -> str:
    """'## 2. **프로젝트 목적**: 개요' → '프로젝트 목적'. 번호·강조·후행 부제/콜론은 무시하고 본문만 비교."""
    h = _HEAD_NUM.sub("", h.strip()).strip("*_` ").strip()
    return _HEAD_TAIL.sub("", h).strip("*_` ").strip()


def _applies(ctx: Context) -> list[tuple[str, dict]]:
    """check 항목의 applies_to 가 있으면 그 문서 키만."""
    only = (ctx.check or {}).get("applies_to")
    return [(k, s) for k, s in ctx.manifest["docs"]["types"].items() if not only or k in only]


def mermaid_block_present(ctx: Context) -> list[Finding]:
    out = []
    for key, spec in _applies(ctx):
        p = _concrete_path(spec)
        if not p or not ctx.snapshot.has_file(p):
            continue
        found = None
        for want in spec.get("must_contain", []):
            kind, _, diagram = want.partition(":")
            if kind != "mermaid":
                continue
            if found is None:
                found = set(_MERMAID.findall(ctx.snapshot.read(p)))
            if diagram not in found:
                out.append(_f(f"{key}: mermaid {diagram} 블록 없음", p, f"```mermaid\\n{diagram} ...``` 추가"))
    return out


def openapi_valid(ctx: Context) -> list[Finding]:
    """외부 validator 없이 최소 구조만 본다: openapi 3.x, info, paths. Snapshot 캐시를 통해 읽는다."""
    out = []
    for key, spec in _applies(ctx):
        p = _concrete_path(spec)
        if spec.get("format") != "openapi" or not p or not ctx.snapshot.has_file(p):
            continue
        try:
            doc = yaml_io.loads(ctx.snapshot.read(p))
        except AutodocsError as e:
            out.append(_f(f"{key}: {e}", p))
            continue
        if not isinstance(doc, dict):
            out.append(_f(f"{key}: 최상위가 매핑이 아님", p))
            continue
        want = str(spec["openapi_version"])
        if not str(doc.get("openapi", "")).startswith(want.split(".")[0]):
            out.append(_f(f"{key}: 'openapi: {want}' 선언 없음", p))
        for k in spec["must_have"]:
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
