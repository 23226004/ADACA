"""L2 — manifest + profile 로부터 "이 프로젝트에 실제로 요구되는 것"을 계산한다.

manifest 는 일반 규칙, profile 은 프로젝트 선언. 둘을 합쳐 구체 경로 목록을 만든다.
모든 함수는 순수 함수이며 디스크를 읽지 않는다. 반환하는 경로는 전부 norm_rel 을 거친 정규형이다.
"""
from __future__ import annotations

import re

from autodocs.foundation import ManifestInvalid, Profile, ProfileInvalid, norm_rel

_WHEN = re.compile(r"^project_profile\.(\w+)\s*==\s*(true|false)$")


def _when_ok(expr: str | None, profile: Profile | None) -> bool:
    """`when: project_profile.has_api == true` 형태만 지원. profile 없으면 조건부는 요구하지 않음."""
    if not expr:
        return True
    if profile is None:
        return False
    m = _WHEN.match(expr.strip())
    if not m:
        raise ManifestInvalid(f"지원하지 않는 when 식: {expr!r} (project_profile.<field> == true|false 만 가능)")
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


def doc_path(spec: dict) -> str | None:
    """단일 파일 문서의 정규화 경로. `{id}` 같은 placeholder 가 있으면(proposal/adr) None."""
    p = spec["path"]
    return None if "{" in p else norm_rel(p)


def top_level_dirs(manifest: dict) -> list[str]:
    return [norm_rel(p) for p in manifest["structure"]["top_level"] if p.endswith("/")]


def required_dirs(manifest: dict) -> list[str]:
    return [norm_rel(p) for p, spec in manifest["structure"]["top_level"].items()
            if p.endswith("/") and spec.get("requirement") == "required"]


def required_top_files(manifest: dict) -> list[str]:
    return [norm_rel(p) for p, spec in manifest["structure"]["top_level"].items()
            if not p.endswith("/") and spec.get("requirement") == "required"]


def preset_names(manifest: dict) -> list[str]:
    return list(manifest["structure"].get("presets", {"generic": None}))


def layer_dirs(manifest: dict, profile: Profile | None) -> dict[str, str]:
    """{L0: 'src/foundation', ...} — preset 과 placeholder 를 해석한 실제 경로.

    placeholder 는 정제된 값만 치환한다 ({package}=snake, {Name}=Pascal). 원문 name 은 경로에 넣지 않는다.
    """
    preset = (profile.layout_preset if profile else "generic") or "generic"
    presets = manifest["structure"].get("presets", {})
    if preset not in presets:
        raise ProfileInvalid(f"알 수 없는 layout_preset: {preset!r} (가능: {', '.join(presets)})")
    raw = presets[preset]["layer_dirs"]
    name = profile.name if profile else "project"
    subs = {"Name": lambda: _pascal(name), "package": lambda: _snake(name)}   # placeholder 가 실제 있을 때만 정제
    return {lid: norm_rel(_fill(path, subs)) for lid, path in raw.items()}


def layer_order(manifest: dict) -> list[str]:
    return [l["id"] for l in manifest["structure"]["layers"]]


def _fill(s: str, subs: dict) -> str:
    for k, v in subs.items():
        if "{" + k + "}" in s:
            s = s.replace("{" + k + "}", v())
    if "{" in s:
        raise ManifestInvalid(f"preset 경로에 알 수 없는 placeholder: {s}")
    return s


def _snake(s: str) -> str:
    out = re.sub(r"[^a-z0-9_]+", "_", s.lower()).strip("_")
    if not out:
        raise ProfileInvalid(f"프로젝트 이름 {s!r} 에서 패키지명을 만들 수 없습니다 (영문·숫자 필요)")
    return out


def _pascal(s: str) -> str:
    out = "".join(w.capitalize() for w in re.split(r"[^A-Za-z0-9]+", s) if w)
    if not out:
        raise ProfileInvalid(f"프로젝트 이름 {s!r} 에서 식별자를 만들 수 없습니다 (영문·숫자 필요)")
    return out
