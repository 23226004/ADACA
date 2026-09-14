"""L1 — 파일 시스템 접근. 프로젝트 트리를 정확히 한 번 걷는다."""
from __future__ import annotations

import os
from pathlib import Path

from autodocs.foundation import Snapshot

SOURCE_EXT = {".py", ".cs", ".ts", ".js", ".svelte", ".java", ".go", ".rs"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
             ".mypy_cache", ".pytest_cache", "bin", "obj", ".svelte-kit"}


def scan(root: Path) -> Snapshot:
    """os.walk 한 번으로 Snapshot 생성. 이후 어떤 check 도 디스크를 다시 걷지 않는다."""
    root = root.resolve()
    files: set[str] = set()
    dirs: set[str] = set()
    for cur, subdirs, names in os.walk(root):
        subdirs[:] = [d for d in subdirs if d not in SKIP_DIRS]
        rel_dir = Path(cur).relative_to(root).as_posix()
        if rel_dir != ".":
            dirs.add(rel_dir)
        for n in names:
            files.add(n if rel_dir == "." else f"{rel_dir}/{n}")
    source = frozenset(f for f in files if Path(f).suffix in SOURCE_EXT)
    return Snapshot(root=root, files=frozenset(files), dirs=frozenset(dirs), source_files=source)


def write_text(path: Path, content: str, *, overwrite: bool = False) -> bool:
    """파일 생성. 이미 있으면 overwrite=False 일 때 건드리지 않고 False 반환."""
    if path.exists() and not overwrite:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def ensure_dir(path: Path) -> bool:
    if path.is_dir():
        return False
    path.mkdir(parents=True, exist_ok=True)
    (path / ".gitkeep").touch()
    return True
