# autodocs 설치 (Windows PowerShell)
#   irm https://raw.githubusercontent.com/23226004/ADACA/main/install.ps1 | iex
#   .\install.ps1 -Dev C:\path\to\checkout   # 로컬 체크아웃을 marketplace 로 (개발용)
param([string]$Dev = "")
$ErrorActionPreference = "Stop"
$Repo = "23226004/ADACA"; $Market = "adaca"; $Plugin = "autodocs"

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) { throw "claude CLI 가 없습니다. https://code.claude.com/docs/en/setup" }
if (-not (Get-Command sh -ErrorAction SilentlyContinue)) { throw "sh 가 없습니다. Claude Code 는 Windows 에서 Git Bash 가 필요합니다." }
$py = $null
foreach ($c in @("python3", "python")) {
  if (Get-Command $c -ErrorAction SilentlyContinue) {
    & $c -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) { $py = $c; break }
  }
}
if (-not $py) { throw "Python 3.10+ 가 PATH 에 없습니다." }
& $py -c "import yaml" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "PyYAML 설치 중…"; & $py -m pip install --quiet pyyaml }

if ($Dev) { claude plugin marketplace add $Dev } else { claude plugin marketplace add $Repo 2>$null; if ($LASTEXITCODE -ne 0) { claude plugin marketplace update $Market } }
claude plugin install "$Plugin@$Market"

Write-Host ""
Write-Host "설치 완료. 아무 프로젝트에서 claude 를 열면 [autodocs] state: … 가 보입니다."
Write-Host "명령: /std-init  /std-adopt  /std-audit  /std-check   (검증: claude plugin list)"
