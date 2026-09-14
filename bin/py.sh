#!/bin/sh
# 플랫폼별 Python 실행기 선택. macOS/Linux 는 python3, Windows(Git Bash) 는 보통 python 만 있다.
# 사용: sh "${CLAUDE_PLUGIN_ROOT}/bin/py.sh" <script> [args...]
if command -v python3 >/dev/null 2>&1 && python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
  exec python3 "$@"
elif command -v python >/dev/null 2>&1; then
  exec python "$@"
else
  echo "[autodocs] python 3.10+ 를 찾을 수 없습니다" >&2
  exit 0   # 훅은 fail-open
fi
