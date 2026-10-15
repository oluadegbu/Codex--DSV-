# INERT UNTIL RUN AFTER FINAL EXPLICIT REQUEST-0009 AUTHORIZATION.
# No policy/ACL/firewall changes. No plaintext password storage or command-line secret.
$ErrorActionPreference = 'Stop'
$base = 'C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-OPS-0.3.0\package'
$python = Join-Path $base 'runtime\python\python.exe'
$app = Join-Path $base 'app'
$hostScript = Join-Path $app 'tools\run_windows_lifecycle_host.py'
$taskName = 'Directive.DMB.ShadowWorker.Phase10'
# Host policy blocks exit 0 to avoid scheduler retry; require exact positive JSON too.
$preflight = & $python -I $hostScript --preflight | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Native preflight failed' }
if ($preflight.preflight -ne 'PASS') { throw 'Final grant, pairing or native acceptance missing' }
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
$bstr = [IntPtr]::Zero
$token = [IntPtr]::Zero
try {
 $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($credential.Password)
 $transientPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
 # Prove batch logon is ALREADY allowed. No registration-triggered implicit right grant.
 if (-not [DmbBatchCheck]::LogonUser('DirectiveCodex','WIN-HQAAFGGU1AM',$transientPassword,4,0,[ref]$token)) {
  $code = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
  throw "Batch logon unavailable ($code); no task registered or right granted"
 }
 [void][DmbBatchCheck]::CloseHandle($token); $token = [IntPtr]::Zero
 $service = New-Object -ComObject Schedule.Service
 $service.Connect()
 $definition = $service.NewTask(0)
 $definition.XmlText = [IO.File]::ReadAllText((Join-Path $app 'deployment\phase10\lifecycle-v0.3.0\Directive.DMB.ShadowWorker.Phase10.xml'))
 # TASK_CREATE=2 (never update), TASK_LOGON_PASSWORD=1. LeastPrivilege comes from pinned XML.
 [void]$service.GetFolder('\').RegisterTaskDefinition($taskName,$definition,2,$credential.UserName,$transientPassword,1,$null)
} finally {
 if ($token -ne [IntPtr]::Zero) { [void][DmbBatchCheck]::CloseHandle($token) }
 if ($bstr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
 $transientPassword = $null; $credential = $null
}
# Registration is the only persistent change here; explicit initial start uses this exact task.
Start-ScheduledTask -TaskName $taskName -TaskPath '\'
