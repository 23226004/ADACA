"""L1 — 표준(SSOT) 위치 결정 및 로드.

우선순위:
  1. AUTODOCS_STANDARD_DIR 환경변수
  2. 소스 체크아웃: <repo>/standard  (이 파일 기준 상위 3단계)
  3. 패키지 동봉본: autodocs/standard (빌드 시 force-include 로 복사됨)
"""
from __future__ import annotations

import os
from pathlib import Path

from autodocs.foundation import StandardNotFound
from autodocs.platform.yaml_io import load

MANIFEST = "manifest.yaml"


def locate(explicit: Path | None = None) -> Path:
    candidates = [
        explicit,
        Path(os.environ["AUTODOCS_STANDARD_DIR"]) if os.environ.get("AUTODOCS_STANDARD_DIR") else None,
        Path(__file__).resolve().parents[3] / "standard",
        Path(__file__).resolve().parents[1] / "standard",
    ]
    for c in candidates:
        if c and (c / MANIFEST).is_file():
            return c
    raise StandardNotFound("standard/manifest.yaml 을 찾을 수 없습니다. --standard 또는 AUTODOCS_STANDARD_DIR 를 지정하세요.")


def load_manifest(standard_dir: Path) -> dict:
    m = load(standard_dir / MANIFEST)
    m["_dir"] = str(standard_dir)   # 템플릿 경로 해석용
    return m


def template_path(manifest: dict, rel: str) -> Path:
    return Path(manifest["_dir"]) / rel
