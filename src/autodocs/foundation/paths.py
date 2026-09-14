"""L0 — 경로 정책. 엔진 안의 모든 상대 경로는 norm_rel 을, 실제 파일 접근은 safe_path 를 거친다.

정책 (읽기·쓰기 동일):
  - 절대 경로, '..', null byte 는 입력 단계에서 거부 (norm_rel)
  - 심볼릭 링크는 허용하되, 링크를 따라간 최종 위치가 root 밖이면 거부 (safe_path)
    → `CLAUDE.md -> AGENTS.md` 같은 root 내부 링크는 정상, `README.md -> /etc/hostname` 은 PathEscape
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath

from .errors import PathEscape


def norm_rel(rel: str) -> str:
    """루트 기준 상대 경로의 유일한 정규형: '/' 구분, 앞뒤 '/' 및 '.' 세그먼트 제거."""
    if not isinstance(rel, str) or "\x00" in rel:
        raise PathEscape(f"잘못된 경로: {rel!r}")
    s = rel.replace("\\", "/")
    if s.startswith("/") or (len(s) > 1 and s[1] == ":"):
        raise PathEscape(f"절대 경로는 허용하지 않음: {rel}")
    parts = [p for p in s.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise PathEscape(f"'..' 는 허용하지 않음: {rel}")
    return "/".join(parts)


def safe_path(root: Path, rel: str) -> Path:
    """root/rel 의 절대 경로. 링크를 모두 따라간 결과(resolve)가 root 안이 아니면 PathEscape.

    반환값은 resolve 하지 않은 경로(root / rel)다 — 링크 자체를 가리켜야 exists()/is_symlink() 판단이 가능하다.
    """
    root = root.resolve()
    key = norm_rel(rel)
    if not key:
        return root
    target = root / PurePosixPath(key)
    try:
        real = target.resolve()   # dangling 링크도 strict=False 로 최종 목적지를 계산
    except (RuntimeError, OSError) as e:   # 심링크 루프 등
        raise PathEscape(f"경로를 해석할 수 없음: {rel} ({e})") from e
    if real != root and root not in real.parents:
        raise PathEscape(f"root 밖을 가리킴: {rel} -> {real}")
    return target
