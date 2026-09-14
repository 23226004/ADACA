"""autodocs CLI — 얇은 디스패처. 판단 로직은 features 에만 있다.

  autodocs audit  [--json]                     준수 상태 판정 (new/legacy/partial/compliant)
  autodocs check  [--json] [--override 사유]    audit 와 같으나 error 가 있으면 exit 1 (PR 게이트용)
                                               --override 는 .standard/overrides.log 에 기록되며 AUTODOCS_STRICT=1 이면 금지
  autodocs init   --name X --kind web --language python [--api] [--db] [--preset generic] [--no-adapters]
  autodocs adopt  (init 과 동일 인자)            기존 프로젝트: 마커·문서 생성 + 계층 배치 계획서

exit code: 0 통과 · 1 위반 있음 · 2 엔진/사용 오류 (잘못된 입력, 표준 없음, 예외)
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from autodocs.features import adopt, audit, init, profile as profile_mod, report
from autodocs.foundation import AutodocsError, safe_path
from autodocs.platform import fs, standard


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):   # cp949 등 비UTF-8 콘솔에서 아이콘 때문에 죽지 않게
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    try:
        args = _parser().parse_args(argv)
        manifest = standard.load_manifest(standard.locate(args.standard))
        return args.func(args, manifest)
    except AutodocsError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except SystemExit as e:                    # argparse 오류 → 2 (사용 오류)
        return 2 if e.code else 0
    except Exception as e:  # noqa: BLE001 — 어떤 예외도 "위반 있음(1)" 과 섞이면 안 된다
        print(f"internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="autodocs", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", type=Path, default=Path.cwd(), help="프로젝트 루트 (기본: cwd)")
    p.add_argument("--standard", type=Path, default=None, help="standard/ 디렉터리 (기본: 자동 탐색)")
    sub = p.add_subparsers(dest="cmd", required=True)

    for name, strict in (("audit", False), ("check", True)):
        s = sub.add_parser(name)
        s.add_argument("--json", action="store_true")
        if strict:
            s.add_argument("--override", metavar="REASON", default=None,
                           help="위반이 있어도 exit 0. 사유가 출력에 남는다 (긴급 탈출구)")
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
    rep = audit.run(manifest, fs.require_dir(args.root, "--root"))
    override = getattr(args, "override", None)
    print(report.json_str(rep, override=override) if args.json else report.text(rep, override=override))
    if not args.strict or rep.ok:
        return 0
    if override:
        if os.environ.get("AUTODOCS_STRICT", "").lower() in ("1", "true", "yes"):
            print(f"error: AUTODOCS_STRICT 환경에서는 --override 를 쓸 수 없습니다 (위반 {len(rep.errors)}건)", file=sys.stderr)
            return 1
        _log_override(args.root, override, rep)
        print(f"OVERRIDE: 위반 {len(rep.errors)}건을 사유 '{override}' 로 통과시킴 (.standard/overrides.log 에 기록)", file=sys.stderr)
        return 0
    return 1


def _log_override(root: Path, reason: str, rep) -> None:
    """탈출구 사용 흔적. 저장소에 남아 리뷰·감사에서 보인다."""
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} | {reason} | " \
           f"{'; '.join(f'[{f.check_id}] {f.message}' for f in rep.errors)}\n"
    path = safe_path(root, ".standard/overrides.log")
    if path.is_symlink():
        raise AutodocsError("overrides.log 가 심볼릭 링크입니다 — 감사 로그는 일반 파일이어야 합니다")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)


def _profile(args, manifest: dict):
    return profile_mod.from_dict(manifest, {
        "name": args.name, "kind": args.kind, "language": args.language,
        "has_api": args.has_api, "has_database": args.has_database,
        "layout_preset": args.layout_preset, "standard_version": manifest["standard"]["version"],
    })


def _cmd_init(args, manifest: dict) -> int:
    res = init.run(manifest, fs.require_dir(args.root, "--root"), _profile(args, manifest), with_adapters=not args.no_adapters)
    _print_init(res)
    return 0


def _cmd_adopt(args, manifest: dict) -> int:
    res, plan = adopt.run(manifest, fs.require_dir(args.root, "--root"), _profile(args, manifest), with_adapters=not args.no_adapters)
    _print_init(res)
    print(f"\n다음: {plan} 의 미분류 파일 표를 채운 뒤 이동을 실행하고 `autodocs check` 를 돌리세요.")
    return 0


def _print_init(res: init.InitResult) -> None:
    for p in res.created:
        print(f"+ {p}")
    for p in res.skipped:
        print(f"= {p} (이미 있음, 유지)")
    for w in res.warnings:
        print(f"! {w}")
    print(f"\n{len(res.created)} created, {len(res.skipped)} kept")


if __name__ == "__main__":
    sys.exit(main())
