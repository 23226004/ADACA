"""L1 — manifest 구조 검증. 로드 직후 한 번 실행되어 이후 코드가 KeyError/ValueError 로 죽지 않게 한다.

외부 스키마 라이브러리 없이 필요한 만큼만 검사한다. 오류는 모두 ManifestInvalid 로 모아 한 번에 보고.
"""
from __future__ import annotations

from autodocs.foundation import ManifestInvalid

_SEVERITY = {"error", "warning", "info"}
_REQUIREMENT = {"required", "conditional", "optional"}
_FORMAT = {"markdown", "markdown+mermaid", "openapi"}
_STATES = ("new", "legacy", "partial", "compliant")
_PROFILE_TYPES = {"string", "enum", "bool"}


def validate(m: dict) -> None:
    errs: list[str] = []
    need = lambda d, key, path: (errs.append(f"{path}.{key} 누락") or False) if key not in d else True  # noqa: E731

    for k in ("standard", "project_profile", "scan", "docs", "structure", "workflow", "compliance", "adapters"):
        need(m, k, "manifest")
    if errs:
        raise ManifestInvalid("manifest 최상위 키 누락: " + ", ".join(errs))

    def typed(d, key, t, path):
        if key in d and not isinstance(d[key], t):
            errs.append(f"{path}.{key} 는 {getattr(t, '__name__', t)} 이어야 함 (실제 {type(d[key]).__name__})")

    # standard
    need(m["standard"], "version", "standard")
    typed(m["standard"], "version", str, "standard")   # YAML 1.0 → float 이 되면 profile 검증이 실패한다

    # project_profile.schema
    schema = m["project_profile"].get("schema") or {}
    for k, s in schema.items():
        if not isinstance(s, dict) or s.get("type") not in _PROFILE_TYPES:
            errs.append(f"project_profile.schema.{k}.type 은 {sorted(_PROFILE_TYPES)} 중 하나")
        elif s["type"] == "enum" and not isinstance(s.get("values"), list):
            errs.append(f"project_profile.schema.{k}.values 는 목록")
        if isinstance(s, dict) and "default" in s and s.get("type") in _PROFILE_TYPES:
            want = {"string": str, "enum": str, "bool": bool}[s["type"]]
            if not isinstance(s["default"], want) or (want is str and isinstance(s["default"], bool)):
                errs.append(f"project_profile.schema.{k}.default 는 {s['type']} 이어야 함")
    for k in ("name", "kind", "language", "layout_preset", "standard_version"):
        if k not in schema:
            errs.append(f"project_profile.schema.{k} 누락")

    # scan
    sc = m["scan"]
    if not isinstance(sc.get("skip_dirs"), list):
        errs.append("scan.skip_dirs 는 목록")
    if not isinstance(sc.get("source_ext"), dict) or not all(str(e).startswith(".") for e in sc.get("source_ext", {})):
        errs.append("scan.source_ext 는 {'.ext': language} 매핑")
    need(sc, "keep_file", "scan")
    typed(sc, "keep_file", str, "scan")
    typed(sc, "index_files", list, "scan")

    # docs.types
    types = m["docs"].get("types") or {}
    if "project_context" not in types:
        errs.append("docs.types.project_context 필수 (포인터 파일의 목적지)")
    typed(m["docs"], "section_heading_depth", int, "docs")
    typed(m["docs"], "pointer_template", str, "docs")
    for key, spec in types.items():
        p = f"docs.types.{key}"
        if not isinstance(spec, dict):
            errs.append(f"{p} 는 매핑"); continue
        for f in ("title", "path", "format", "template", "requirement"):
            need(spec, f, p)
            typed(spec, f, str, p)
        typed(spec, "sections", list, p)
        typed(spec, "must_contain", list, p)
        typed(spec, "must_have", list, p)
        if spec.get("format") == "openapi":
            for f in ("openapi_version", "must_have"):
                need(spec, f, p)
        if spec.get("requirement") not in _REQUIREMENT:
            errs.append(f"{p}.requirement 는 {sorted(_REQUIREMENT)} 중 하나")
        if spec.get("requirement") == "conditional" and not spec.get("when"):
            errs.append(f"{p}.when 누락 (conditional 은 조건 필요)")
        if spec.get("format") not in _FORMAT:
            errs.append(f"{p}.format 은 {sorted(_FORMAT)} 중 하나")

    # structure
    st = m["structure"]
    layers = st.get("layers") or []
    ids = [l.get("id") for l in layers]
    if not ids or len(set(ids)) != len(ids):
        errs.append("structure.layers 는 고유한 id 를 가진 목록")
    for l in layers:
        for f in ("id", "name", "dir", "role"):
            need(l, f, f"structure.layers[{l.get('id')}]")
    presets = st.get("presets") or {}
    if "generic" not in presets:
        errs.append("structure.presets.generic 필수")
    for name, p in presets.items():
        if set((p.get("layer_dirs") or {}).keys()) != set(ids):
            errs.append(f"structure.presets.{name}.layer_dirs 키가 layers id {ids} 와 다름")
        elif any(not isinstance(v, str) for v in p["layer_dirs"].values()):
            errs.append(f"structure.presets.{name}.layer_dirs 값은 문자열")
        if not isinstance(p.get("import_roots"), list):
            errs.append(f"structure.presets.{name}.import_roots 는 목록")
        for f in ("aliases",):
            typed(p, f, dict, f"structure.presets.{name}")
        for f in ("entry_dirs", "languages", "default_for", "discouraged_for"):
            typed(p, f, list, f"structure.presets.{name}")
    rules = (st.get("dependency_rules") or {}).get("allowed")
    if not isinstance(rules, list):
        errs.append("structure.dependency_rules.allowed 는 목록")
    else:
        for r in rules:
            if r.get("from") not in ids or any(t not in ids for t in r.get("to", [])):
                errs.append(f"structure.dependency_rules.allowed 에 알 수 없는 계층 id: {r}")
    if not isinstance(st.get("top_level"), dict):
        errs.append("structure.top_level 는 매핑")
    else:
        for k, v in st["top_level"].items():
            if not isinstance(v, dict) or v.get("requirement") not in _REQUIREMENT:
                errs.append(f"structure.top_level[{k}] 는 {{requirement: ...}} 매핑")

    # compliance
    c = m["compliance"]
    for f in ("marker", "code_detection", "adopt_plan", "input_error_id", "pointer_max_lines", "states", "checks"):
        need(c, f, "compliance")
    if not (c.get("marker") or {}).get("path"):
        errs.append("compliance.marker.path 누락")
    typed(c, "pointer_max_lines", int, "compliance")
    for f in ("adopt_plan", "input_error_id", "override_log"):
        typed(c, f, str, "compliance")
    need(c, "override_log", "compliance")
    cd = c.get("code_detection") or {}
    for f in ("source_dirs", "exclude_dirs", "min_source_files"):
        need(cd, f, "compliance.code_detection")
    typed(cd, "source_dirs", list, "compliance.code_detection")
    typed(cd, "exclude_dirs", list, "compliance.code_detection")
    typed(cd, "min_source_files", int, "compliance.code_detection")
    states = c.get("states") or {}
    for s in _STATES:
        if not isinstance(states.get(s), dict) or not isinstance(states[s].get("next"), str):
            errs.append(f"compliance.states.{s}.next 는 문자열 필수")
    seen_ids: set[str] = set()
    for chk in c.get("checks") or []:
        cid, name = chk.get("id"), chk.get("name")
        if not cid or not name:
            errs.append(f"compliance.checks 항목에 id/name 누락: {chk}")
            continue
        if cid in seen_ids:
            errs.append(f"compliance.checks id 중복: {cid}")
        seen_ids.add(cid)
        if chk.get("severity", "error") not in _SEVERITY:
            errs.append(f"compliance.checks[{cid}].severity 는 {sorted(_SEVERITY)} 중 하나")
        for t in chk.get("applies_to", []):
            if t not in types:
                errs.append(f"compliance.checks[{cid}].applies_to 에 알 수 없는 문서: {t}")

    # adapters
    for name, ad in (m.get("adapters") or {}).items():
        if not isinstance(ad, dict) or "pointer_file" not in ad:
            errs.append(f"adapters.{name}.pointer_file 누락")

    if errs:
        raise ManifestInvalid("manifest 검증 실패:\n  - " + "\n  - ".join(errs))
