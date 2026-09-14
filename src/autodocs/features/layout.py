"""L2 — manifest + profile 로부터 "이 프로젝트에 실제로 요구되는 것"을 계산한다.

manifest 는 일반 규칙, profile 은 프로젝트 선언. 둘을 합쳐 구체 경로 목록을 만든다.
모든 함수는 순수 함수이며 디스크를 읽지 않는다.
"""
from __future__ import annotations

import re

from autodocs.foundation import Profile

_WHEN = re.compile(r"^project_profile\.(\w+)\s*==\s*(true|false)$")


def _when_ok(expr: str | None, profile: Profile | None) -> bool:
    """`when: project_profile.has_api == true` 형태만 지원. profile 없으면 조건부는 요구하지 않음."""
    if not expr:
        return True
    if profile is None:
        return False
    m = _WHEN.match(expr.strip())
    if not m:
        raise ValueError(f"지원하지 않는 when 식: {expr}")
    field, want = m.groups()
    actual = getattr(profile, field, profile.extra.get(field))
    return bool(actual) == (want == "true")


def required_docs(manifest: dict, profile: Profile | None) -> dict[str, dict]:
    """required + (조건 충족한) conditional 문서. {doc_key: spec}"""
    out = {}
    for key, spec in manifest["docs"]["types"].items():
        req = spec.get("requirement", "optional")
        if req == "required" or (req == "conditional" and _when_ok(spec.get("when"), profile)):
            out[key] = spec
    return out


def optional_docs(manifest: dict) -> dict[str, dict]:
    return {k: s for k, s in manifest["docs"]["types"].items() if s.get("requirement") == "optional"}


def required_dirs(manifest: dict) -> list[str]:
    return [p.rstrip("/") for p, spec in manifest["structure"]["top_level"].items()
            if p.endswith("/") and spec.get("requirement") == "required"]


def required_top_files(manifest: dict) -> list[str]:
    return [p for p, spec in manifest["structure"]["top_level"].items()
            if not p.endswith("/") and spec.get("requirement") == "required"]


def layer_dirs(manifest: dict, profile: Profile | None) -> dict[str, str]:
    """{L0: 'src/foundation', ...} — preset 과 placeholder 를 해석한 실제 경로."""
    preset = (profile.layout_preset if profile else "generic") or "generic"
    presets = manifest["structure"].get("presets", {})
    raw = presets.get(preset, presets["generic"])["layer_dirs"]
    name = profile.name if profile else "project"
    subs = {"Name": _pascal(name), "package": _snake(name), "name": name}
    return {lid: _fill(path, subs) for lid, path in raw.items()}


def layer_order(manifest: dict) -> list[str]:
    return [l["id"] for l in manifest["structure"]["layers"]]


def _fill(s: str, subs: dict[str, str]) -> str:
    for k, v in subs.items():
        s = s.replace("{" + k + "}", v)
    return s


def _snake(s: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", s.lower()).strip("_") or "project"


def _pascal(s: str) -> str:
    return "".join(w.capitalize() for w in re.split(r"[^A-Za-z0-9]+", s) if w) or "Project"
