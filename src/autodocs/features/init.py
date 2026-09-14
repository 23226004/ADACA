"""L2 — init: 표준 구조와 필수 문서를 생성한다. 이미 있는 파일은 절대 덮어쓰지 않는다."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from string import Template

from autodocs.features import layout, profile as profile_mod
from autodocs.foundation import Profile
from autodocs.platform import fs, standard


@dataclass
class InitResult:
    created: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def run(manifest: dict, root: Path, profile: Profile, *, with_adapters: bool = True) -> InitResult:
    res = InitResult()
    subs = _substitutions(manifest, profile)

    for d in layout.required_dirs(manifest):
        _track(res, d + "/", fs.ensure_dir(root / d))
    for d in layout.layer_dirs(manifest, profile).values():
        _track(res, d + "/", fs.ensure_dir(root / d))
    for key, spec in layout.required_docs(manifest, profile).items():
        rel = spec["path"]
        if "{" in rel:
            continue
        _track(res, rel, fs.write_text(root / rel, _render(manifest, spec, subs)))
    for key, spec in layout.optional_docs(manifest).items():   # 선택 문서는 디렉터리만
        parent = Path(spec["path"]).parent
        if str(parent) not in (".", ""):
            _track(res, f"{parent}/", fs.ensure_dir(root / parent))
    if with_adapters:
        for ad in manifest.get("adapters", {}).values():
            p = ad.get("pointer_file")
            if p:
                _track(res, p, fs.write_text(root / p, _pointer(manifest, subs)))

    path = profile_mod.save(manifest, root, profile)
    res.created.append(path.relative_to(root).as_posix())
    return res


def _substitutions(manifest: dict, profile: Profile) -> dict[str, str]:
    return {
        "project_name": profile.name,
        "project_kind": profile.kind,
        "language": profile.language,
        "standard_version": manifest["standard"]["version"],
        "date": date.today().isoformat(),
        "context_path": manifest["docs"]["types"]["project_context"]["path"],
        "layer_dirs": "\n".join(f"- {lid}: `{d}/`" for lid, d in layout.layer_dirs(manifest, profile).items()),
    }


def _render(manifest: dict, spec: dict, subs: dict[str, str]) -> str:
    tpl = standard.template_path(manifest, spec["template"])
    if not tpl.is_file():   # 템플릿이 아직 없으면 섹션 헤딩만으로 골격 생성
        body = "\n\n".join(f"## {s}\n\n_TODO_" for s in spec.get("sections", []))
        return f"# {spec['title']} — {subs['project_name']}\n\n{body}\n"
    return Template(tpl.read_text(encoding="utf-8")).safe_substitute(subs)


def _pointer(manifest: dict, subs: dict[str, str]) -> str:
    tpl = standard.template_path(manifest, "templates/POINTER.md")
    if tpl.is_file():
        return Template(tpl.read_text(encoding="utf-8")).safe_substitute(subs)
    return (f"# {subs['project_name']}\n\n"
            f"작업을 시작하기 전에 `{subs['context_path']}` 를 먼저 읽으세요.\n"
            f"프로젝트 규칙·현재 상태·용어는 그 문서가 단일 원천입니다. 이 파일에는 규칙을 적지 않습니다.\n")


def _track(res: InitResult, rel: str, created: bool) -> None:
    (res.created if created else res.skipped).append(rel)
