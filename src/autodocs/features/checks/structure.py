"""L2 — 구조 관련 검사 (C03 디렉터리, C04 계층, C05 의존성 방향)."""
from __future__ import annotations

from pathlib import PurePosixPath

from autodocs.features import layout
from autodocs.foundation import Context, Finding, Severity, Snapshot, norm_rel
from autodocs.platform import imports

_H = "structure"


def _f(msg: str, path: str | None = None, hint: str | None = None, sev: Severity = Severity.ERROR) -> Finding:
    return Finding(_H, sev, msg, path, hint)


def required_dirs_present(ctx: Context) -> list[Finding]:
    """디렉터리 + 문서 타입이 아닌 필수 파일. 문서 타입 파일(README 등)은 C01 이 보고하므로 중복 제외."""
    doc_paths = {layout.doc_path(s) for s in ctx.manifest["docs"]["types"].values()}
    out = [_f(f"필수 디렉터리 없음: {d}/", d) for d in layout.required_dirs(ctx.manifest) if not ctx.snapshot.has_dir(d)]
    out += [_f(f"필수 파일 없음: {p}", p) for p in layout.required_top_files(ctx.manifest)
            if p not in doc_paths and not ctx.snapshot.has_file(p)]
    return out


def layer_dirs_present(ctx: Context) -> list[Finding]:
    dirs = layout.layer_dirs(ctx.manifest, ctx.profile)
    out = [_f(f"계층 디렉터리 없음: {lid} → {d}/", d, "autodocs init 이 생성. 기존 코드는 adopt 계획에 따라 이동")
           for lid, d in dirs.items() if not ctx.snapshot.has_dir(d)]
    warn = layout.preset_warning(ctx.manifest, ctx.profile)
    if warn:
        out.append(_f(warn, ctx.manifest["compliance"]["marker"]["path"], sev=Severity.WARNING))
    return out


def dependency_direction(ctx: Context) -> list[Finding]:
    """계층 안 소스 파일의 import 를 preset.import_roots 기준으로 해석해 dependency_rules.allowed 에 없는 (src, dst) 를 보고.

    파일당 한 번 읽는다. 파싱 실패·미지원 언어는 INFO 로 남겨 조용히 통과시키지 않는다.
    """
    dirs = layout.layer_dirs(ctx.manifest, ctx.profile)
    allowed = layout.allowed_edges(ctx.manifest)
    resolver = Resolver(ctx.snapshot, dirs, layout.preset_of(ctx.manifest, ctx.profile), ctx.manifest["scan"])
    languages = ctx.manifest["scan"]["source_ext"]
    out = []
    for rel in sorted(ctx.snapshot.source_files):
        src_layer = resolver.layer_of_path(rel)
        if src_layer is None:
            continue
        lang = languages.get(PurePosixPath(rel).suffix)
        scan = imports.extract(PurePosixPath(rel), ctx.snapshot.read(rel), lang)
        if scan.error == "unsupported":
            out.append(_f(f"{lang}: import 해석 미지원 — 의존성 검사에서 제외됨", rel, sev=Severity.INFO))
            continue
        if scan.error:
            out.append(_f(f"파싱 실패로 의존성 검사에서 제외됨: {scan.error}", rel, sev=Severity.INFO))
            continue
        seen: set[str] = set()   # 파일당 목적지 계층별 1건 (같은 계층으로의 여러 import 는 첫 번째만 보고)
        for ref in scan.refs:
            dst_layer = resolver.layer_of_import(rel, ref, lang)
            if dst_layer and dst_layer != src_layer and (src_layer, dst_layer) not in allowed and dst_layer not in seen:
                seen.add(dst_layer)
                out.append(_f(f"{src_layer} → {dst_layer} 허용되지 않는 의존: {rel} imports {ref}", rel,
                              f"{dst_layer} 의 기능을 {src_layer} 에서 직접 참조하지 말고, 계약(interface)을 {src_layer} 이하로 내리거나 호출 방향을 뒤집으세요"))
    return out


