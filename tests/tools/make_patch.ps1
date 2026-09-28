# Выгружает изменения прод-кода с последнего снимка во временном git-индексе в docs/patches/<name>.diff
# и делает новый снимок. Настоящий индекс и история git не трогаются (коммитов нет).
#   powershell -File tests\tools\make_patch.ps1 -Name 01-session-state-machine -Index <путь к временному индексу>
param([Parameter(Mandatory=$true)][string]$Name, [Parameter(Mandatory=$true)][string]$Index)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$env:GIT_INDEX_FILE = $Index
$paths = @("app", "frontend", "scripts", "requirements.txt", "requirements.lock", ".env.example", "start.bat", "README.md", "data")
$existing = $paths | Where-Object { Test-Path $_ }
git add -N -- $existing 2>$null
$out = "docs/patches/$Name.diff"
git -c core.quotepath=off diff --no-color -- $existing | Out-File -Encoding utf8 $out
git add -A -- $existing
$stat = git -c core.quotepath=off diff --no-color --stat HEAD -- $existing | Select-Object -Last 1
Write-Output "$out : $((Get-Item $out).Length) байт; всего с HEAD: $stat"
