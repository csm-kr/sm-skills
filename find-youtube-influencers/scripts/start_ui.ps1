[CmdletBinding()]
param(
  [ValidateRange(1024, 65535)]
  [int]$Port = 43119,
  [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$skillRoot = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $skillRoot 'assets\ui\start-ui.ps1'

if (-not (Test-Path -LiteralPath $launcher)) {
  throw "번들 UI 실행 파일을 찾지 못했습니다: $launcher"
}

if (-not $env:CODEX_UI_WORKSPACE) {
  $env:CODEX_UI_WORKSPACE = (Get-Location).Path
}

& $launcher -Port $Port -NoBrowser:$NoBrowser
