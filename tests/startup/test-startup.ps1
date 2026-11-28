# Isolated launcher contract tests. Docker/HTTP are explicit test doubles here,
# never model-execution evidence. Real clean-start evidence is collected separately.
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$temp = Join-Path ([IO.Path]::GetTempPath()) ('odie-startup-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path (Join-Path $temp 'scripts') | Out-Null
Copy-Item -LiteralPath (Join-Path $root 'scripts/start.ps1') -Destination (Join-Path $temp 'scripts/start.ps1')
Copy-Item -LiteralPath (Join-Path $root '.env.example') -Destination (Join-Path $temp '.env.example')
$probe = @'
param([string]$Launcher,[string]$State,[int]$ExpectedPort=18000,[switch]$ConfigOnly)
$ErrorActionPreference='Stop'
function global:docker { $global:LASTEXITCODE=0; if ($args -contains 'info') { 'EXPLICIT TEST DOUBLE: Docker' } }
function global:Invoke-RestMethod {
    param($Uri,$TimeoutSec)
    if ($Uri -ne "http://127.0.0.1:$ExpectedPort/system/status") { throw "Wrong readiness URL: $Uri" }
    [pscustomobject]@{api='ready';database='ready';rag=$(if($State -eq 'unavailable'){'unavailable'}else{'ready'});mode=$(if($State -eq 'fixture'){'fixture'}else{'live'})}
}
try {
    & $Launcher -Mode Remote -ApiPort $ExpectedPort -CheckOnly:$ConfigOnly
    if ($env:API_HOST_PORT -ne [string]$ExpectedPort) { throw 'Explicit port was not passed to Compose.' }
    exit 0
} catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }
'@
$probePath = Join-Path $temp 'probe.ps1'
[IO.File]::WriteAllText($probePath,$probe)
$engine = (Get-Process -Id $PID).Path
$cases = @(
    @{State='unavailable';Expected=1;Config=$false},
    @{State='fixture';Expected=1;Config=$false},
    @{State='live';Expected=0;Config=$false},
    @{State='unavailable';Expected=0;Config=$true}
)
foreach ($case in $cases) {
    $extra = @()
    if ($case.Config) { $extra += '-ConfigOnly' }
    # Windows PowerShell wraps expected child stderr as NativeCommandError.
    $ErrorActionPreference = 'Continue'
    $output = & $engine -NoProfile -File $probePath -Launcher (Join-Path $temp 'scripts/start.ps1') -State $case.State @extra 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($code -ne $case.Expected) { throw "Startup contract failed: $($case.State) config=$($case.Config), exit=$code; $output" }
    Write-Host "PASS: state=$($case.State) configuration_only=$($case.Config) exit=$code"
}
Write-Host '4 isolated startup contracts passed. No GPU inference was performed by these tests.'
