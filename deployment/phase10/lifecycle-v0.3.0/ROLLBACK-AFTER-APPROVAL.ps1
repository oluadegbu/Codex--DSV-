# Approved rollback only; preserve every package, DPAPI file, journal and quarantine.
$ErrorActionPreference = 'Stop'
$name = 'Directive.DMB.ShadowWorker.Phase10'
$task = Get-ScheduledTask -TaskName $name -TaskPath '\'
$expected = 'C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-OPS-0.3.0\package\runtime\python\python.exe'
if ($task.Actions.Count -ne 1 -or $task.Actions[0].Execute -ine $expected) { throw 'Task differs; refuse unrelated task modification' }
$stop = 'C:\Users\DirectiveCodex\AppData\Local\Directive\DMBWindowsWorker-ops-0.3.0\STOP'
if (-not (Test-Path -LiteralPath $stop)) { [IO.File]::WriteAllBytes($stop,[byte[]]@()) }
Disable-ScheduledTask -TaskName $name -TaskPath '\' | Out-Null
$limit = (Get-Date).AddSeconds(45)
do { $state = (Get-ScheduledTask -TaskName $name -TaskPath '\').State; if ($state -ne 'Running') { break }; Start-Sleep -Seconds 1 } while ((Get-Date) -lt $limit)
if ($state -eq 'Running') { throw 'Drain unverified; retain disabled task and evidence for exact-task emergency Stop review' }
Unregister-ScheduledTask -TaskName $name -TaskPath '\' -Confirm:$false
