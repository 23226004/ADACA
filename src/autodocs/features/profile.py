"""L2 — `.standard/project.yaml` 읽기/검증/쓰기. 스키마는 manifest.project_profile.schema 가 정의한다."""
from __future__ import annotations

from dataclasses import asdict, fields
from pathlib import Path

from autodocs.foundation import Profile, ProfileInvalid, Snapshot, norm_rel
from autodocs.platform import fs, yaml_io

_KNOWN = {f.name for f in fields(Profile)} - {"extra"}
_TYPES = {"string": str, "enum": str, "bool": bool}


def marker_rel(manifest: dict) -> str:
    return norm_rel(manifest["compliance"]["marker"]["path"])


def load(manifest: dict, snapshot: Snapshot) -> Profile | None:
    rel = marker_rel(manifest)
    if not snapshot.has_file(rel):
        return None
    return from_dict(manifest, yaml_io.load(snapshot.root / rel))


def from_dict(manifest: dict, raw: dict) -> Profile:
    schema = manifest["project_profile"]["schema"]
    missing = [k for k, s in schema.items() if s.get("required") and k not in raw]
    if missing:
        raise ProfileInvalid(f"project.yaml 필수 항목 누락: {', '.join(missing)}")
    data: dict = {}
    for k, s in schema.items():
        if k not in raw:
            if "default" in s:
                data[k] = s["default"]
            continue
        v = raw[k]
        want = _TYPES.get(s.get("type", "string"), str)
        if not isinstance(v, want) or (want is str and isinstance(v, bool)):
            raise ProfileInvalid(f"project.yaml {k}: {s.get('type')} 이어야 함, 실제 {type(v).__name__}")
        if s.get("type") == "enum" and v not in s["values"]:
            raise ProfileInvalid(f"project.yaml {k}={v!r} 는 허용값 {s['values']} 에 없습니다")
        data[k] = v
    presets = manifest["structure"].get("presets", {})
    if data.get("layout_preset", "generic") not in presets:
        raise ProfileInvalid(f"project.yaml layout_preset={data.get('layout_preset')!r} 는 presets 에 없습니다 ({', '.join(presets)})")
    known = {k: v for k, v in data.items() if k in _KNOWN}
    extra = {k: v for k, v in raw.items() if k not in _KNOWN}
    return Profile(**known, extra=extra)


def save(manifest: dict, root: Path, profile: Profile) -> tuple[str, bool]:
    """마커 생성. 이미 있으면 절대 덮어쓰지 않는다 (init 재실행이 프로필을 바꾸면 안 된다). (rel, created)"""
    data = asdict(profile)
    data.update(data.pop("extra"))
    rel = marker_rel(manifest)
    path = fs.safe_path(root, rel)
    if path.exists() or path.is_symlink():
        return rel, False
    yaml_io.dump(data, path)
    return rel, True
