"""L1 — 소스 파일에서 import 대상 모듈 경로를 추출한다 (C05 의존성 방향 검사용).

Python 은 ast 로 정확히, 그 외 언어는 정규식으로 근사한다.
반환값은 "모듈 경로 문자열" 목록이며 해석(어느 계층인지)은 features 가 한다.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

_TS_IMPORT = re.compile(r"""(?:import|export)\s[^'"]*?from\s+['"]([^'"]+)['"]|import\s*\(\s*['"]([^'"]+)['"]\s*\)|require\(\s*['"]([^'"]+)['"]\s*\)""")
_CS_USING = re.compile(r"^\s*using\s+(?:static\s+)?([\w.]+)\s*;", re.M)


def extract(path: Path, text: str) -> list[str]:
    suffix = path.suffix
    if suffix == ".py":
        return _python(text)
    if suffix in {".ts", ".js", ".svelte"}:
        return [next(g for g in m.groups() if g) for m in _TS_IMPORT.finditer(text)]
    if suffix == ".cs":
        return _CS_USING.findall(text)
    return []


def _python(text: str) -> list[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            out.append(("." * node.level) + (node.module or ""))
    return out
