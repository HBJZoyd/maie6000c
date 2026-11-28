[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$CheckoutDirectory,
    [string]$Repository = 'https://github.com/HBJZoyd/maie6000c.git',
    [string]$Revision = 'w13-final',
    [ValidatePattern('^[a-z0-9][a-z0-9_-]+$')][string]$ProjectName = ('odie-clean-' + (Get-Date -Format 'yyyyMMddHHmmss')),
    [ValidateRange(1,65535)][int]$ApiPort = 18000,
    [ValidateRange(1,65535)][int]$AiPort = 18100,
    [ValidateRange(1,65535)][int]$DatabasePort = 15432,
    [string]$Python = 'python',
    [switch]$KeepRunning
)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $CheckoutDirectory) { throw 'CheckoutDirectory must not exist; existing files are never removed.' }
if (@(@($ApiPort,$AiPort,$DatabasePort) | Select-Object -Unique).Count -ne 3) { throw 'Choose three different host ports.' }
foreach ($port in @($ApiPort,$AiPort,$DatabasePort)) {
    $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,$port)
    try { $listener.Start() } catch { throw "Host port $port is occupied; choose another port." } finally { $listener.Stop() }
}
& docker --context default info --format '{{.ServerVersion}}'
if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop is not ready.' }
& git -c http.sslVerify=true clone --no-local -- $Repository $CheckoutDirectory
if ($LASTEXITCODE -ne 0) { throw 'Fresh clone failed.' }
$checkout = (Resolve-Path -LiteralPath $CheckoutDirectory).Path
Push-Location -LiteralPath $checkout
$started = $false
$record = [ordered]@{ started_at_utc=[DateTime]::UtcNow.ToString('o'); project=$ProjectName; repository=$Repository; requested_revision=$Revision }
try {
    & git checkout --detach $Revision
    if ($LASTEXITCODE -ne 0) { throw 'Requested revision was not found.' }
    $record.source_commit = (& git rev-parse HEAD).Trim()
    $record.initial_git_status = [string](& git status --porcelain)
    if ($record.initial_git_status) { throw 'Fresh checkout is not clean.' }
    $record.initial_env_exists = Test-Path -LiteralPath '.env'
    if ($record.initial_env_exists) { throw 'Fresh checkout unexpectedly contains .env.' }
    $existing = & docker --context default compose -p $ProjectName -f compose.yaml ps -a -q
    if ($LASTEXITCODE -ne 0 -or $existing) { throw 'Choose a new, unused Compose project name.' }
    $envText = Get-Content -LiteralPath '.env.example' -Raw
    $envText = $envText -replace '(?m)^API_HOST_PORT=.*$',"API_HOST_PORT=$ApiPort"
    $envText = $envText -replace '(?m)^AI_HOST_PORT=.*$',"AI_HOST_PORT=$AiPort"
    $envText = $envText -replace '(?m)^POSTGRES_HOST_PORT=.*$',"POSTGRES_HOST_PORT=$DatabasePort"
    # Optional existing gateway token stays local; it is never written to evidence.
    if ($env:RAG_API_TOKEN) {
        if ($env:RAG_API_TOKEN -match '[\r\n]') { throw 'Invalid gateway token format.' }
        $envText = [regex]::Replace($envText,'(?m)^RAG_API_TOKEN=.*$',('RAG_API_TOKEN='+$env:RAG_API_TOKEN).Replace('$','$$'))
    }
    [IO.File]::WriteAllText((Join-Path $checkout '.env'),$envText)
    $started = $true
    & .\scripts\start.ps1 -Mode Remote -ProjectName $ProjectName -ApiPort $ApiPort
    $questions = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/questions" -TimeoutSec 15
    $record.initial_question_count = @($questions).Count
    if (@($questions).Count -ne 0) { throw 'The isolated database is not empty; this is not a fresh-state validation.' }
    $record.initial_status = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/system/status" -TimeoutSec 15
    & $Python scripts/collect_final_evidence.py --mode live --base-url "http://127.0.0.1:$ApiPort" --project $ProjectName --compose-file compose.yaml --pause-worker --restart --timeout 900 --output artifacts/clean-start/live
    if ($LASTEXITCODE -ne 0) { throw 'Real end-to-end collector failed; inspect retained evidence and logs.' }
    $record.live_summary = Get-Content -LiteralPath 'artifacts/clean-start/live/summary.json' -Raw | ConvertFrom-Json
    $record.final_status = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/system/status" -TimeoutSec 15
    $record.success = $true
} catch {
    $record.success = $false
    $record.error = $_.Exception.Message
    throw
} finally {
    $record.finished_at_utc = [DateTime]::UtcNow.ToString('o')
    $record.cleanup_requested = -not $KeepRunning
    if ($started -and -not $KeepRunning) {
        & docker --context default compose -p $ProjectName -f compose.yaml down
        $record.cleanup_exit = $LASTEXITCODE
    }
    New-Item -ItemType Directory -Path 'artifacts/clean-start' -Force | Out-Null
    $record | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath 'artifacts/clean-start/reproduction.json' -Encoding UTF8
    Write-Host "Reproduction evidence: $checkout\artifacts\clean-start\reproduction.json"
    Pop-Location
}
