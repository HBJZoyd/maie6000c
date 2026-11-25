[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SshHost,
    [Parameter(Mandatory=$true)][ValidateRange(1,65535)][int]$Port,
    [string]$User = 'root',
    [string]$RagDir = '/root/autodl-tmp/RAG',
    [string]$RemotePython = 'python',
    [ValidateRange(1,65535)][int]$LocalPort = 6001,
    [ValidateRange(1,65535)][int]$RemotePort = 6001
)

$ErrorActionPreference = 'Stop'
# Keep user-controlled shell fragments out of the remote command.
foreach ($value in @($SshHost, $User)) {
    if ($value -notmatch '^[a-zA-Z0-9_.-]+$') { throw 'Invalid SSH host or user.' }
}
foreach ($value in @($RagDir, $RemotePython)) {
    if ($value -notmatch '^[/a-zA-Z0-9_.-]+$') { throw 'Use an absolute path without spaces.' }
}
$gatewayFiles = @('rag_gateway.py','rag_evidence.py','rag_assets.py','rag_store.py','start_rag.py') |
    ForEach-Object { Join-Path $PSScriptRoot $_ }
foreach ($gatewayFile in $gatewayFiles) {
    if (-not (Test-Path -LiteralPath $gatewayFile)) { throw "Missing gateway: $gatewayFile" }
}
$target = '{0}@{1}' -f $User, $SshHost
$destination = '{0}:{1}/' -f $target, $RagDir
Write-Host 'Uploading the manual Q&A HTTP adapter. Enter the SSH password when prompted.'
& scp -P $Port @gatewayFiles $destination
if ($LASTEXITCODE -ne 0) { throw 'Upload failed. Check SSH login and the remote RAG directory.' }

$forward = '127.0.0.1:{0}:127.0.0.1:{1}' -f $LocalPort, $RemotePort
$remoteCommand = "cd '$RagDir' && exec '$RemotePython' start_rag.py --root '$RagDir' --port $RemotePort"
Write-Host "Starting the existing RAG pipeline; local tunnel port: $LocalPort."
Write-Host 'Keep this terminal open. Ctrl+C stops the gateway and tunnel.'
Write-Host 'Keep the existing LLM and MongoDB running. The vector index uses Milvus Lite.'
& ssh -t -p $Port -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L $forward $target $remoteCommand
if ($LASTEXITCODE -ne 0) { throw 'Remote gateway stopped. Review the error above.' }
