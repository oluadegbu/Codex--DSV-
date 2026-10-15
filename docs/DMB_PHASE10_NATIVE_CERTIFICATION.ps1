# Foreground certification ONLY: no task/service installation, elevation or policy change.
& {
 $ErrorActionPreference='Stop'
 $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
 if ($identity.Name -ine 'WIN-HQAAFGGU1AM\DirectiveCodex' -or $identity.User.Value -cne 'S-1-5-21-3675741470-1525898003-3877381073-1000' -or ($identity.Groups.Value -contains 'S-1-5-32-544')) { throw 'Existing DirectiveCodex non-admin session required; never elevate' }
 $base=[Environment]::GetFolderPath('LocalApplicationData')
 if ($base -ine 'C:\Users\DirectiveCodex\AppData\Local') { throw 'Reviewed LocalAppData boundary differs' }
 $install=Join-Path $base 'Directive\DMB-OPS-0.3.0'
 if (Test-Path -LiteralPath $install) { throw 'Existing installation retained; no overwrite, re-pair or blind retry' }
 [void][IO.Directory]::CreateDirectory($install)
 $zip=Join-Path $install 'DMB-Windows-0.3.0-a46705985abd-amd64.zip'
 $expected='38b395f3609900d1c5423fc9ed4f02413397db8728c2c27d66ae576308ead5f6'
 if ($expected -cnotmatch '^[0-9a-f]{64}$') { throw 'Exact validated release digest required' }
 Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/oluadegbu/Codex--DSV-/releases/download/dmb-windows-v0.3.0-a46705985abd/DMB-Windows-0.3.0-a46705985abd-amd64.zip' -OutFile $zip -TimeoutSec 180
 if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant() -cne $expected) { throw 'ZIP integrity failure; preserve download and stop' }
 $package=Join-Path $install 'package'
 Expand-Archive -LiteralPath $zip -DestinationPath $package
 $python=Join-Path $package 'runtime\python\python.exe'
 $signature=Get-AuthenticodeSignature -LiteralPath $python
 if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Python Software Foundation') { throw 'Official embedded Python signature not verified' }
 # Native identity + exact manifest + pinned official Codex verification precede authentication.
 # Actual elapsed >1h, owned cancellation/crash/recovery, exclusive ownership and harmless canary denial.
 & $python -I (Join-Path $package 'app\tools\certify_windows_lifecycle.py') --full-hour
 if ($LASTEXITCODE -ne 0) { throw 'Native certification blocked; preserve all new and previous evidence; do not retry' }
 Write-Output 'Foreground certification finished. REQUEST-0009 remains withheld; no persistent task or remote relay was activated.'
}
