"""L1 — 파일 시스템 접근. 프로젝트 트리를 정확히 한 번 걷고, 쓰기는 반드시 foundation.safe_path 를 거친다.

심링크 정책: root 안을 가리키는 링크는 "이미 있음" 으로 취급해 건너뛴다. root 밖은 PathEscape."""
from __future__ import annotations

import os
import stat
from pathlib import Path

from autodocs.foundation import AutodocsError, Snapshot, safe_path

SOURCE_EXT = {".py", ".cs", ".ts", ".js", ".svelte", ".java", ".go", ".rs"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
             ".mypy_cache", ".pytest_cache", "bin", "obj", ".svelte-kit"}


def require_dir(path: Path, what: str = "경로") -> Path:
    if not path.is_dir():
        raise AutodocsError(f"{what}가 디렉터리가 아니거나 존재하지 않습니다: {path}")
    return path.resolve()


def scan(root: Path, *, skip_dirs: set[str] = SKIP_DIRS, source_ext: set[str] = SOURCE_EXT) -> Snapshot:
    """os.walk 한 번으로 Snapshot 생성. 이후 어떤 check 도 디스크를 다시 걷지 않는다. 심링크는 따라가지 않는다."""
    root = require_dir(root, "프로젝트 루트")
    files: set[str] = set()
    dirs: set[str] = set()
    errors: list[str] = []

    def on_error(e: OSError) -> None:   # 읽을 수 없는 디렉터리를 조용히 건너뛰지 않는다
        errors.append(Path(e.filename).relative_to(root).as_posix() if e.filename else str(e))

    for cur, subdirs, names in os.walk(root, followlinks=False, onerror=on_error):
        subdirs[:] = [d for d in subdirs if d not in skip_dirs]
        rel_dir = Path(cur).relative_to(root).as_posix()
        if rel_dir != ".":
            dirs.add(rel_dir)
        for n in names:
            mode = os.lstat(os.path.join(cur, n)).st_mode
            if stat.S_ISREG(mode) or stat.S_ISLNK(mode):   # FIFO·소켓·디바이스는 파일로 치지 않는다 (read 가 블록됨)
                files.add(n if rel_dir == "." else f"{rel_dir}/{n}")
    source = frozenset(f for f in files if Path(f).suffix in source_ext)
    return Snapshot(root=root, files=frozenset(files), dirs=frozenset(dirs), source_files=source, errors=tuple(errors))


def write_text(root: Path, rel: str, content: str) -> bool:
    """root/rel 에 파일 생성. 이미 있으면(심링크 포함) 건드리지 않고 False. 그 자리에 디렉터리가 있으면 오류."""
    path = safe_path(root, rel)
    if path.is_dir() and not path.is_symlink():
        raise AutodocsError(f"파일 자리에 디렉터리가 있습니다: {rel}")
    if path.exists() or path.is_symlink():   # dangling 이라도 root 안 링크면 건드리지 않는다
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8") as f:   # 'x': 경쟁 상태에서도 덮어쓰지 않음
        f.write(content)
    return True


def ensure_dir(root: Path, rel: str) -> bool:
    path = safe_path(root, rel)
    if path.is_dir() or path.is_symlink():
        return False
    if path.exists():
        raise AutodocsError(f"디렉터리 자리에 파일이 있습니다: {rel}")
    path.mkdir(parents=True, exist_ok=True)
    (path / ".gitkeep").touch()
    return True


def preflight(root: Path, targets: list[tuple[str, str]]) -> None:
    """쓰기 전에 모든 (rel, kind) 를 먼저 검증한다. kind 는 'file' | 'dir'.
    경로 탈출이나 종류 불일치(파일 자리에 디렉터리 등)가 하나라도 있으면 아무것도 쓰지 않는다 (원자성)."""
    for rel, kind in targets:
        p = safe_path(root, rel)
        if p.is_symlink():
            continue
        if kind == "dir" and p.exists() and not p.is_dir():
            raise AutodocsError(f"디렉터리 자리에 파일이 있습니다: {rel}")
        if kind == "file" and p.is_dir():
            raise AutodocsError(f"파일 자리에 디렉터리가 있습니다: {rel}")
