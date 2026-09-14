"""훅 공통. 원칙 (bkit 참조 노트 1.3~1.5):

- fail-open: 어떤 예외도 세션을 막지 않는다. 문제가 있으면 아무것도 출력하지 않고 exit 0.
- 엔진은 in-process 로 호출한다 (서브프로세스 없음). 표준은 항상 이 플러그인의 standard/.
- 출력은 상한을 둔다 (Claude Code 훅 출력 10,000자 초과 시 파일로 빠짐).
- 프로젝트 루트는 payload 의 cwd 에서 위로 올라가며 마커 또는 .git 을 찾는다 (worktree 대응).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "src"))

MAX_CHARS = 6000


def read_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:  # noqa: BLE001
        return {}


def find_root(payload: dict) -> Path:
    from autodocs.platform import standard  # noqa: F401  (경로 설정 확인용)
    start = Path(payload.get("cwd") or ".").resolve()
    for d in (start, *start.parents):
        if (d / ".standard" / "project.yaml").is_file() or (d / ".git").exists():
            return d
    return start


def run_audit(root: Path):
    """Report 반환. manifest 는 플러그인 동봉 standard/ 고정."""
    from autodocs.features import audit
    from autodocs.platform import standard
    manifest = standard.load_manifest(standard.locate(PLUGIN_ROOT / "standard"))
    return manifest, audit.run(manifest, root)


def summarize(report, *, limit: int = 8) -> str:
    """상태 + 다음 행동 + error 상위 N 건. 절단 시 표시."""
    lines = [f"[autodocs] state: {report.state.value} — {report.next_action}"]
    errs = report.errors
    if errs:
        lines.append(f"error {len(errs)}건" + (f" (상위 {limit}건만 표시)" if len(errs) > limit else ""))
        for f in errs[:limit]:
            loc = f" ({f.path})" if f.path else ""
            lines.append(f"  x [{f.check_id}] {f.message}{loc}")
    text = "\n".join(lines)
    return text if len(text) <= MAX_CHARS else text[:MAX_CHARS - 20] + "\n  … (절단됨)"


def emit(obj: dict | None = None, text: str | None = None) -> None:
    if text is not None:
        sys.stdout.write(text)
    elif obj is not None:
        sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()


def guarded(fn) -> None:
    """훅 본체를 감싼다. 예외는 stderr 에만 남기고 exit 0."""
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        print(f"[autodocs hook] {type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(0)
