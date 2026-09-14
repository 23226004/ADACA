"""L2 — 구조 관련 검사 (C03 디렉터리, C04 계층, C05 의존성 방향)."""
from __future__ import annotations

from pathlib import PurePosixPath

from autodocs.features import layout
from autodocs.foundation import Context, Finding, Severity
from autodocs.platform import imports

_H = "structure"


def _f(msg: str, path: str | None = None, hint: str | None = None) -> Finding:
    return Finding(_H, Severity.ERROR, msg, path, hint)


def required_dirs_present(ctx: Context) -> list[Finding]:
    out = [_f(f"필수 디렉터리 없음: {d}/", d) for d in layout.required_dirs(ctx.manifest) if not ctx.snapshot.has_dir(d)]
    out += [_f(f"필수 파일 없음: {p}", p) for p in layout.required_top_files(ctx.manifest) if not ctx.snapshot.has_file(p)]
    return out


def layer_dirs_present(ctx: Context) -> list[Finding]:
    dirs = layout.layer_dirs(ctx.manifest, ctx.profile)
    return [_f(f"계층 디렉터리 없음: {lid} → {d}/", d, "autodocs init 이 생성. 기존 코드는 adopt 계획에 따라 이동")
            for lid, d in dirs.items() if not ctx.snapshot.has_dir(d)]


def dependency_direction(ctx: Context) -> list[Finding]:
    """소스 파일의 계층 < import 대상 계층 이면 상향 의존 → 위반. 파일당 한 번 읽는다."""
    dirs = layout.layer_dirs(ctx.manifest, ctx.profile)
    order = layout.layer_order(ctx.manifest)
    rank = {lid: i for i, lid in enumerate(order)}
    resolver = _Resolver(dirs)
    out = []
    for rel in sorted(ctx.snapshot.source_files):
        src_layer = resolver.layer_of_path(rel)
        if src_layer is None:
            continue
        text = ctx.snapshot.read(rel)
        for mod in imports.extract(PurePosixPath(rel), text):
            dst_layer = resolver.layer_of_import(rel, mod)
            if dst_layer and rank[dst_layer] > rank[src_layer]:
                out.append(_f(f"{src_layer} → {dst_layer} 상향 의존: {rel} imports {mod}", rel,
                              f"{dst_layer} 의 기능을 {src_layer} 에서 직접 참조하지 말고, 계약(interface)을 {src_layer} 이하로 내리거나 호출 방향을 뒤집으세요"))
    return out


class _Resolver:
    """경로/모듈 문자열 → 계층 id. 계층 dir 의 여러 표기(경로, dotted, $lib alias)를 미리 만들어 둔다."""

    def __init__(self, layer_dirs: dict[str, str]):
        self.by_path = sorted(layer_dirs.items(), key=lambda kv: -len(kv[1]))  # 긴 경로 우선
        self.dotted: list[tuple[str, str]] = []
        for lid, d in layer_dirs.items():
            parts = d.split("/")
            for strip in ({"src"}, {"src", "lib"}, set()):
                dotted = ".".join(p for p in parts if p not in strip)
                if dotted:
                    self.dotted.append((lid, dotted))
        self.dotted.sort(key=lambda kv: -len(kv[1]))

    def layer_of_path(self, rel: str) -> str | None:
        for lid, d in self.by_path:
            if rel == d or rel.startswith(d + "/"):
                return lid
        return None

    def layer_of_import(self, src_rel: str, mod: str) -> str | None:
        if mod.startswith("$lib/"):
            return self.layer_of_path("src/lib/" + mod[5:])
        if mod.startswith("."):
            base = PurePosixPath(src_rel).parent
            if "/" in mod:                                   # TS/JS 상대 경로
                return self.layer_of_path(_norm(base / mod))
            level = len(mod) - len(mod.lstrip("."))         # Python 상대 import
            target = base
            for _ in range(level - 1):
                target = target.parent
            tail = mod.lstrip(".").replace(".", "/")
            return self.layer_of_path(_norm(target / tail) if tail else _norm(target))
        for lid, dotted in self.dotted:                      # 절대 dotted (python/C#)
            if mod == dotted or mod.startswith(dotted + "."):
                return lid
        return self.layer_of_path(mod)                       # 경로형 절대 import


def _norm(p: PurePosixPath) -> str:
    parts: list[str] = []
    for seg in p.parts:
        if seg == "..":
            if parts:
                parts.pop()
        elif seg not in (".", ""):
            parts.append(seg)
    return "/".join(parts)
