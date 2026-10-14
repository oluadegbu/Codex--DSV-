$ErrorActionPreference = 'Stop'
$DmbIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$DmbPrincipal = New-Object Security.Principal.WindowsPrincipal($DmbIdentity)
if ($DmbIdentity.Name -ine "$env:COMPUTERNAME\DirectiveCodex" -or $DmbPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use normal PowerShell in the existing non-admin DirectiveCodex RDP session.'
}
$DmbUrl = 'https://github.com/oluadegbu/Codex--DSV-/releases/download/dmb-windows-v0.1.2-d3ce1b9cc73e/DMB-Windows-0.1.2-d3ce1b9cc73e-amd64.zip'
$DmbSha = '4ebd023dbfd6c935fccca64bbe6ae3004b1b17052b693c90d9078f9d5f0d640e'
$DmbRoot = Join-Path $env:LOCALAPPDATA 'Directive\DMB-0.1.2-d3ce1b9cc73e'
if (Test-Path $DmbRoot) { throw 'Existing state preserved. Do not overwrite, delete or silently re-pair.' }
for ($DmbPath = [IO.DirectoryInfo]$DmbRoot; $null -ne $DmbPath; $DmbPath = $DmbPath.Parent) {
    if ($DmbPath.Exists -and ($DmbPath.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Junction/reparse deployment boundary rejected.' }
}
New-Item -ItemType Directory -Path $DmbRoot | Out-Null
$DmbZip = Join-Path $DmbRoot 'package.zip'
Invoke-WebRequest -UseBasicParsing -Uri $DmbUrl -OutFile $DmbZip
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $DmbZip).Hash -ine $DmbSha) { throw 'Package SHA-256 mismatch; nothing executed.' }
$DmbPackage = Join-Path $DmbRoot 'package'
Expand-Archive -LiteralPath $DmbZip -DestinationPath $DmbPackage
& (Join-Path $DmbPackage 'runtime\python\python.exe') -I (Join-Path $DmbPackage 'app\tools\run_windows_shadow_bridge.py')
if ($LASTEXITCODE -ne 0) { throw "Stopped safely. Preserve $DmbPackage\app\artifacts\windows-foreground; no blind rerun." }
Get-Content -LiteralPath (Join-Path $DmbPackage 'app\artifacts\windows-foreground\CERTIFICATION.json')
