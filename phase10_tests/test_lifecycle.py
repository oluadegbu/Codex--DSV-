"""Real SQLite/process interruption checks; not Windows runtime certification."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET
from dci.master.windows_lifecycle import Lifecycle
from run_windows_lifecycle_host import validate_grant
import test_deployment


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.path = Path(self.tmp.name)/'lifecycle.sqlite'
    def tearDown(self): self.tmp.cleanup()
    def open(self): return Lifecycle(self.path, 'fixed-test-binding')
    def test_normal_rotation_continues_past_hour_without_resetting_crash_budget(self):
        l=self.open(); a=l.enter(1000); l.finish(a['owner'], 4300, 'NORMAL'); l.close()
        l=self.open(); b=l.enter(4600)
        self.assertEqual(b['state'],'ACTIVE');self.assertNotEqual(a['owner'],b['owner'])
        self.assertEqual(b['crashes'],0); l.store.verify_audit();l.close()
    def test_three_real_process_deaths_trip_persistent_circuit(self):
        # os._exit bypasses finally; the next invocation observes actual committed ACTIVE.
        script="from dci.master.windows_lifecycle import Lifecycle; import sys,os; l=Lifecycle(sys.argv[1],'fixed-test-binding'); s=l.enter(int(sys.argv[2])); assert s['state']=='ACTIVE'; os._exit(37)"
        for now in (1000,1601,2202):
            child=subprocess.run([sys.executable,'-c',script,str(self.path),str(now)],capture_output=True)
            self.assertEqual(child.returncode,37,child.stderr.decode())
            l=self.open(); r=l.enter(now+1); l.close()
            if now<2202:
                self.assertEqual(r['state'],'COOLDOWN')
                l=self.open();self.assertEqual(l.enter(now+299)['state'],'COOLDOWN');l.close()
        l=self.open();self.assertEqual(l.enter(9999)['state'],'BLOCKED')
        self.assertEqual(l.snapshot()['crashes'],3);l.store.verify_audit();l.close()
    def test_stop_cannot_be_cleared_by_removing_marker_or_restarting(self):
        l=self.open();self.assertEqual(l.enter(1000,stopped=True)['state'],'PAUSED');l.close()
        l=self.open();self.assertEqual(l.enter(5000)['state'],'PAUSED');l.close()
    def test_uncertainty_never_retries_even_with_unused_crash_budget(self):
        l=self.open();a=l.enter(1000);l.finish(a['owner'],1001,'UNCERTAIN');l.close()
        l=self.open();self.assertEqual(l.enter(5000)['state'],'BLOCKED');self.assertEqual(l.snapshot()['crashes'],0);l.close()
    def test_clock_regression_and_owner_substitution_block(self):
        l=self.open();a=l.enter(1000)
        with self.assertRaises(PermissionError):l.finish('other',1001,'NORMAL')
        self.assertFalse(l.heartbeat(a['owner'],999));self.assertEqual(l.enter(5000)['state'],'BLOCKED');l.close()
    def test_binding_drift_does_not_overwrite_original(self):
        l=self.open();l.close()
        with self.assertRaises(PermissionError):Lifecycle(self.path,'different-code')
        l=self.open();self.assertEqual(l.snapshot()['state'],'READY');l.close()
    def test_crash_counter_survives_normal_success(self):
        l=self.open();a=l.enter(1000);l.finish(a['owner'],1001,'CRASH')
        a=l.enter(1301);l.finish(a['owner'],1302,'NORMAL');l.close()
        l=self.open();self.assertEqual(l.enter(1602)['crashes'],1);l.close()
    def test_native_task_definition_has_one_restart_authority(self):
        ns={'t':'http://schemas.microsoft.com/windows/2004/02/mit/task'}
        task=ET.parse(Path(__file__).resolve().parents[1]/'deployment/phase10/lifecycle-v0.3.0/Directive.DMB.ShadowWorker.Phase10.xml')
        self.assertEqual(task.find('.//t:Repetition/t:Interval',ns).text,'PT5M')
        self.assertIsNone(task.find('.//t:RestartOnFailure',ns));self.assertIsNone(task.find('.//t:Repetition/t:Duration',ns))
        self.assertEqual(task.find('.//t:MultipleInstancesPolicy',ns).text,'IgnoreNew')
        self.assertIn('0.3.0',task.find('.//t:Command',ns).text)
    def test_extended_authority_requires_new_grant_version(self):
        g=test_deployment.DeploymentTests().base();g['version']=2;g['expires_at']=1000+28800
        validate_grant(g,{'source_commit':'a'*40},'b'*64,'c'*64,1001)
        for field,value in [('version',1),('expires_at',29801)]:
            bad=dict(g);bad[field]=value
            with self.assertRaises(PermissionError):validate_grant(bad,{'source_commit':'a'*40},'b'*64,'c'*64,1001)


if __name__=='__main__':unittest.main()
