"""L2 — init: 표준 구조와 필수 문서를 생성한다. 이미 있는 파일·마커는 절대 덮어쓰지 않는다.

모든 경로는 fs.safe_path 를 거친다 (manifest 값도 신뢰하지 않는다).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from string import Template

from autodocs.features import layout, profile as profile_mod
from autodocs.foundation import Profile
from autodocs.platform import fs, standard

_LEFTOVER = re.compile(r"\$\{?([a-z][a-z0-9_]*)\}?")   # 템플릿 변수는 소문자 snake_case. $HOME 같은 셸 변수는 무시


@dataclass
class InitResult:
    created: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def run(manifest: dict, root: Path, profile: Profile, *, with_adapters: bool = True,
        extra_files: tuple[str, ...] = ()) -> InitResult:
    root = fs.require_dir(root, "프로젝트 루트")
    res = InitResult()
    subs = _substitutions(manifest, profile)
    fs.preflight(root, targets(manifest, profile, with_adapters, extra_files))   # 하나라도 문제면 아무것도 쓰지 않는다

    keep = manifest["scan"]["keep_file"]
    if (w := layout.preset_warning(manifest, profile)):
        res.warnings.append(w)
    for d in layout.required_dirs(manifest):
        _track(res, d + "/", fs.ensure_dir(root, d, keep))
    for d in layout.layer_dirs(manifest, profile).values():
        _track(res, d + "/", fs.ensure_dir(root, d, keep))
    for key, spec in layout.required_docs(manifest, profile).items():
        rel = layout.doc_path(spec)
        if rel is None:
            continue
        text = _render(manifest, spec, subs, res)
        _track(res, rel, fs.write_text(root, rel, text))
    for spec in layout.optional_docs(manifest).values():   # 선택 문서는 디렉터리만
        parent = Path(spec["path"]).parent.as_posix()
        if parent not in (".", ""):
            _track(res, f"{parent}/", fs.ensure_dir(root, parent, keep))
    if with_adapters:
        for ad in manifest.get("adapters", {}).values():
            p = ad.get("pointer_file")
            if p:
                _track(res, p, fs.write_text(root, p, _pointer(manifest, subs)))

    rel, created = profile_mod.save(manifest, root, profile)
    _track(res, rel, created)
    return res


def targets(manifest: dict, profile: Profile, with_adapters: bool, extra_files: tuple[str, ...] = ()) -> list[tuple[str, str]]:
    """init/adopt 이 건드릴 수 있는 모든 (rel, kind). 검증용이며 실제 쓰기 순서와 무관."""
    dirs = list(layout.required_dirs(manifest)) + list(layout.layer_dirs(manifest, profile).values())
    dirs += [Path(s["path"]).parent.as_posix() for s in layout.optional_docs(manifest).values()]
    files = [p for p in (layout.doc_path(s) for s in layout.required_docs(manifest, profile).values()) if p]
    if with_adapters:
        files += [ad["pointer_file"] for ad in manifest.get("adapters", {}).values() if ad.get("pointer_file")]
    files += [profile_mod.marker_rel(manifest), *extra_files]
    return [(d, "dir") for d in dirs if d not in (".", "")] + [(f, "file") for f in files]


def _substitutions(manifest: dict, profile: Profile) -> dict[str, str]:
    return {
        "project_name": profile.name,
        "project_kind": profile.kind,
        "language": profile.language,
        "standard_version": manifest["standard"]["version"],
        "date": date.today().isoformat(),
        "context_path": layout.doc_path(manifest["docs"]["types"]["project_context"]) or "",
        "layer_dirs": "\n".join(f"- {lid}: `{d}/`" for lid, d in layout.layer_dirs(manifest, profile).items()),
    }


def _render(manifest: dict, spec: dict, subs: dict[str, str], res: InitResult) -> str:
    tpl = standard.template_path(manifest, spec["template"])
    if not tpl.is_file():   # 템플릿이 아직 없으면 섹션 헤딩만으로 골격 생성
        body = "\n\n".join(f"## {s}\n\n_TODO_" for s in spec.get("sections", []))
        return f"# {spec['title']} — {subs['project_name']}\n\n{body}\n"
    text = Template(tpl.read_text(encoding="utf-8")).safe_substitute(subs)
    leftover = sorted(set(_LEFTOVER.findall(text)))
    if leftover:
        res.warnings.append(f"{spec['template']}: 치환되지 않은 변수 {', '.join(leftover)}")
    return text


def _pointer(manifest: dict, subs: dict[str, str]) -> str:
    tpl = standard.template_path(manifest, manifest["docs"]["pointer_template"])
    if tpl.is_file():
        return Template(tpl.read_text(encoding="utf-8")).safe_substitute(subs)
    return (f"# {subs['project_name']}\n\n"
            f"작업을 시작하기 전에 `{subs['context_path']}` 를 먼저 읽으세요.\n"
            f"프로젝트 규칙·현재 상태·용어는 그 문서가 단일 원천입니다. 이 파일에는 규칙을 적지 않습니다.\n")


def _track(res: InitResult, rel: str, created: bool) -> None:
    (res.created if created else res.skipped).append(rel)
