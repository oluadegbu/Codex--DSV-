# One foreground command — route 2, manual launch required

Open **normal, non-elevated Windows PowerShell in the existing approved research
account's interactive session**. Do not use Administrator Desktop Commander, Run as
Administrator, runas, an execution-policy bypass, a task or a service. If local
policy blocks the script or Add-Type, stop; do not change policy.

Paste this **one complete block**. It prompts once for the exact source directory
and existing local account named in the directive; neither is a password. No broad
path search, credential enrollment, installation or permission change occurs.
The launcher and audit are hash-pinned. The branch URL is not trusted without the
matching hash. No dataset processing starts before launcher preflight.

```powershell
& {
    $ErrorActionPreference='Stop'
    $src=Read-Host 'Exact historical-data directory from the directive'
    $user=Read-Host 'Existing approved local research account from the directive'
    $who=[Security.Principal.WindowsIdentity]::GetCurrent()
    $principal=New-Object Security.Principal.WindowsPrincipal($who)
    $expected=Get-LocalUser -Name $user -ErrorAction Stop
    if ($expected.SID.Value -ne $who.User.Value -or -not $expected.Enabled -or $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) -or (@($who.Groups | ForEach-Object {$_.Value}) -contains 'S-1-5-32-544')) { throw 'BLOCKED: use the existing standard-user session.' }
    $inputItem=Get-Item -LiteralPath $src -Force
    if (-not $inputItem.PSIsContainer) { throw 'BLOCKED: source unavailable.' }
    $docs=[Environment]::GetFolderPath('MyDocuments')
    if (-not $docs) { throw 'BLOCKED: user Documents unavailable.' }
    $volume=New-Object IO.DriveInfo([IO.Path]::GetPathRoot($docs))
    if ($volume.DriveType -ne [IO.DriveType]::Fixed) { throw 'BLOCKED: output must be on local fixed storage.' }
    $d=Get-Item -LiteralPath $docs -Force
    while ($null -ne $d) { if (($d.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'BLOCKED: redirected/reparse output.' }; $d=$d.Parent }
    $dir=Join-Path $docs ('DATMT5Bootstrap_'+[Guid]::NewGuid().ToString('N'))
    $d=$inputItem
    while ($null -ne $d -and $null -ne $d.Parent) { if ($dir.StartsWith($d.FullName.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'BLOCKED: output overlaps the source/production tree.' }; $d=$d.Parent }
    New-Item -ItemType Directory -Path $dir | Out-Null
    $file=Join-Path $dir 'Launch-ResearchAudit.ps1'
    $uri='https://raw.githubusercontent.com/oluadegbu/Codex--DSV-/research/dat-mt5-edge-phase1/research/dat_mt5_edge/phase6_6s/Launch-ResearchAudit.ps1'
    $r=[Net.HttpWebRequest]::Create($uri); $r.Timeout=30000; $r.ReadWriteTimeout=10000; $r.AllowAutoRedirect=$false
    $response=$r.GetResponse(); $stream=$response.GetResponseStream(); $sink=[IO.File]::Open($file,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try { $buf=New-Object byte[] 4096; $total=0; while (($n=$stream.Read($buf,0,$buf.Length)) -gt 0) { $total+=$n; if ($total -gt 65536) { throw 'BLOCKED: launcher download size limit.' }; $sink.Write($buf,0,$n) } } finally { $sink.Dispose(); $stream.Dispose(); $response.Dispose() }
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ine 'f9b899a925563e2f0cbe1f78cf74324a12d4f4a1bbdb63b4031c38677f739362') { throw 'BLOCKED: launcher hash mismatch.' }
    & $file -InputRoot $inputItem.FullName -ExpectedAccount $user
}
```

Keep the foreground window open. No remote connection is needed once the two
public code downloads finish. No data is uploaded automatically.

## What it does and where it stops

- Checks local account SID/enabled state, token administrator membership and Windows
  integrity. Rejects filtered administrators too. Uses current identity only.
- Screens every source node's ACL and ancestor replacement rights, with no source
  write probe or permission change. This is conservative: matching write allows or
  ownership block even if a more complex deny might make access effectively read-only.
  Do not weaken the check; report the specific blocker.
- Requires existing Python 3.10+, standard library and the unchanged audit script's
  exact SHA256. Existing package source constant must match the supplied input.
- Creates an ephemeral Windows Job Object before resuming the Python process:
  one process, 512 MiB committed-memory limits, kill-on-controller-exit and foreground
  wall-time monitoring. Dependency probe: 10 seconds; census: 600 seconds; quality
  mode if separately supplied a reviewed schema: 60 seconds. This is not a service.
- Checks tree size/path bounds (20,000 nodes, 512 characters), rejects reparse
  paths, requires 256 MiB free and monitors run output against a 128 MiB stop
  threshold. The output threshold is sampled, **not an NTFS quota**; brief overshoot
  is possible. Stable, bounded input is required. No disk quota is installed.
- Writes only a new per-run folder under the current user's research Documents
  directory. Private identity/path details stay local. Existing results are not
  overwritten. Failure before folder creation appears in the console; later failures
  also produce `launch-result.json`. Partial output never means completion.

The default command runs the existing **census** only. No reviewed source schema
or timezone is available yet. Expected honest success state is therefore
`INVENTORY_COMPLETE_QUALITY_BLOCKED_REVIEWED_SCHEMA`, not a dataset PASS. If a
reviewed explicit schema already exists outside the transferred data, the launcher
supports `-ReviewedSchema <path>`; do not enable the disabled example or guess
UTC/columns. No terminal, strategy, optimization or sealed-holdout analysis occurs.

Return the local `launch-result.json` and successful `inventory_summary.json`, plus
the private inventory through an authorized private channel if needed for review.
Do **not** publish raw input data, private paths, SIDs, account identifiers or license
receipts to the public PR. Without a valid schema and license/calendar/contract
review, actual historical coverage and research suitability remain unverified.

**Validation limitation:** this launcher has been statically reviewed against the
Windows API documentation but has not been run on Windows here; no PowerShell/.NET
runtime is available in this environment. Any compile, containment or preflight
failure is a stop condition, not permission to fall back to elevated execution.
