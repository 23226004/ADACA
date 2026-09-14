"""L2 — 검사 레지스트리. manifest.compliance.checks[].name ↔ 함수 이름으로 연결된다.

각 check 는 `(ctx: Context) -> list[Finding]` 인 순수 함수이며 Snapshot 만 본다.
manifest 에 있으나 구현이 없는 check 는 실행 시 INFO 로 보고된다 (조용히 통과시키지 않음).
"""
from __future__ import annotations

from collections.abc import Callable

from autodocs.foundation import AutodocsError, Context, Finding, ProfileInvalid, Severity

from . import docs, meta, structure

Check = Callable[[Context], list[Finding]]

REGISTRY: dict[str, Check] = {
    "required_docs_present": docs.required_docs_present,
    "conditional_docs_present": docs.conditional_docs_present,
    "doc_required_sections": docs.doc_required_sections,
    "mermaid_block_present": docs.mermaid_block_present,
    "openapi_valid": docs.openapi_valid,
    "changelog_has_unreleased_or_latest": docs.changelog_has_unreleased_or_latest,
    "required_dirs_present": structure.required_dirs_present,
    "layer_dirs_present": structure.layer_dirs_present,
    "dependency_direction": structure.dependency_direction,
    "standard_version_pinned": meta.standard_version_pinned,
    "adapter_files_are_pointers": meta.adapter_files_are_pointers,
}


def run_all(ctx: Context) -> list[Finding]:
    """manifest 에 선언된 순서대로 실행. severity 는 manifest 값으로 덮어쓴다 (SSOT)."""
    out: list[Finding] = []
    for spec in ctx.manifest["compliance"]["checks"]:
        fn = REGISTRY.get(spec["name"])
        if fn is None:
            out.append(Finding(spec["id"], Severity.INFO, f"check '{spec['name']}' 미구현"))
            continue
        sev = Severity(spec.get("severity", "error"))
        try:
            results = fn(ctx)
        except ProfileInvalid as e:   # 프로필 유래 오류는 프로젝트의 문제 → C00 (같은 메시지는 한 번만)
            f = Finding("C00", Severity.ERROR, str(e), ctx.manifest["compliance"]["marker"]["path"])
            if f not in out:
                out.append(f)
            continue
        except AutodocsError as e:    # 읽기 실패·root 밖 심링크 등 대상 프로젝트의 문제 → 해당 check 의 finding
            out.append(Finding(spec["id"], Severity.ERROR, str(e)))
            continue
        out.extend(Finding(spec["id"], sev, f.message, f.path, f.fix_hint) for f in results)
    return out
