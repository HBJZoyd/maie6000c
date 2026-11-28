[CmdletBinding()]
param(
    [ValidateSet('Offline','Remote','Demo')][string]$Mode = 'Remote',
    [ValidatePattern('^[a-z0-9][a-z0-9_-]+$')][string]$ProjectName = 'odie-offline',
    [ValidateRange(1,65535)][int]$ApiPort = 8000,
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
        if (-not $PSBoundParameters.ContainsKey('ApiPort')) { $ApiPort = 8020 }
        $composeFile = 'compose.offline.yaml'
        $env:OFFLINE_API_PORT = [string]$ApiPort
    } elseif ($Mode -eq 'Demo') {
        $composeFile = 'compose.demo.yaml'
        if ($ProjectName -eq 'odie-offline') { $ProjectName = 'odie-demo' }
        if (-not $PSBoundParameters.ContainsKey('ApiPort')) { $ApiPort = 8030 }
        $env:DEMO_API_PORT = [string]$ApiPort
    } else {
        $composeFile = 'compose.yaml'
        if ($ProjectName -eq 'odie-offline') { $ProjectName = 'maie6000c' }
        # Explicit parameters override configuration; otherwise preserve the user's port.
        if ($PSBoundParameters.ContainsKey('ApiPort')) {
            $env:API_HOST_PORT = [string]$ApiPort
        } elseif ($env:API_HOST_PORT) {
            $ApiPort = [int]$env:API_HOST_PORT
        } else {
            $portLine = Get-Content -LiteralPath '.env' | Where-Object { $_ -match '^API_HOST_PORT=([0-9]+)$' } | Select-Object -Last 1
            if ($portLine) { $ApiPort = [int]($portLine -split '=',2)[1] }
        }
        if ($ApiPort -lt 1 -or $ApiPort -gt 65535) { throw 'Invalid API_HOST_PORT.' }
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
    if ($Mode -in @('Offline','Demo')) {
        $status = Invoke-RestMethod "http://127.0.0.1:$ApiPort/system/status"
        if ($status.mode -ne 'fixture') { throw 'Expected explicitly labelled fixture backend.' }
        if ($Mode -eq 'Demo') {
            if ($status.demo_kind -ne 'recorded-replay') { throw 'Expected recorded demo adapter.' }
            Write-Host "RECORDED PRESENTATION DEMO: http://localhost:$ApiPort/app"
            Write-Host 'Select the Sentry Mode scenario. The answer replays a dated recording.'
        } else {
            Write-Host "OFFLINE ENGINEERING FIXTURE: http://localhost:$ApiPort/app"
            Write-Host 'Answers are synthetic. This does not validate real AI or vehicle instructions.'
        }
    } else {
        $status = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/system/status" -TimeoutSec 15
        if ($status.api -ne 'ready' -or $status.database -ne 'ready' -or $status.rag -ne 'ready' -or $status.mode -ne 'live') {
            throw 'Containers started, but real AI readiness failed. Restore the GPU backend and SSH tunnel, then rerun. No fixture/replay fallback was enabled; database volumes are preserved.'
        }
        Write-Host "REAL MODEL READY: http://localhost:$ApiPort/app"
    }
} finally { Pop-Location }
