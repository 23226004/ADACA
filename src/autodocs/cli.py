"""autodocs CLI — 얇은 디스패처. 판단 로직은 features 에만 있다.

  autodocs audit  [--json]                     준수 상태 판정 (new/legacy/partial/compliant)
  autodocs check  [--json]                     audit 와 같으나 error 가 있으면 exit 1 (PR 게이트용)
  autodocs init   --name X --kind web --language python [--api] [--db] [--preset generic]
  autodocs adopt  --name X --kind web --language python [--api] [--db] [--preset generic]

exit code: 0 통과 · 1 위반 있음 · 2 엔진 오류
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from autodocs.features import adopt, audit, init, profile as profile_mod, report
from autodocs.foundation import AutodocsError
from autodocs.platform import standard


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = standard.load_manifest(standard.locate(args.standard))
        return args.func(args, manifest)
    except AutodocsError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="autodocs", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", type=Path, default=Path.cwd(), help="프로젝트 루트 (기본: cwd)")
    p.add_argument("--standard", type=Path, default=None, help="standard/ 디렉터리 (기본: 자동 탐색)")
    sub = p.add_subparsers(dest="cmd", required=True)

    for name, strict in (("audit", False), ("check", True)):
        s = sub.add_parser(name)
        s.add_argument("--json", action="store_true")
        s.set_defaults(func=_cmd_audit, strict=strict)

    for name, fn in (("init", _cmd_init), ("adopt", _cmd_adopt)):
        s = sub.add_parser(name)
        s.add_argument("--name", required=True)
        s.add_argument("--kind", required=True)
        s.add_argument("--language", required=True)
        s.add_argument("--api", action="store_true", dest="has_api")
        s.add_argument("--db", action="store_true", dest="has_database")
        s.add_argument("--preset", default="generic", dest="layout_preset")
        s.add_argument("--no-adapters", action="store_true", help="CLAUDE.md 등 포인터 파일을 만들지 않음")
        s.set_defaults(func=fn)
    return p


def _cmd_audit(args, manifest: dict) -> int:
    rep = audit.run(manifest, args.root)
    print(report.json_str(rep) if args.json else report.text(rep))
    return 1 if (args.strict and not rep.ok) else 0


def _profile(args, manifest: dict):
    return profile_mod.from_dict(manifest, {
        "name": args.name, "kind": args.kind, "language": args.language,
        "has_api": args.has_api, "has_database": args.has_database,
        "layout_preset": args.layout_preset, "standard_version": manifest["standard"]["version"],
    })


def _cmd_init(args, manifest: dict) -> int:
    res = init.run(manifest, args.root, _profile(args, manifest), with_adapters=not args.no_adapters)
    _print_init(res)
    return 0


def _cmd_adopt(args, manifest: dict) -> int:
    res, plan = adopt.run(manifest, args.root, _profile(args, manifest))
    _print_init(res)
    print(f"\n다음: {plan} 의 미분류 파일 표를 채운 뒤 이동을 실행하고 `autodocs check` 를 돌리세요.")
    return 0


def _print_init(res: init.InitResult) -> None:
    for p in res.created:
        print(f"+ {p}")
    for p in res.skipped:
        print(f"= {p} (이미 있음, 유지)")
    print(f"\n{len(res.created)} created, {len(res.skipped)} kept")


if __name__ == "__main__":
    sys.exit(main())
