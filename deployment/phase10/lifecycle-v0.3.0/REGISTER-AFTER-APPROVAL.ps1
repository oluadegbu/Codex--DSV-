# FINAL EXPLICIT REQUEST-0009 AUTHORIZATION ONLY. Does not elevate its caller.
# Microsoft restricts boot-trigger CREATION to an existing Administrator.
# Worker execution remains DirectiveCodex/LeastPrivilege; never launch it directly here.
param(
 [Parameter(Mandatory=$true)][string]$ApprovedPreflightPath,
 [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{64}$')][string]$ApprovedPreflightSHA256
)
$ErrorActionPreference = 'Stop'
$current = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($current)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) -or [Environment]::MachineName -ine 'WIN-HQAAFGGU1AM') { throw 'Final-approved registration requires the existing security owner; never elevate DirectiveCodex' }
$base = 'C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-OPS-0.3.0\package'
$app = Join-Path $base 'app'
$private = 'C:\Users\DirectiveCodex\AppData\Local\Directive\DMBWindowsWorker-ops-0.3.0'
$path = [IO.Path]::GetFullPath($ApprovedPreflightPath)
if ([IO.Path]::GetDirectoryName($path) -ine $private -or [IO.Path]::GetFileName($path) -notmatch '^PREDEPLOY-[0-9a-f]{64}\.json$') { throw 'Exact approved private predeployment receipt required' }
function Digest([byte[]]$bytes) {
 $algorithm = [Security.Cryptography.SHA256]::Create()
 try { return ([BitConverter]::ToString($algorithm.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() } finally { $algorithm.Dispose() }
}
# Parse the SAME bytes that were hashed; do not reread unchecked XML/configuration.
$receiptBytes = [IO.File]::ReadAllBytes($path)
if ((Digest $receiptBytes) -cne $ApprovedPreflightSHA256) { throw 'Human-approved preflight digest mismatch' }
$review = [Text.Encoding]::UTF8.GetString($receiptBytes) | ConvertFrom-Json
$now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
if ($review.schema_version -ne 1 -or $review.mode -cne 'SHADOW' -or $review.preflight -cne 'PASS' -or $review.remote_HMAC_TLS_HELLO -cne 'PASS' -or $review.host -ine 'WIN-HQAAFGGU1AM' -or $review.user_sid -cne 'S-1-5-21-3675741470-1525898003-3877381073-1000' -or $review.package_version -cne '0.3.0' -or $review.expires_at -le ($now+300)) { throw 'Native preflight identity/lease invalid' }
$manifestBytes = [IO.File]::ReadAllBytes((Join-Path $base 'PACKAGE_MANIFEST.json'))
if ((Digest $manifestBytes) -cne $review.manifest_sha256) { throw 'Approved manifest drift' }
$manifest = [Text.Encoding]::UTF8.GetString($manifestBytes) | ConvertFrom-Json
if ($manifest.source_commit -cne $review.source_commit -or $manifest.package_version -cne '0.3.0') { throw 'Approved source/version mismatch' }
foreach ($entry in $manifest.files.PSObject.Properties) {
 if ($entry.Name -match '(^/|\\|:|(^|/)\.\.(/|$))') { throw 'Package path violation' }
 $file = [IO.Path]::GetFullPath((Join-Path $base $entry.Name))
 if (-not $file.StartsWith($base+'\',[StringComparison]::OrdinalIgnoreCase) -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -cne $entry.Value) { throw 'Reviewed package file drift' }
}
if ((Get-FileHash -LiteralPath (Join-Path $private 'activation.dpapi') -Algorithm SHA256).Hash.ToLowerInvariant() -cne $review.activation_ciphertext_sha256 -or (Get-FileHash -LiteralPath (Join-Path $private 'WINDOWS_ACCEPTANCE.json') -Algorithm SHA256).Hash.ToLowerInvariant() -cne $review.Windows_acceptance_sha256) { throw 'Private activation/evidence changed since native preflight' }
$xmlBytes = [IO.File]::ReadAllBytes((Join-Path $app 'deployment\phase10\lifecycle-v0.3.0\Directive.DMB.ShadowWorker.Phase10.xml'))
if ((Digest $xmlBytes) -cne $review.task_xml_sha256) { throw 'Approved task XML drift' }
$taskName = 'Directive.DMB.ShadowWorker.Phase10'
if (Get-ScheduledTask -TaskName $taskName -TaskPath '\' -ErrorAction SilentlyContinue) { throw 'Existing task preserved; no overwrite' }
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class DmbBatchCheck {
 [DllImport("advapi32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
 public static extern bool LogonUser(string user,string domain,string password,int type,int provider,out IntPtr token);
 [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr token);
}
'@
$credential = Get-Credential -UserName 'WIN-HQAAFGGU1AM\DirectiveCodex' -Message 'FINAL APPROVAL ONLY: Windows-protected DMB batch task credential'
if ($credential.UserName -ine 'WIN-HQAAFGGU1AM\DirectiveCodex') { throw 'Exact existing identity required' }
$bstr = [IntPtr]::Zero; $token = [IntPtr]::Zero
try {
 $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($credential.Password)
 $transientPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
 # Verify batch logon ALREADY allowed. Never implicitly grant a missing right.
 if (-not [DmbBatchCheck]::LogonUser('DirectiveCodex','WIN-HQAAFGGU1AM',$transientPassword,4,0,[ref]$token)) {
  $code = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
  throw "Batch logon unavailable ($code); no task registered or right granted"
 }
 [void][DmbBatchCheck]::CloseHandle($token); $token = [IntPtr]::Zero
 $service = New-Object -ComObject Schedule.Service; $service.Connect()
 $definition = $service.NewTask(0); $definition.XmlText = [Text.Encoding]::UTF8.GetString($xmlBytes)
 # TASK_CREATE=2, TASK_LOGON_PASSWORD=1. Pinned XML enforces worker LeastPrivilege.
 [void]$service.GetFolder('\').RegisterTaskDefinition($taskName,$definition,2,$credential.UserName,$transientPassword,1,$null)
} finally {
 if ($token -ne [IntPtr]::Zero) { [void][DmbBatchCheck]::CloseHandle($token) }
 if ($bstr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
 $transientPassword = $null; $credential = $null
}
# Launch ONLY the registered least-privilege task, never a worker as Administrator.
Start-ScheduledTask -TaskName $taskName -TaskPath '\'
