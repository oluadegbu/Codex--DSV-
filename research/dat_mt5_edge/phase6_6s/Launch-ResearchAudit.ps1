# Foreground launcher only. The existing Phase 6.6 inspection engine is unchanged.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$InputRoot,
    [Parameter(Mandatory=$true)][string]$ExpectedAccount,
    [string]$ReviewedSchema = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
if ($env:OS -ne 'Windows_NT') { throw 'BLOCKED: Windows is required.' }
if (-not [Environment]::UserInteractive) { throw 'BLOCKED: use an interactive foreground session.' }
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
$account = $identity.Name.Split('\')[-1]
$expectedUser = Get-LocalUser -Name $ExpectedAccount -ErrorAction Stop
if ($expectedUser.SID.Value -ne $identity.User.Value -or -not $expectedUser.Enabled) {
    throw 'BLOCKED: expected enabled local account does not match effective SID.'
}
if ($account -ine $ExpectedAccount -or $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'BLOCKED: effective account mismatch or administrator token.'
}
# Reject filtered administrator accounts too, not just enabled admin memberships.
$subjectSids = @($identity.User.Value) + @($identity.Groups | ForEach-Object {$_.Value}) + @('S-1-1-0','S-1-5-11')
if ($subjectSids -contains 'S-1-5-32-544') { throw 'BLOCKED: administrator group exists in token.' }
if ($ExecutionContext.SessionState.LanguageMode -ne 'FullLanguage') {
    throw 'BLOCKED: native containment cannot be verified in this language mode; do not change policy.'
}
# Add-Type may use the current user's temporary directory for compilation.
# Verify that location is local, unredirected and outside source/production ancestors.
$earlySource=Get-Item -LiteralPath $InputRoot -Force
$scratch=[IO.Path]::GetTempPath()
$scratchDrive=New-Object IO.DriveInfo([IO.Path]::GetPathRoot($scratch))
if ($scratchDrive.DriveType -ne [IO.DriveType]::Fixed) { throw 'BLOCKED: compilation scratch must be local fixed storage.' }
$scratchNode=Get-Item -LiteralPath $scratch -Force
while ($null -ne $scratchNode) {
    if (($scratchNode.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'BLOCKED: redirected compilation scratch.' }
    $scratchNode=$scratchNode.Parent
}
$sourceParent=$earlySource
while ($null -ne $sourceParent -and $null -ne $sourceParent.Parent) {
    if ($scratch.StartsWith($sourceParent.FullName.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'BLOCKED: compilation scratch overlaps source/production.' }
    $sourceParent=$sourceParent.Parent
}

Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
public static class DatForeground {
  [DllImport("advapi32.dll", SetLastError=true)] static extern bool GetTokenInformation(IntPtr t,int c,IntPtr b,int n,out int needed);
  [DllImport("advapi32.dll")] static extern IntPtr GetSidSubAuthorityCount(IntPtr s);
  [DllImport("advapi32.dll")] static extern IntPtr GetSidSubAuthority(IntPtr s,uint i);
  [StructLayout(LayoutKind.Sequential)] struct Luid { public uint Low; public int High; }
  [DllImport("advapi32.dll",SetLastError=true,CharSet=CharSet.Unicode)] static extern bool LookupPrivilegeName(string system,ref Luid id,StringBuilder name,ref int length);
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr CreateJobObject(IntPtr a,string n);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool SetInformationJobObject(IntPtr j,int c,ref Limits x,uint n);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr j,IntPtr p);
  [DllImport("kernel32.dll", SetLastError=true,CharSet=CharSet.Unicode)] static extern bool CreateProcess(string app,StringBuilder cmd,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr env,string cwd,ref Startup si,out Proc pi);
  [DllImport("kernel32.dll", SetLastError=true)] static extern uint ResumeThread(IntPtr t);
  [DllImport("kernel32.dll")] static extern uint WaitForSingleObject(IntPtr p,uint ms);
  [DllImport("kernel32.dll")] static extern bool GetExitCodeProcess(IntPtr p,out uint c);
  [DllImport("kernel32.dll")] static extern bool TerminateProcess(IntPtr p,uint c);
  [DllImport("kernel32.dll")] static extern bool TerminateJobObject(IntPtr j,uint c);
  [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
  [StructLayout(LayoutKind.Sequential)] struct Basic {
    public long UserTime,JobTime; public uint Flags; public UIntPtr Min,Max;
    public uint Active; public UIntPtr Affinity; public uint Priority,Scheduling;
  }
  [StructLayout(LayoutKind.Sequential)] struct Io { public ulong R,W,O,RB,WB,OB; }
  [StructLayout(LayoutKind.Sequential)] struct Limits {
    public Basic Basic; public Io Io; public UIntPtr ProcessMemory,JobMemory,PeakProcess,PeakJob;
  }
  [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] struct Startup {
    public uint Size; public string Reserved,Desktop,Title;
    public uint X,Y,XS,YS,XC,YC,Fill,Flags; public short Show,ReservedSize;
    public IntPtr ReservedPtr,StdIn,StdOut,StdErr;
  }
  [StructLayout(LayoutKind.Sequential)] struct Proc { public IntPtr Process,Thread; public uint Pid,Tid; }
  public static uint IntegrityRid() {
    int n=0; IntPtr token=WindowsIdentity.GetCurrent().Token;
    GetTokenInformation(token,25,IntPtr.Zero,0,out n);
    if(n<=0) throw new Win32Exception();
    IntPtr b=Marshal.AllocHGlobal(n);
    try {
      if(!GetTokenInformation(token,25,b,n,out n)) throw new Win32Exception();
      IntPtr sid=Marshal.ReadIntPtr(b); byte count=Marshal.ReadByte(GetSidSubAuthorityCount(sid));
      return unchecked((uint)Marshal.ReadInt32(GetSidSubAuthority(sid,(uint)(count-1))));
    } finally { Marshal.FreeHGlobal(b); }
  }
  public static void AssertOrdinaryToken() {
    using(WindowsIdentity identity=WindowsIdentity.GetCurrent()) {
      IntPtr token=identity.Token; int n=0; IntPtr flag=Marshal.AllocHGlobal(4);
      try {
        if(!GetTokenInformation(token,29,flag,4,out n) || Marshal.ReadInt32(flag)!=0) throw new InvalidOperationException("BLOCKED: AppContainer/unknown token");
      } finally { Marshal.FreeHGlobal(flag); }
      GetTokenInformation(token,3,IntPtr.Zero,0,out n);
      if(n<=0) throw new Win32Exception();
      IntPtr b=Marshal.AllocHGlobal(n);
      try {
        if(!GetTokenInformation(token,3,b,n,out n)) throw new Win32Exception();
        int count=Marshal.ReadInt32(b);
        string denied="|SeBackupPrivilege|SeRestorePrivilege|SeTakeOwnershipPrivilege|SeDebugPrivilege|SeImpersonatePrivilege|SeAssignPrimaryTokenPrivilege|SeCreateTokenPrivilege|SeTcbPrivilege|SeLoadDriverPrivilege|";
        for(int i=0;i<count;i++) {
          Luid id=(Luid)Marshal.PtrToStructure(IntPtr.Add(b,4+i*12),typeof(Luid));
          int size=256; StringBuilder name=new StringBuilder(size);
          if(!LookupPrivilegeName(null,ref id,name,ref size)) throw new Win32Exception();
          if(denied.IndexOf("|"+name.ToString()+"|",StringComparison.Ordinal)>=0) throw new InvalidOperationException("BLOCKED: sensitive privilege assigned");
        }
      } finally { Marshal.FreeHGlobal(b); }
    }
  }
  static string Quote(string s) {
    if(s.IndexOf('"')>=0 || s.EndsWith("\\")) throw new ArgumentException("unsafe argument");
    return "\""+s+"\"";
  }
  // Create suspended, attach limits, then resume: no uncontained audit interval.
  public static int Run(string exe,string[] args,string cwd,int seconds) {
    IntPtr job=CreateJobObject(IntPtr.Zero,null);
    if(job==IntPtr.Zero) throw new Win32Exception();
    Proc p=new Proc(); bool created=false;
    try {
      Limits l=new Limits(); l.Basic.Flags=0x2000|0x8|0x100|0x200;
      l.Basic.Active=1; l.ProcessMemory=(UIntPtr)(512UL*1024*1024); l.JobMemory=l.ProcessMemory;
      if(!SetInformationJobObject(job,9,ref l,(uint)Marshal.SizeOf(typeof(Limits)))) throw new Win32Exception();
      StringBuilder cmd=new StringBuilder(Quote(exe)); foreach(string a in args) cmd.Append(" ").Append(Quote(a));
      Startup si=new Startup(); si.Size=(uint)Marshal.SizeOf(typeof(Startup));
      if(!CreateProcess(exe,cmd,IntPtr.Zero,IntPtr.Zero,false,4,IntPtr.Zero,cwd,ref si,out p)) throw new Win32Exception();
      created=true;
      if(!AssignProcessToJobObject(job,p.Process)) throw new Win32Exception();
      if(ResumeThread(p.Thread)==0xffffffff) throw new Win32Exception();
      Stopwatch clock=Stopwatch.StartNew();
      for(;;) {
        uint state=WaitForSingleObject(p.Process,100);
        if(state!=0 && state!=258) throw new Win32Exception();
        long bytes=0;
        foreach(string f in System.IO.Directory.EnumerateFiles(cwd,"*",System.IO.SearchOption.AllDirectories)) {
          bytes=checked(bytes+new System.IO.FileInfo(f).Length);
          if(bytes>128L*1024*1024) { TerminateJobObject(job,126); throw new System.IO.IOException("output size stop threshold"); }
        }
        if(state==0) { uint code; if(!GetExitCodeProcess(p.Process,out code)) throw new Win32Exception(); return unchecked((int)code); }
        if(clock.Elapsed.TotalSeconds>seconds) { TerminateJobObject(job,124); throw new TimeoutException("audit wall-time limit"); }
      }
    } finally {
      // KILL_ON_JOB_CLOSE terminates the child if the foreground controller exits.
      if(created) { TerminateProcess(p.Process,125); CloseHandle(p.Thread); CloseHandle(p.Process); }
      CloseHandle(job);
    }
  }
}
'@
$integrity = [DatForeground]::IntegrityRid()
if ($integrity -ne 8192) { throw 'BLOCKED: this foreground route requires non-elevated Medium integrity.' }
[DatForeground]::AssertOrdinaryToken()

function Assert-NoReparse([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    while ($null -ne $item) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'BLOCKED: reparse path.' }
        if ($item -is [IO.FileInfo]) { $item = $item.Directory } else { $item = $item.Parent }
    }
}
function Assert-ReadOnlyAcl([string]$Path,[bool]$AncestorOnly=$false) {
    $acl = Get-Acl -LiteralPath $Path
    $raw = New-Object Security.AccessControl.RawSecurityDescriptor($acl.GetSecurityDescriptorBinaryForm(),0)
    if ($null -eq $raw.DiscretionaryAcl) { throw 'BLOCKED: null/unverifiable DACL.' }
    foreach ($rawAce in $raw.DiscretionaryAcl) {
        if ($rawAce.AceType -ne [Security.AccessControl.AceType]::AccessAllowed -and $rawAce.AceType -ne [Security.AccessControl.AceType]::AccessDenied) {
            throw 'BLOCKED: unsupported conditional/object ACL; no read-only inference.'
        }
    }
    $owner = $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value
    if ($subjectSids -contains $owner) { throw 'BLOCKED: worker owns source or ancestor; read-only control not established.' }
    # Conservative proof: any matching write allow blocks, even if a deny might override it.
    # WriteData, Append, EA, Attributes, DeleteChild, Delete, WriteDac, WriteOwner, GenericWrite/All.
    [long]$mask = 0x500D0156
    if ($AncestorOnly) { $mask = 0x500D0040 }
    $readAllowed=$false
    foreach ($ace in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
        if (($ace.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) -ne 0) { continue }
        if (-not $AncestorOnly -and ($subjectSids -contains $ace.IdentityReference.Value) -and (([long]$ace.FileSystemRights -band 0x80000001L) -ne 0)) {
            if ($ace.AccessControlType -eq [Security.AccessControl.AccessControlType]::Deny) { throw 'BLOCKED: source read-deny or ambiguous read access.' }
            $readAllowed=$true
        }
        if ($ace.AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow) { continue }
        if (($subjectSids -contains $ace.IdentityReference.Value) -and (([long]$ace.FileSystemRights -band $mask) -ne 0)) {
            throw 'BLOCKED: matching source/ancestor write allowance; no permissions will be changed.'
        }
    }
    if (-not $AncestorOnly -and -not $readAllowed) { throw 'BLOCKED: source read access not proven by conservative ACL screen.' }
}

$source = (Get-Item -LiteralPath $InputRoot -Force).FullName.TrimEnd('\')
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw 'BLOCKED: source directory unavailable.' }
Assert-NoReparse $source
$python = (Get-Command python.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
if ($python.StartsWith($source+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'BLOCKED: interpreter is inside dataset.' }
Assert-NoReparse $python

# This inspection package has an exact source constant. Validate it, never patch it.
$documents = [Environment]::GetFolderPath('MyDocuments')
if (-not $documents) { throw 'BLOCKED: user Documents unavailable.' }
Assert-NoReparse $documents
$parent = Join-Path $documents 'DATMT5Research'
if (Test-Path -LiteralPath $parent) { Assert-NoReparse $parent }
$run = Join-Path $parent ('Phase6_6S_'+[Guid]::NewGuid().ToString('N'))
if ($run.StartsWith($source+'\',[StringComparison]::OrdinalIgnoreCase) -or $source.StartsWith($run+'\',[StringComparison]::OrdinalIgnoreCase)) {
    throw 'BLOCKED: output/source overlap.'
}
$inputAncestor=(Get-Item -LiteralPath $source).Parent
while ($null -ne $inputAncestor -and $null -ne $inputAncestor.Parent) {
    if ($run.StartsWith($inputAncestor.FullName.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) {
        throw 'BLOCKED: output lies in a non-volume source ancestor/production tree.'
    }
    $inputAncestor=$inputAncestor.Parent
}
$drive = New-Object IO.DriveInfo([IO.Path]::GetPathRoot($run))
if ($drive.DriveType -ne [IO.DriveType]::Fixed) { throw 'BLOCKED: output must be on local fixed storage.' }
if ($drive.AvailableFreeSpace -lt 256MB) { throw 'BLOCKED: at least 256 MiB free required.' }
New-Item -ItemType Directory -Path $run -Force | Out-Null
$status = @{state='PREFLIGHT';worker_sid=$identity.User.Value;integrity_rid=$integrity;source_modified=$false;strategy_runs=0;holdout_analyzed=$false}
$resultPath = Join-Path $run 'launch-result.json'
try {
    # ACL-only census: no data contents, no write probes, no ACL edits.
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $stack = New-Object 'Collections.Generic.Stack[string]'
    $stack.Push($source)
    $nodes = 0
    while ($stack.Count -gt 0) {
        if ($timer.Elapsed.TotalSeconds -gt 120) { throw 'BLOCKED: ACL preflight exceeds 120 seconds.' }
        $path = $stack.Pop(); $nodes++
        if ($nodes -gt 20000 -or $path.Length -gt 512) { throw 'BLOCKED: tree count/path budget; no widening.' }
        $item = Get-Item -LiteralPath $path -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'BLOCKED: source contains reparse point.' }
        Assert-ReadOnlyAcl $path
        if ($item.PSIsContainer) {
            foreach ($child in [IO.Directory]::EnumerateFileSystemEntries($path)) {
                if ($child.Length -gt 512 -or ($nodes+$stack.Count) -ge 20000) { throw 'BLOCKED: tree/path budget.' }
                $stack.Push($child)
            }
        }
    }
    $ancestor = (Get-Item -LiteralPath $source).Parent
    while ($null -ne $ancestor) { Assert-ReadOnlyAcl $ancestor.FullName $true; $ancestor=$ancestor.Parent }
    $status.acl_nodes_verified=$nodes
    $package = Join-Path $run 'inspect_data.py'
    $url='https://raw.githubusercontent.com/oluadegbu/Codex--DSV-/9eadc569f3084c1252460d17dd82e892f5799993/research/dat_mt5_edge/phase6_6/inspect_data.py'
    $request=[Net.HttpWebRequest]::Create($url); $request.Timeout=30000
    $request.ReadWriteTimeout=10000; $request.AllowAutoRedirect=$false
    $response=$request.GetResponse(); $inputStream=$response.GetResponseStream()
    $outputStream=[IO.File]::Open($package,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try {
        $buffer=New-Object byte[] 4096; $received=0
        while (($n=$inputStream.Read($buffer,0,$buffer.Length)) -gt 0) {
            $received+=$n; if ($received -gt 16384) { throw 'BLOCKED: audit download size limit.' }
            $outputStream.Write($buffer,0,$n)
        }
    } finally { $outputStream.Dispose(); $inputStream.Dispose(); $response.Dispose() }
    if ((Get-FileHash -LiteralPath $package -Algorithm SHA256).Hash -ine 'f25f7539b3b0f7940766167ff06c182cea576c8e59a33627e1e49c0592d79961') {
        throw 'BLOCKED: published audit hash mismatch.'
    }
    $probePath=Join-Path $run 'verify_dependency.py'
    @'
import sys,ast,pathlib
p=pathlib.Path(sys.argv[1]); t=ast.parse(p.read_text())
s=[ast.literal_eval(n.value.args[0]) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='SOURCE' for x in n.targets)]
assert sys.version_info>=(3,10)
assert len(s)==1 and pathlib.Path(s[0]).resolve()==pathlib.Path(sys.argv[2]).resolve()
'@ | Set-Content -LiteralPath $probePath -Encoding UTF8
    if ([DatForeground]::Run($python,@('-I','-S','-B',$probePath,$package,$source),$run,10) -ne 0) { throw 'BLOCKED: dependency or exact source mismatch.' }
    $out = Join-Path $run 'inventory'; New-Item -ItemType Directory -Path $out | Out-Null
    $status.state='RUNNING_BOUNDED_INVENTORY'
    $status | ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding UTF8
    if ([DatForeground]::Run($python,@('-I','-S','-B',$package,'inventory','--output',$out,'--restriction-attestation','VERIFIED_STANDARD_USER_SOURCE_READ_ONLY'),$run,600) -ne 0) {
        throw 'BLOCKED: inventory failed; partial output is not complete.'
    }
    $summary = Get-Content -LiteralPath (Join-Path $out 'inventory_summary.json') -Raw | ConvertFrom-Json
    if (-not $summary.enumeration_complete -or -not $summary.checksums_complete) { throw 'BLOCKED: inventory is incomplete; inspect budget/error records.' }
    $status.state='INVENTORY_COMPLETE_QUALITY_BLOCKED_REVIEWED_SCHEMA'
    if ($ReviewedSchema) {
        Assert-NoReparse $ReviewedSchema
        if ((Get-Item -LiteralPath $ReviewedSchema).Length -gt 65536) { throw 'BLOCKED: schema size budget.' }
        if ((Resolve-Path -LiteralPath $ReviewedSchema).Path.StartsWith($source+'\',[StringComparison]::OrdinalIgnoreCase)) {
            throw 'BLOCKED: reviewed control schema must be outside transferred input.'
        }
        $schema=Get-Content -LiteralPath $ReviewedSchema -Raw | ConvertFrom-Json
        if (-not $schema.reviewed_schema -or $schema.timestamp_convention -ne 'UTC_VERIFIED') { throw 'BLOCKED: unreviewed schema/timezone.' }
        $relative=[string]$schema.relative_path
        if (-not $relative -or $relative.Contains(':') -or [IO.Path]::IsPathRooted($relative) -or (($relative -split '[\\/]') -contains '..')) {
            throw 'BLOCKED: invalid schema source path.'
        }
        $candidate=[IO.Path]::GetFullPath((Join-Path $source $relative))
        if (-not $candidate.StartsWith($source+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'BLOCKED: schema source escape.' }
        Assert-NoReparse $candidate
        $quality=Join-Path $run 'quality'; New-Item -ItemType Directory -Path $quality | Out-Null
        if ([DatForeground]::Run($python,@('-I','-S','-B',$package,'audit','--schema',(Resolve-Path -LiteralPath $ReviewedSchema).Path,'--output',$quality,'--restriction-attestation','VERIFIED_STANDARD_USER_SOURCE_READ_ONLY'),$run,60) -ne 0) {
            throw 'BLOCKED: quality inspection failed; no certification.'
        }
        $status.state='QUALITY_INSPECTED_CERTIFICATION_PENDING'
    }
    $status.certification='NOT_CERTIFIED'; $status.schema_guessed=$false
} catch {
    $status.state='BLOCKED'; $status.error=$_.Exception.Message
    throw
} finally {
    $status | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Write-Host ('Local results (keep private): '+$run)
    Write-Host ('Status: '+$status.state)
}
