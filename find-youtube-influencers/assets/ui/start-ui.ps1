param(
  [int]$Port = 43119,
  [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$uiRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:CODEX_UI_PORT = [string]$Port
$healthUrl = "http://127.0.0.1:$Port/api/health"
$uiUrl = "http://127.0.0.1:$Port/"

try {
  $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
  Write-Host "이미 실행 중입니다: $($health.codex_version)"
  if (-not $NoBrowser) { Start-Process $uiUrl }
  exit 0
} catch {
  # 서버가 아직 없으면 아래에서 시작한다.
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  throw 'Node.js를 찾지 못했습니다. Node.js를 설치한 뒤 다시 실행해 주세요.'
}
if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
  throw 'Codex CLI를 찾지 못했습니다. Codex CLI를 설치하고 로그인한 뒤 다시 실행해 주세요.'
}

if (-not $NoBrowser) {
  Start-Job -ScriptBlock {
    param($url)
    for ($i = 0; $i -lt 40; $i++) {
      try {
        Invoke-WebRequest -Uri ($url + 'api/health') -UseBasicParsing -TimeoutSec 1 | Out-Null
        Start-Process $url
        return
      } catch {
        Start-Sleep -Milliseconds 250
      }
    }
  } -ArgumentList $uiUrl | Out-Null
}

Write-Host "유튜브 인플루언서 파인더를 시작합니다: $uiUrl"
Write-Host '이 창을 닫으면 로컬 실행 서버가 종료됩니다.'
node (Join-Path $uiRoot 'server.js')
