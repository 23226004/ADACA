"""L1 — 표준(SSOT) 위치 결정 및 로드.

우선순위:
  1. --standard (명시) — 없으면 오류. 폴백하지 않는다.
  2. AUTODOCS_STANDARD_DIR 환경변수 — 없으면 오류. 폴백하지 않는다.
  3. 소스 체크아웃: <repo>/standard
  4. 패키지 동봉본: autodocs/standard (빌드 시 force-include 로 복사됨)
명시된 경로가 틀렸는데 조용히 기본값으로 떨어지면, 사용자는 커스텀 표준을 쓴다고 믿은 채 다른 규칙으로 검사받는다.
"""
from __future__ import annotations

import os
from pathlib import Path

from autodocs.foundation import StandardNotFound, safe_path
from autodocs.platform.manifest_schema import validate
from autodocs.platform.yaml_io import load

MANIFEST = "manifest.yaml"


def locate(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return _must(explicit, "--standard")
    env = os.environ.get("AUTODOCS_STANDARD_DIR")
    if env:
        return _must(Path(env), "AUTODOCS_STANDARD_DIR")
    for c in (Path(__file__).resolve().parents[3] / "standard", Path(__file__).resolve().parents[1] / "standard"):
        if (c / MANIFEST).is_file():
            return c
    raise StandardNotFound("standard/manifest.yaml 을 찾을 수 없습니다. --standard 또는 AUTODOCS_STANDARD_DIR 를 지정하세요.")


def _must(d: Path, origin: str) -> Path:
    if not (d / MANIFEST).is_file():
        raise StandardNotFound(f"{origin}={d} 에 {MANIFEST} 이 없습니다.")
    return d.resolve()


def load_manifest(standard_dir: Path) -> dict:
    m = load(standard_dir / MANIFEST)
    validate(m)                               # 구조·enum·참조 무결성. 실패는 ManifestInvalid 하나로
    m["_dir"] = str(standard_dir.resolve())   # 템플릿 경로 해석용
    return m


def template_path(manifest: dict, rel: str) -> Path:
    """템플릿은 standard_dir 아래만 허용 (심링크는 목적지가 그 안일 때만). manifest 의 template: 값도 신뢰하지 않는다."""
    return safe_path(Path(manifest["_dir"]), rel)
