"""L2 — `.standard/project.yaml` 읽기/쓰기/검증."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from autodocs.foundation import Profile, ProfileInvalid, Snapshot
from autodocs.platform import yaml_io

_FIELDS = {"name", "kind", "language", "standard_version", "has_api", "has_database", "layout_preset"}


def marker_rel(manifest: dict) -> str:
    return manifest["compliance"]["marker"]["path"]


def load(manifest: dict, snapshot: Snapshot) -> Profile | None:
    rel = marker_rel(manifest)
    if not snapshot.has_file(rel):
        return None
    raw = yaml_io.load(snapshot.root / rel)
    return from_dict(manifest, raw)


def from_dict(manifest: dict, raw: dict) -> Profile:
    schema = manifest["project_profile"]["schema"]
    missing = [k for k, s in schema.items() if s.get("required") and k not in raw]
    if missing:
        raise ProfileInvalid(f"project.yaml 필수 항목 누락: {', '.join(missing)}")
    for k, s in schema.items():
        if s.get("type") == "enum" and k in raw and raw[k] not in s["values"]:
            raise ProfileInvalid(f"project.yaml {k}={raw[k]!r} 는 허용값 {s['values']} 에 없습니다")
    known = {k: v for k, v in raw.items() if k in _FIELDS}
    extra = {k: v for k, v in raw.items() if k not in _FIELDS}
    return Profile(**known, extra=extra)


def save(manifest: dict, root: Path, profile: Profile) -> Path:
    data = asdict(profile)
    extra = data.pop("extra")
    data.update(extra)
    path = root / marker_rel(manifest)
    yaml_io.dump(data, path)
    return path
