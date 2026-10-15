"""Review definition and activation gates; no scheduled task registration or Windows mock PASS."""
import copy
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET
from run_windows_operations_host import validate_grant

ROOT=Path(__file__).resolve().parents[1]
NS={'t':'http://schemas.microsoft.com/windows/2004/02/mit/task'}


class DeploymentTests(unittest.TestCase):
    def test_exact_task_identity_privilege_lifetime_and_action(self):
        task=ET.parse(ROOT/'deployment/phase10/Directive.DMB.ShadowWorker.Phase10.xml')
        get=lambda name:task.find('.//t:'+name,NS).text
        self.assertEqual(get('UserId'),'S-1-5-21-3675741470-1525898003-3877381073-1000')
        self.assertEqual(get('LogonType'),'Password');self.assertEqual(get('RunLevel'),'LeastPrivilege')
        self.assertEqual(get('MultipleInstancesPolicy'),'IgnoreNew');self.assertEqual(get('ExecutionTimeLimit'),'PT1H2M')
        self.assertEqual(get('Interval'),'PT5M');self.assertEqual(get('Count'),'3')
        self.assertTrue(get('Command').endswith('DMB-OPS-0.2.0-review1\\package\\runtime\\python\\python.exe'))
        self.assertNotIn('powershell',get('Arguments').lower());self.assertNotIn('cmd.exe',get('Command').lower())
        self.assertEqual(len(task.findall('.//t:Exec',NS)),1);self.assertEqual(len(task.findall('.//t:BootTrigger',NS)),1)
    def base(self):
        return {'version':1,'approval_reference':'FINAL-REVIEW-FIXTURE-NOT-AUTHORIZATION','host':'WIN-HQAAFGGU1AM','user_sid':'S-1-5-21-3675741470-1525898003-3877381073-1000','source_commit':'a'*40,'manifest_sha256':'b'*64,'task_xml_sha256':'c'*64,'issued_at':1000,'expires_at':2000,'operation':'windows_codex_ping','relay_endpoint':'https://approved.invalid/v1/dmb/windows','worker_pairing_sha256':'d'*64,'isolation_manifest_sha256':'e'*64,'Windows_acceptance_sha256':'f'*64}
    def check(self,g):return validate_grant(g,{'source_commit':'a'*40},'b'*64,'c'*64,1001)
    def test_exact_bound_configuration_can_be_reviewed_without_activation(self):
        self.assertEqual(self.check(self.base())['operation'],'windows_codex_ping')
    def test_reject_administrator_system_source_drift_and_unbounded_approval(self):
        for field,value in [('user_sid','S-1-5-18'),('user_sid','S-1-5-21-3675741470-1525898003-3877381073-500'),('host','OTHER'),('source_commit','0'*40),('manifest_sha256','0'*64),('task_xml_sha256','0'*64),('expires_at',5001),('operation','shell'),('approval_reference','')]:
            with self.subTest(field=field,value=value):
                g=self.base();g[field]=value
                with self.assertRaises(PermissionError):self.check(g)
    def test_missing_acceptance_or_fake_remote_endpoint_fails_closed(self):
        for field,value in [('Windows_acceptance_sha256',None),('relay_endpoint','https://127.0.0.1/v1/dmb/windows'),('relay_endpoint','https://localhost/v1/dmb/windows'),('relay_endpoint','http://approved.invalid/v1/dmb/windows')]:
            g=self.base();g[field]=value
            with self.assertRaises(PermissionError):self.check(g)
    def test_unrecognized_namespace_cannot_redirect_private_worker_state(self):
        from dci.master.windows_native import private_root
        with self.assertRaises(PermissionError):private_root('..\\DAT')


if __name__=='__main__':unittest.main()
