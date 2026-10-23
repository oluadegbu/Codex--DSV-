"""Portable native DDB receipt state; uncertain intents are never retried.

OS-specific subclasses provide preflight, execute and artifact verification.
Signing, publication and quarantine remain in the existing document bridge.
"""
import json
import time
from dci.bridge.protocol import canonical
from .windows_protocol import sha

TEMPLATE = 'codex_shadow_review_v1'


class NativeReceiptBackend:
    def run(self, directive, now):
        if directive['template'] != TEMPLATE: raise PermissionError('Fixed native template required')
        self.preflight(); task=directive['task_id']; scope=sha({'directive':directive,'pins':self.pins})
        with self.store.tx():
            old=self.store.db.execute('SELECT * FROM ddb_native_runs WHERE task=?',(task,)).fetchone()
            if old:
                if old['scope']!=scope: raise PermissionError('Native task ID rebound')
                if old['state']=='INTENT': return None  # Never rerun uncertain native effects.
                evidence=json.loads(old['evidence'])
            else:
                if self.store.db.execute('SELECT 1 FROM ddb_native_runs').fetchone(): raise PermissionError('One native foreground execution maximum')
                self.store.db.execute("INSERT INTO ddb_native_runs VALUES (?,?,'INTENT',NULL)",(task,scope))
                self.store.audit('ddb-native','execution_intent',{'task':task,'scope':scope},now)
                evidence=None
        if evidence is None:
            evidence=self._execute(task)
            with self.store.tx():
                self.store.db.execute("UPDATE ddb_native_runs SET state='SEALED',evidence=? WHERE task=?",(canonical(evidence),task))
                self.store.audit('ddb-native','completion_sealed',{'task':task,'digest':sha(evidence)},int(time.time()))
        self.verify(task,evidence);self.store.verify_audit()
        return {'kind':'VERIFIED_NATIVE_CODEX','scope_digest':scope,'result_digest':sha(evidence),
                'artifact_sha256':evidence['files_sha256']['stdout.log'],'git_commit':self.pins['git_commit'],'audit_valid':True,'exit_code':0}

    def review(self, report, now):
        old=self.store.db.execute('SELECT * FROM ddb_native_runs WHERE task=?',(report['task_id'],)).fetchone()
        if old is None or old['state'] not in {'SEALED','REVIEWED'}: raise PermissionError('No sealed native receipt')
        evidence=json.loads(old['evidence']);self.verify(report['task_id'],evidence)
        if report['evidence']['kind']!='VERIFIED_NATIVE_CODEX' or report['evidence']['scope_digest']!=old['scope'] or report['evidence']['result_digest']!=sha(evidence):
            raise PermissionError('Native supervisory evidence mismatch')
        with self.store.tx():
            self.store.db.execute("UPDATE ddb_native_runs SET state='REVIEWED' WHERE task=?",(report['task_id'],))
            self.store.audit('ddb-native','attested_review_accepted',{'task':report['task_id'],'human_approval':False},now)
