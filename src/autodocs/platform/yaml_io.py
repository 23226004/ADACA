"""L1 — YAML 읽기/쓰기. PyYAML 의존은 이 모듈에만 둔다."""
from __future__ import annotations

from pathlib import Path

import yaml


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def dump(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
