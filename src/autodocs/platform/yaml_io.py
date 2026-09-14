"""L1 — YAML 읽기/쓰기. PyYAML 의존은 이 모듈에만 둔다. 파싱 오류는 AutodocsError 로 바꾼다."""
from __future__ import annotations

from pathlib import Path

import yaml

from autodocs.foundation import AutodocsError


def load(path: Path) -> dict:
    return loads(path.read_text(encoding="utf-8"), where=str(path))


def loads(text: str, *, where: str = "<text>") -> dict:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise AutodocsError(f"YAML 파싱 실패: {where} — {e}") from e
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise AutodocsError(f"YAML 최상위가 매핑이 아닙니다: {where}")
    return data


def dump(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
