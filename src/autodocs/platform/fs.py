"""L1 — 파일 시스템 접근. 프로젝트 트리를 정확히 한 번 걷고, 쓰기는 반드시 safe_path 를 거친다."""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

from autodocs.foundation import AutodocsError, PathEscape, Snapshot, norm_rel

SOURCE_EXT = {".py", ".cs", ".ts", ".js", ".svelte", ".java", ".go", ".rs"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
             ".mypy_cache", ".pytest_cache", "bin", "obj", ".svelte-kit"}


def require_dir(path: Path, what: str = "경로") -> Path:
    if not path.is_dir():
        raise AutodocsError(f"{what}가 디렉터리가 아니거나 존재하지 않습니다: {path}")
    return path.resolve()


def safe_path(root: Path, rel: str) -> Path:
    """root 아래의 절대 경로를 돌려준다. 다음 중 하나면 PathEscape:

    - rel 이 절대 경로이거나 '..' 를 포함 (norm_rel)
    - 경로의 어떤 기존 구성 요소든 심볼릭 링크 (링크를 따라 root 밖으로 나갈 수 있음)
    - resolve 결과가 root 밖
    엔진이 쓰는(또는 템플릿을 읽는) 모든 경로는 이 함수를 통해서만 만든다.
    """
    root = root.resolve()
    key = norm_rel(rel)
    cur = root
    for part in PurePosixPath(key).parts:
        cur = cur / part
        if cur.is_symlink():
            raise PathEscape(f"심볼릭 링크는 허용하지 않음: {key}")
    target = (root / PurePosixPath(key)).resolve() if key else root
    if target != root and root not in target.parents:
        raise PathEscape(f"root 밖 경로: {rel}")
    return target


def scan(root: Path, *, skip_dirs: set[str] = SKIP_DIRS, source_ext: set[str] = SOURCE_EXT) -> Snapshot:
    """os.walk 한 번으로 Snapshot 생성. 이후 어떤 check 도 디스크를 다시 걷지 않는다. 심링크는 따라가지 않는다."""
    root = require_dir(root, "프로젝트 루트")
    files: set[str] = set()
    dirs: set[str] = set()
    for cur, subdirs, names in os.walk(root, followlinks=False):
        subdirs[:] = [d for d in subdirs if d not in skip_dirs]
        rel_dir = Path(cur).relative_to(root).as_posix()
        if rel_dir != ".":
            dirs.add(rel_dir)
        for n in names:
            files.add(n if rel_dir == "." else f"{rel_dir}/{n}")
    source = frozenset(f for f in files if Path(f).suffix in source_ext)
    return Snapshot(root=root, files=frozenset(files), dirs=frozenset(dirs), source_files=source)


def write_text(root: Path, rel: str, content: str) -> bool:
    """root/rel 에 파일 생성. 이미 있으면(심링크 포함) 건드리지 않고 False."""
    path = safe_path(root, rel)
    if path.exists() or path.is_symlink():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8") as f:   # 'x': 경쟁 상태에서도 덮어쓰지 않음
        f.write(content)
    return True


def ensure_dir(root: Path, rel: str) -> bool:
    path = safe_path(root, rel)
    if path.is_dir():
        return False
    path.mkdir(parents=True, exist_ok=True)
    (path / ".gitkeep").touch()
    return True
