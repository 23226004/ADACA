#!/bin/sh
# autodocs 설치 (macOS / Linux / Windows Git Bash)
#   curl -fsSL https://raw.githubusercontent.com/23226004/ADACA/main/install.sh | sh
#   sh install.sh --dev /path/to/checkout   # 로컬 체크아웃을 marketplace 로 (개발용)
set -e
REPO="23226004/ADACA"; MARKET="adaca"; PLUGIN="autodocs"
say() { printf '%s\n' "$*"; }
fail() { say "error: $*" >&2; exit 1; }

# 1. 전제 조건
command -v claude >/dev/null 2>&1 || fail "claude CLI 가 없습니다. https://code.claude.com/docs/en/setup"
PY=""
if command -v python3 >/dev/null 2>&1 && python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then PY=python3
elif command -v python >/dev/null 2>&1 && python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then PY=python
fi
[ -n "$PY" ] || fail "Python 3.10+ 가 PATH 에 없습니다."
$PY -c "import yaml" 2>/dev/null || { say "PyYAML 설치 중…"; $PY -m pip install --quiet pyyaml || fail "pip install pyyaml 실패"; }

# 2. marketplace + plugin
if [ "$1" = "--dev" ]; then
  [ -d "$2" ] || fail "--dev <체크아웃 경로> 가 필요합니다"
  claude plugin marketplace add "$2"
else
  claude plugin marketplace add "$REPO" 2>/dev/null || claude plugin marketplace update "$MARKET"
fi
claude plugin install "$PLUGIN@$MARKET"

say ""
say "설치 완료. 아무 프로젝트에서 claude 를 열면 [autodocs] state: … 가 보입니다."
say "명령: /std-init  /std-adopt  /std-audit  /std-check   (검증: claude plugin list)"
