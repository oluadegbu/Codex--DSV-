"""Real harmless subprocess protocol fixtures; not Windows Job/Codex certification."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from dci.master.document_windows import ReviewMachine, drive_review, FILES

SCRIPT = r'''
import sys,json
scenario=sys.argv[1]
for line in sys.stdin:
 m=json.loads(line); i=m.get('id')
 def emit(x): print(json.dumps(x),flush=True)
 if i==1:emit({'id':1,'result':{}})
 if i==2:emit({'id':2,'result':{'cwd':'scratch','approvalPolicy':'never','sandbox':{'type':'readOnly','networkAccess':False},'thread':{'id':'t'}}})
 if i==3:
  if scenario=='crash':sys.exit(73)
  if scenario=='timeout':continue
  emit({'id':3,'result':{'turn':{'id':'u'}}})
  if scenario=='complete':
   emit({'method':'item/completed','params':{'threadId':'t','turnId':'u','item':{'type':'agentMessage','text':json.dumps({'mode':'SHADOW','review':'Controlled subprocess fixture only'})}}})
   emit({'method':'turn/completed','params':{'threadId':'t','turn':{'id':'u','status':'completed'}}})
 if i==4:
  emit({'id':4,'result':{}})
  emit({'method':'turn/completed','params':{'threadId':'t','turn':{'id':'u','status':'interrupted'}}})
'''


class ProcessFixture:
    def __init__(self,root,scenario):
        self.out=(root/'stdout.log').open('wb');self.err=(root/'stderr.log').open('wb')
        self.process=subprocess.Popen([sys.executable,'-u','-c',SCRIPT,scenario],stdin=subprocess.PIPE,stdout=self.out,stderr=self.err)
        self.pid=self.process.pid
    def send(self,value):self.process.stdin.write((json.dumps(value)+'\n').encode());self.process.stdin.flush()
    def active(self):return int(self.process.poll() is None)
    def terminate(self):
        if self.process.poll() is None:self.process.kill()
        self.process.wait(timeout=3);return 0
    def close(self):self.process.stdin.close();self.out.close();self.err.close()


class ControlledSubprocessTests(unittest.TestCase):
    def scenario(self,name):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=ProcessFixture(root,name);m=ReviewMachine('scratch',{f:'Fixture' for f in FILES})
            if name=='complete':
                result=drive_review(p,m,root,lambda:False,2);self.assertEqual(result['mode'],'SHADOW')
            else:
                with self.assertRaises(Exception):drive_review(p,m,root,lambda:name=='cancel',.4)
            self.assertIsNotNone(p.process.poll())
    def test_real_subprocess_completion(self):self.scenario('complete')
    def test_real_subprocess_cancellation(self):self.scenario('cancel')
    def test_real_subprocess_crash(self):self.scenario('crash')
    def test_real_subprocess_timeout(self):self.scenario('timeout')
