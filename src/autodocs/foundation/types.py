"""L0 Contracts — 엔진 전 계층이 공유하는 불변 데이터 구조.

상위 계층(platform/features)을 알지 않는다. 표준 라이브러리만 사용.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .errors import AutodocsError
from .paths import norm_rel, safe_path


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
    """파일 시스템을 정확히 한 번 스캔한 결과. 모든 check 는 이것만 본다 (O(n) 보장).

    read() 는 파일당 한 번만 디스크를 읽고 캐시한다 (frozen 이지만 캐시 dict 는 내부 가변 상태).
    """

    root: Path
    files: frozenset[str]          # root 기준 상대 경로 (posix). 파일만.
    dirs: frozenset[str]           # 상대 경로. 끝에 '/' 없음.
    source_files: frozenset[str]   # 소스 코드로 간주되는 파일의 부분집합
    errors: tuple[str, ...] = ()   # 스캔 중 읽을 수 없었던 디렉터리 (권한 등). audit 가 finding 으로 올린다
    _cache: dict = field(default_factory=dict, repr=False, compare=False)

    def has_file(self, rel: str) -> bool:
        return norm_rel(rel) in self.files

    def has_dir(self, rel: str) -> bool:
        return norm_rel(rel) in self.dirs

    def read(self, rel: str) -> str:
        key = norm_rel(rel)
        if key not in self._cache:   # 읽기도 쓰기와 같은 경로 정책 (root 밖 심링크 거부)
            try:
                self._cache[key] = safe_path(self.root, key).read_text(encoding="utf-8", errors="replace")
            except OSError as e:      # 권한 등. 호출자(check) 가 finding 으로 바꾼다
                raise AutodocsError(f"읽기 실패: {key} ({e.strerror or e})") from e
        return self._cache[key]

    @property
    def reads(self) -> int:
        """디스크에서 실제로 읽은 파일 수 (테스트용)."""
        return len(self._cache)


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
