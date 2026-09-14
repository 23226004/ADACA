from pathlib import Path

import pytest

from autodocs.features import profile as profile_mod
from autodocs.platform import standard

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def manifest() -> dict:
    return standard.load_manifest(REPO / "standard")   # 개발자 셸의 AUTODOCS_STANDARD_DIR 와 무관하게 저장소 표준을 쓴다


@pytest.fixture
def profile(manifest):
    return profile_mod.from_dict(manifest, {
        "name": "demo", "kind": "web", "language": "python",
        "standard_version": manifest["standard"]["version"], "has_api": True, "has_database": False,
    })
