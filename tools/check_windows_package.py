"""Test the actual packaged runtime with no system Git/Python; never launch Codex."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def main(package, output, codex_fixture):
    if os.name != 'nt': raise PermissionError('Actual Windows package smoke required')
    python = package / 'runtime/python/python.exe'
    system = Path(os.environ['SystemRoot']) / 'System32'
    env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA'}}
    env['PATH'] = str(system)
    # Check the official Python executable signature, without changing trust or policy.
    literal = str(python).replace("'", "''")
    signature_script = "$s=Get-AuthenticodeSignature -LiteralPath '" + literal + "'; if($s.Status -ne 'Valid' -or $s.SignerCertificate.Subject -notmatch 'Python Software Foundation'){throw 'Official Python signature not verified'}; $s.Status"
    subprocess.run([str(system / 'WindowsPowerShell/v1.0/powershell.exe'), '-NoProfile', '-NonInteractive', '-Command',
                    signature_script], env=env, check=True, timeout=120)
    code = r'''
import hashlib,json,os,shutil,sqlite3,ssl,subprocess,tempfile,sys,threading,urllib.request,csv,io
from http.server import HTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from windows_package_runtime import verify_package,create_tls_certificate
from dci.master.windows_protocol import PeerKey,sign,verify
from dci.master.windows_native import require_identity,token_snapshot,system_directory
from dci.master.windows_codex_locator import discover,OFFICIAL_CODEX,pinned_image,canonical_path
from dci.bridge.store import BridgeStore
app=Path(sys.argv[1]); assert sys.version_info[:3]==(3,12,10)
assert shutil.which('git') is None and shutil.which('python') is None
meta=verify_package(app, '0.3.0'); assert meta['mode']=='SHADOW'
assert not (app/'deployment/phase10/activation.dpapi').exists()
from xml.etree import ElementTree as ET
task=ET.parse(app/'deployment/phase10/lifecycle-v0.3.0/Directive.DMB.ShadowWorker.Phase10.xml')
ns={'t':'http://schemas.microsoft.com/windows/2004/02/mit/task'}
assert task.find('.//t:LogonType',ns).text=='Password'
assert task.find('.//t:RunLevel',ns).text=='LeastPrivilege'
assert task.find('.//t:Repetition/t:Interval',ns).text=='PT5M'
assert task.find('.//t:RestartOnFailure',ns) is None
# Native Task Scheduler parser only: no registration, Run, or credentials.
ps=str(system_directory()/'WindowsPowerShell/v1.0/powershell.exe')
xml_path=str(app/'deployment/phase10/lifecycle-v0.3.0/Directive.DMB.ShadowWorker.Phase10.xml').replace("'", "''")
script="$s=New-Object -ComObject Schedule.Service; $s.Connect(); $t=$s.NewTask(0); $t.XmlText=[IO.File]::ReadAllText('"+xml_path+"'); if($t.Settings.MultipleInstances -ne 2 -or $t.Settings.RestartCount -ne 0 -or $t.Triggers.Item(1).Repetition.Interval -ne 'PT5M' -or $t.Principal.LogonType -ne 1 -or $t.Principal.RunLevel -ne 0){throw 'Unsafe task definition'}"
subprocess.run([ps,'-NoProfile','-NonInteractive','-Command',script],check=True,capture_output=True,timeout=15)
assert subprocess.check_output(['git','--version'],text=True).strip()=='git version 2.51.0.windows.1'
key=PeerKey('windows_codex_shadow','offline-smoke',2000,b'0'*32)
verify(key,sign(key,'worker_to_controller','POLL',1,{},1000),'worker_to_controller',1000)
with tempfile.TemporaryDirectory() as d:
 p=Path(d); create_tls_certificate(p/'certificate.pem',p/'key.pem')
 local=p/'local-appdata'; installed=local/'Programs/OpenAI/Codex/bin/codex.exe'
 installed.parent.mkdir(parents=True);shutil.copyfile(sys.argv[2],installed)
 def missing_path():raise RuntimeError('PATH lookup must not be used for the installed user-local binary')
 assert discover(local,missing_path,'x86_64')==installed.resolve(strict=True)
 profile=p/'profile'; junction_local=profile/'AppData/Local'
 standalone=profile/'.codex/packages/standalone'
 release=standalone/'releases/0.162.1-x86_64-pc-windows-msvc/bin/codex.exe'
 release.parent.mkdir(parents=True);shutil.copyfile(sys.argv[2],release)
 source=junction_local/'Programs/OpenAI/Codex/bin'
 source.parent.mkdir(parents=True)
 cmd=str(system_directory()/'cmd.exe')
 def junction(link,target):
  subprocess.run([cmd,'/d','/c','mklink','/J',str(link),str(target)],check=True,capture_output=True,timeout=5)
 current=standalone/'current'
 junction(current,release.parent.parent);junction(source,current/'bin')
 assert discover(junction_local,missing_path,'x86_64')==release.resolve(strict=True)
 with pinned_image(release) as (locked,identity):
  assert locked==release.resolve(strict=True) and len(identity)==3
  try:
   with release.open('r+b'):pass
  except OSError:pass
  else:raise RuntimeError('Pinned executable write must fail')
  try:release.parent.rename(release.parent.with_name('changed-bin'))
  except OSError:pass
  else:raise RuntimeError('Pinned executable directory rename must fail')
 outside=p/'outside';outside.mkdir();shutil.copyfile(sys.argv[2],outside/'codex.exe')
 source.rmdir();junction(source,outside)
 try:discover(junction_local,missing_path,'x86_64')
 except PermissionError:pass
 else:raise RuntimeError('Even matching official bytes at an untrusted junction must be rejected')
 source.rmdir();current.rmdir()
 discovery={'official_raw_release_SHA256':OFFICIAL_CODEX['x86_64'][1],
  'native_official_bin_current_versioned_release_junctions':'PASS',
  'matching_binary_untrusted_junction_rejected':'PASS',
  'native_pinned_image_write_and_directory_rename_denied':'PASS','native_file_identity':identity,

  'native_Windows_user_local_discovery_without_PATH':'PASS', 'PATH_lookup_called':False,
  'Codex_executed_in_CI':False}
 server=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);server.load_cert_chain(p/'certificate.pem',p/'key.pem')
 client=ssl.create_default_context(cafile=str(p/'certificate.pem'))
 assert client.check_hostname and client.verify_mode==ssl.CERT_REQUIRED
 class Echo(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_POST(self):
   raw=self.rfile.read(int(self.headers['Content-Length'])); packet=json.loads(raw)
   verify(key,packet,'worker_to_controller',1000)
   body=json.dumps(sign(key,'controller_to_worker','REPLY',1,{'fixture':'TLS_ONLY'},1000)).encode()
   self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 http=HTTPServer(('127.0.0.1',0),Echo); http.timeout=2
 http.socket=server.wrap_socket(http.socket,server_side=True)
 thread=threading.Thread(target=http.handle_request);thread.start()
 try:
  request=urllib.request.Request('https://127.0.0.1:'+str(http.server_port),json.dumps(sign(key,'worker_to_controller','POLL',1,{},1000)).encode())
  with urllib.request.urlopen(request,context=client,timeout=2) as response:verify(key,json.load(response),'controller_to_worker',1000)
 finally:
  thread.join(3);http.server_close()
 assert not thread.is_alive()
 db=BridgeStore(p/'audit.sqlite');db.verify_audit();db.close()
 db=BridgeStore(p/'audit.sqlite');db.verify_audit();db.close()
 subprocess.run(['git','init','--quiet',str(p/'scratch')],check=True,timeout=5)
actual=token_snapshot()
whoami=str(system_directory()/'whoami.exe')
user_rows=list(csv.reader(io.StringIO(subprocess.check_output([whoami,'/user','/fo','csv'],text=True))))
group_rows=list(csv.reader(io.StringIO(subprocess.check_output([whoami,'/groups','/fo','csv'],text=True))))[1:]
assert actual['user'].casefold()==user_rows[1][0].casefold()
assert actual['user_sid']==user_rows[1][1]
assert all(len(row)==4 for row in group_rows)
correct_sids={row[2] for row in group_rows}
legacy_wrong_column={row[1] for row in group_rows}
assert actual['integrity_sid'] in correct_sids
assert actual['integrity_sid'] not in legacy_wrong_column
assert correct_sids <= set(actual['group_sids']) | {actual['integrity_sid']}
assert not any(s.startswith('S-1-') for s in legacy_wrong_column)
native_identity_evidence={'process_user':actual['user'],'user_sid_matches_whoami':True,
 'TokenIntegrityLevel_sid':actual['integrity_sid'],'GetTokenInformation_groups_match_correct_CSV_column':True,
 'legacy_column_2_has_no_SIDs':True,'legacy_would_reject_any_valid_Medium_token':True,
 'elevated':actual['elevated'],'administrators_member':'S-1-5-32-544' in actual['group_sids']}
try:
 require_identity()
except PermissionError:
 guard='PASS CI identity rejected before worker launch'
else:
 raise RuntimeError('CI cannot substitute for the DirectiveCodex worker session')
print(json.dumps({'embedded_python':'PASS3.12.10','system_Git_Python_absent_from_PATH':True,'bundled_git':'PASS2.51.0.windows.1','TLS_crypto_native_dependencies':'PASS','sqlite_reopen_audit':'PASS','HMAC_protocol':'PASS','identity_guard':guard,'native_token_API_evidence':native_identity_evidence,'native_Codex_discovery':discovery,'native_five_minute_task_XML':'PASS parsed only; never registered','genuine_Codex':'NOT TESTED','services_installed':False}))
'''
    result = subprocess.run([str(python), '-I', '-c', code, str(package / 'app'), str(codex_fixture)], env=env,
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        print(result.stderr[-8000:], file=sys.stderr)
        raise RuntimeError('Actual embedded Windows runtime smoke failed')
    data = json.loads(result.stdout)
    data['official_python_Authenticode'] = 'PASS'
    output.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps(data))


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--codex-fixture',type=Path,required=True)
    a=p.parse_args();main(a.package.resolve(),a.output.resolve(),a.codex_fixture.resolve())
