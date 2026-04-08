Param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "[AnderBot] create venv"
& $Python -m venv .venv

$venvPython = Join-Path $PWD ".venv\Scripts\python.exe"
$venvPip = Join-Path $PWD ".venv\Scripts\pip.exe"

Write-Host "[AnderBot] install package"
& $venvPip install --upgrade pip
& $venvPip install -e .

if (-not (Test-Path .env)) {
  Copy-Item .env.example .env
  Write-Host "[AnderBot] created .env from .env.example"
}

Write-Host "[AnderBot] done"
Write-Host "Run: .venv\Scripts\python.exe -m anderbot.main run"
