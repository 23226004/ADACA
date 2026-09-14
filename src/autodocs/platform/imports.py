"""L1 — 소스 파일에서 import 대상 문자열을 추출한다 (C05 의존성 방향 검사용).

반환: ImportScan(refs, error). refs 는 "모듈/경로 문자열" 목록이고 해석(어느 계층인지)은 features 가 한다.
  - python     : ast. `from X import a, b` 는 X 와 X.a, X.b 모두 후보 (a 가 서브모듈일 수 있음)
  - typescript : 주석 제거 후 정규식. from/side-effect/dynamic import/require
  - csharp     : 주석 제거 후 `using X;`, `using A = X;`, `global using X;`
  - 그 외 언어  : error="unsupported" — 조용히 통과시키지 않고 호출자가 INFO 로 보고
파싱 실패도 error 로 돌려준다 (SyntaxError, null byte 등).
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath

_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_LINE_COMMENT = re.compile(r"(?m)^\s*//.*$|(?<=[;{}\s])//(?![^\n]*['\"]\s*[;)]).*$")
_TS_FROM = re.compile(r"""(?:import|export)\s+(?:type\s+)?[^'";]*?\sfrom\s+['"]([^'"]+)['"]""")
_TS_SIDE = re.compile(r"""(?m)^\s*import\s+['"]([^'"]+)['"]""")
_TS_DYN = re.compile(r"""(?:import\s*\(|require\s*\()\s*['"]([^'"]+)['"]\s*\)""")
_CS_USING = re.compile(r"\busing\s+(?:static\s+)?(?:\w+\s*=\s*)?([\w.]+)\s*;")   # global using 도 \busing 으로 잡힘


@dataclass(frozen=True)
class ImportScan:
    refs: tuple[str, ...] = ()
    error: str | None = None   # "unsupported" | 파싱 오류 메시지


def extract(path: PurePosixPath, text: str, language: str | None) -> ImportScan:
    if language == "python":
        return _python(text)
    if language == "typescript":
        return ImportScan(tuple(_typescript(text)))
    if language == "csharp":
        return ImportScan(tuple(_CS_USING.findall(_strip_c_comments(text))))
    return ImportScan(error="unsupported")


def _python(text: str) -> ImportScan:
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError) as e:   # ValueError: null byte (3.10)
        return ImportScan(error=f"{type(e).__name__}: {e}")
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = ("." * node.level) + (node.module or "")
            out.append(base)
            for a in node.names:               # `from .. import features` → ..features
                if a.name != "*":
                    out.append(base + ("" if base.endswith(".") or not base else ".") + a.name)
    return ImportScan(tuple(out))


def _typescript(text: str) -> list[str]:
    t = _strip_c_comments(text)
    return _TS_FROM.findall(t) + _TS_SIDE.findall(t) + _TS_DYN.findall(t)


def _strip_c_comments(text: str) -> str:
    return _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", text))
