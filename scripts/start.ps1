[CmdletBinding()]
param(
    [ValidateSet('Offline','Remote')][string]$Mode = 'Offline',
    [ValidatePattern('^[a-z0-9][a-z0-9_-]+$')][string]$ProjectName = 'odie-offline',
    [ValidateRange(1,65535)][int]$ApiPort = 8020,
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Push-Location -LiteralPath $projectRoot
try {
    & docker --context default info --format '{{.ServerVersion}}'
    if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop and wait for its engine, then retry.' }
    if (-not (Test-Path -LiteralPath '.env')) {
        Copy-Item -LiteralPath '.env.example' -Destination '.env'
    }
    if ($Mode -eq 'Offline') {
        $composeFile = 'compose.offline.yaml'
        $env:OFFLINE_API_PORT = [string]$ApiPort
    } else {
        $composeFile = 'compose.yaml'
        if ($ProjectName -eq 'odie-offline') { $ProjectName = 'maie6000c' }
        # Real mode preserves the host ports in the user's existing configuration.
        Write-Host 'Remote mode requires the real GPU backend and an active tunnel.'
    }
    & docker --context default compose -p $ProjectName -f $composeFile config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Compose configuration is invalid.' }
    if ($CheckOnly) { Write-Host 'Local prerequisites and Compose configuration checked.'; return }
    if ($Mode -eq 'Remote') {
        # Drain old code before an additive migration; never mix unfenced W07 workers with v2.
        & docker --context default compose -p $ProjectName -f $composeFile stop worker
        if ($LASTEXITCODE -ne 0) { throw 'Could not stop old workers safely before upgrade.' }
    }
    & docker --context default compose -p $ProjectName -f $composeFile up -d --build --wait --wait-timeout 180
    if ($LASTEXITCODE -ne 0) { throw 'Startup failed. Inspect compose ps and logs; no volumes were deleted.' }
    if ($Mode -eq 'Offline') {
        $status = Invoke-RestMethod "http://127.0.0.1:$ApiPort/system/status"
        if ($status.mode -ne 'fixture') { throw 'Expected explicitly labelled fixture backend.' }
        Write-Host "OFFLINE ENGINEERING FIXTURE: http://localhost:$ApiPort/app"
        Write-Host 'Answers are synthetic. This does not validate real AI or vehicle instructions.'
    } else {
        Write-Host 'Application started. Check /system/status before submitting a real question.'
    }
} finally { Pop-Location }
