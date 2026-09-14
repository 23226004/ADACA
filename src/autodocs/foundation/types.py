"""L0 Contracts — 엔진 전 계층이 공유하는 불변 데이터 구조.

상위 계층(platform/features)을 알지 않는다. 표준 라이브러리만 사용.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class State(str, Enum):
    """준수 상태 (manifest.compliance.states)."""

    NEW = "new"              # 마커 없음, 코드 없음 → init
    LEGACY = "legacy"        # 마커 없음, 코드 있음 → adopt
    PARTIAL = "partial"      # 마커 있음, 위반 있음
    COMPLIANT = "compliant"  # 마커 있음, 위반 없음


@dataclass(frozen=True)
class Finding:
    """단일 검사 결과. check_id 는 manifest.compliance.checks[].id 와 일치."""

    check_id: str
    severity: Severity
    message: str
    path: str | None = None
    fix_hint: str | None = None


@dataclass(frozen=True)
class Snapshot:
    """파일 시스템을 정확히 한 번 스캔한 결과. 모든 check 는 이것만 본다 (O(n) 보장)."""

    root: Path
    files: frozenset[str]          # root 기준 상대 경로 (posix). 파일만.
    dirs: frozenset[str]           # 상대 경로. 끝에 '/' 없음.
    source_files: frozenset[str]   # 소스 코드로 간주되는 파일의 부분집합

    def has_file(self, rel: str) -> bool:
        return rel.strip("/") in self.files

    def has_dir(self, rel: str) -> bool:
        return rel.strip("/") in self.dirs

    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class Profile:
    """`.standard/project.yaml` — 프로젝트가 스스로 선언한 프로필."""

    name: str
    kind: str
    language: str
    standard_version: str
    has_api: bool = False
    has_database: bool = False
    layout_preset: str = "generic"
    extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Context:
    """한 번의 명령 실행에 필요한 모든 입력. check 함수의 유일한 인자."""

    manifest: dict
    snapshot: Snapshot
    profile: Profile | None


@dataclass(frozen=True)
class Report:
    state: State
    findings: tuple[Finding, ...]

    @property
    def errors(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity == Severity.ERROR)

    @property
    def ok(self) -> bool:
        return not self.errors