class Resolver:
    """import 문자열 → 계층 id. 해석된 경로가 Snapshot 에 실제로 존재할 때만 계층으로 인정한다.

    - 상대 import (./, ../, 파이썬 ..) : 소스 파일 위치 기준
    - alias ($lib/…)                    : preset.aliases
    - 절대 (dotted 또는 경로형)          : preset.import_roots 각각의 아래에서 찾는다.
      dotted 는 a.b.c → a/b/c, a/b, a 순으로(마지막 세그먼트가 심볼일 수 있음), dotnet 은 디렉터리명에 '.' 이 있으므로
      'a.b/c' 형태도 시도한다. 어느 것도 존재하지 않으면 외부 패키지로 보고 무시.
    """

    _JS_TO_TS = {".js": (".ts", ".tsx"), ".jsx": (".tsx",), ".mjs": (".mts", ".ts"), ".cjs": (".cts", ".ts")}

    def __init__(self, snapshot: Snapshot, layer_dirs: dict[str, str], preset: dict, scan_policy: dict):
        self.snap = snapshot
        self.by_path = sorted(layer_dirs.items(), key=lambda kv: -len(kv[1]))  # 긴 경로 우선
        self.roots = [norm_rel(r) for r in preset.get("import_roots", [])]
        self.aliases = {k: norm_rel(v) for k, v in preset.get("aliases", {}).items()}
        self.exts = ("",) + tuple(scan_policy["source_ext"]) + tuple("/" + i for i in scan_policy["index_files"])

    def layer_of_path(self, rel: str) -> str | None:
        for lid, d in self.by_path:
            if rel == d or rel.startswith(d + "/"):
                return lid
        return None

    def _exists(self, rel: str) -> bool:
        if any(self.snap.has_file(rel + e) or (e == "" and self.snap.has_dir(rel)) for e in self.exts):
            return True
        stem, dot, ext = rel.rpartition(".")            # ESM 관례: '../a.js' 가 실제로는 a.ts
        return dot == "." and any(self.snap.has_file(f"{stem}{t}") for t in self._JS_TO_TS.get("." + ext, ()))

    def _layer_if_exists(self, rel: str) -> str | None:
        rel = _norm(PurePosixPath(rel))
        return self.layer_of_path(rel) if rel and self._exists(rel) else None

    def layer_of_import(self, src_rel: str, ref: str, language: str | None = None) -> str | None:
        for alias, target in self.aliases.items():
            if ref == alias or ref.startswith(alias + "/"):
                return self._layer_if_exists(target + ref[len(alias):])
        base = PurePosixPath(src_rel).parent
        if ref.startswith("./") or ref.startswith("../"):            # TS/JS 상대 경로
            return self._layer_if_exists(str(base / ref))
        if language == "typescript" and not ref.startswith("."):     # bare specifier 는 항상 패키지 (alias 는 위에서 처리)
            return next((l for r in self.roots if r and ref.startswith(r + "/") and (l := self._layer_if_exists(ref))), None)
        if ref.startswith("."):                                       # Python 상대 import
            level = len(ref) - len(ref.lstrip("."))
            target = base
            for _ in range(level - 1):
                target = target.parent
            tail = ref.lstrip(".").replace(".", "/")
            return self._layer_if_exists(str(target / tail) if tail else str(target))
        if "/" in ref:                                                # 경로형 절대 (import_root 기준)
            return next((l for r in self.roots if (l := self._layer_if_exists(_join(r, ref)))), None)
        parts = ref.split(".")                                        # dotted 절대 (python / C#)
        for r in self.roots:
            for k in range(len(parts), 0, -1):
                for cand in (_join(r, "/".join(parts[:k])), _join(r, ".".join(parts[:k]))):
                    if (l := self._layer_if_exists(cand)):
                        return l
        return None


def _join(root: str, rel: str) -> str:
    return f"{root}/{rel}" if root else rel


def _norm(p: PurePosixPath) -> str:
    parts: list[str] = []
    for seg in p.parts:
        if seg == "..":
            if parts:
                parts.pop()
        elif seg not in (".", ""):
            parts.append(seg)
    return "/".join(parts)
