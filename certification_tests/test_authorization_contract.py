from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from dci.master.authorization_contract import FixtureClaims, FixtureApprovalRequest, ShadowResourcePolicy
from dci.bridge.store import BridgeStore
from dci.bridge.runner import Runner
from dci.bridge.heg import HumanGateway

ISSUER='https://issuer.dmb.invalid'
RESOURCE='https://brain.dmb.invalid/mcp'


class AuthorizationContractTests(unittest.TestCase):
    def setUp(self):
        self.acl={'synthetic-brain':{'client_id':'synthetic-brain-client','scopes':['dmb:shadow:read','dmb:shadow:submit','dmb:shadow:control'],'projects':['BHB','HEG']},'synthetic-supervisor':{'client_id':'synthetic-supervisor-client','scopes':['heg:shadow:approve'],'projects':['HEG']}}
        self.policy=ShadowResourcePolicy(ISSUER,RESOURCE,self.acl)
        self.claims=FixtureClaims(ISSUER,(RESOURCE,),'synthetic-brain','synthetic-brain-client','synthetic-token-1',('dmb:shadow:read',),900,900,1100)
        self.request=FixtureApprovalRequest('synthetic-request','a'*64,1050)

    def approve_claims(self):
        return replace(self.claims,subject='synthetic-supervisor',client_id='synthetic-supervisor-client',scopes=('heg:shadow:approve',),bound_request_id=self.request.request_id,bound_scope_digest=self.request.scope_digest,bound_expires=self.request.expires)

    def test_read_policy_result_cannot_authorize_live_or_human_action(self):
        result=self.policy.check(self.claims,'dmb_job_status','BHB',1000)
        self.assertTrue(result.fixture_policy_allows);self.assertTrue(result.fixture_only)
        self.assertFalse(result.external_identity_verified);self.assertFalse(result.live_execution_allowed);self.assertFalse(result.human_approval)

    def test_issuer_requires_exact_equality(self):
        for issuer in ('https://wrong.invalid',ISSUER+'/other','https://issuer.dmb.invalid.attacker.invalid'):
            with self.assertRaises(PermissionError):self.policy.check(replace(self.claims,issuer=issuer),'dmb_job_status','BHB',1000)

    def test_audience_exact_resource_not_prefix_or_multi_resource(self):
        for audience in ((),(RESOURCE+'/other',),('https://wrong.invalid/mcp',),(RESOURCE,'https://extra.invalid/mcp'),RESOURCE):
            with self.assertRaises(PermissionError):self.policy.check(replace(self.claims,audience=audience),'dmb_job_status','BHB',1000)

    def test_missing_scope_denies_fixed_submit_and_control(self):
        for tool in ('dmb_submit_job','dmb_control'):
            with self.assertRaises(PermissionError):self.policy.check(self.claims,tool,'BHB',1000)
        self.assertTrue(self.policy.check(replace(self.claims,scopes=('dmb:shadow:submit',)),'dmb_submit_job','BHB',1000).fixture_policy_allows)

    def test_excess_and_duplicate_scope_claims_fail_closed(self):
        for scopes in (('admin',),('dmb:shadow:read','dmb:shadow:read'),('dmb:shadow:read','heg:shadow:approve'),['dmb:shadow:read']):
            with self.assertRaises(PermissionError):self.policy.check(replace(self.claims,scopes=scopes),'dmb_job_status','BHB',1000)

    def test_unknown_project_never_infers_access(self):
        for project in ('DAT_FUTURES','DCI','unknown','../HEG'):
            with self.assertRaises(PermissionError):self.policy.check(self.claims,'dmb_job_status',project,1000)

    def test_subject_and_client_no_fallback(self):
        for claims in (replace(self.claims,subject='synthetic-missing'),replace(self.claims,client_id='synthetic-other-client')):
            with self.assertRaises(PermissionError):self.policy.check(claims,'dmb_job_status','BHB',1000)

    def test_expired_not_yet_valid_and_unbounded_time_claims(self):
        for claims in (replace(self.claims,expires=1000),replace(self.claims,not_before=1001),replace(self.claims,issued_at=1001),replace(self.claims,expires=1300),replace(self.claims,expires=True),replace(self.claims,issued_at=-1)):
            with self.assertRaises(PermissionError):self.policy.check(claims,'dmb_job_status','BHB',1000)

    def test_refreshed_fixture_keeps_stable_subject(self):
        old=self.policy.check(self.claims,'dmb_job_status','BHB',1000)
        new=self.policy.check(replace(self.claims,token_id='synthetic-token-2',issued_at=950,not_before=950,expires=1200),'dmb_job_status','BHB',1000)
        self.assertEqual(old.principal,new.principal)

    def test_revoked_subject_acl_denies_without_identity_fallback(self):
        policy=ShadowResourcePolicy(ISSUER,RESOURCE,{'synthetic-supervisor':self.acl['synthetic-supervisor']})
        with self.assertRaises(PermissionError):policy.check(self.claims,'dmb_job_status','BHB',1000)

    def test_exact_approval_binding_is_still_only_fixture_policy(self):
        result=self.policy.check(self.approve_claims(),'heg_shadow_approval','HEG',1000,self.request)
        self.assertTrue(result.fixture_policy_allows);self.assertFalse(result.human_approval)

    def test_approval_wrong_request_scope_or_expiry_rejected(self):
        for request in (replace(self.request,request_id='synthetic-other'),replace(self.request,scope_digest='b'*64),replace(self.request,expires=1049),replace(self.request,expires=1000)):
            with self.assertRaises(PermissionError):self.policy.check(self.approve_claims(),'heg_shadow_approval','HEG',1000,request)

    def test_degraded_outcome_cannot_be_released_as_ordinary_approval(self):
        with self.assertRaises(PermissionError):self.policy.check(self.approve_claims(),'heg_shadow_approval','HEG',1000,replace(self.request,category='CONTROL_PLANE_DEGRADED'))

    def test_scope_expiry_and_ordinary_tool_bindings_are_not_interchangeable(self):
        for claims in (replace(self.approve_claims(),bound_expires=True),replace(self.claims,bound_request_id='synthetic-request')):
            with self.assertRaises(PermissionError):self.policy.check(claims,'dmb_job_status','HEG',1000)
        with self.assertRaises(PermissionError):self.policy.check(self.approve_claims(),'heg_shadow_approval','HEG',1000,replace(self.request,scope_digest='bad'))

    def test_bearer_token_and_nonfixture_inputs_are_rejected(self):
        for claims in ('Bearer synthetic-text',{'iss':ISSUER},replace(self.claims,fixture_only=False),replace(self.claims,token_id='not-a-fixture')):
            with self.assertRaises(PermissionError):self.policy.check(claims,'dmb_job_status','BHB',1000)
        with self.assertRaises(PermissionError):ShadowResourcePolicy('https://real.example.com',RESOURCE,self.acl)
        with self.assertRaises(PermissionError):ShadowResourcePolicy(ISSUER,'http://brain.dmb.invalid/mcp',self.acl)

    def test_arbitrary_tool_and_human_scope_cannot_be_assumed(self):
        for tool in ('sh -c whoami','enable_live_trading','heg_shadow_approval'):
            with self.assertRaises(PermissionError):self.policy.check(self.claims,tool,'HEG',1000)

    def test_fixture_policy_result_is_rejected_by_existing_heg(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=BridgeStore(Path(tmp)/'bridge.db')
            try:
                store.create_task('gated_shadow_note',1000,task_id='gated',correlation_id='corr')
                Runner(store,Path(__file__).resolve().parents[1]).tick(1001)
                row=store.db.execute('SELECT * FROM escalations').fetchone()
                request=FixtureApprovalRequest(row['id'],row['scope'],row['expires'])
                claims=replace(self.approve_claims(),expires=1350,issued_at=1050,not_before=1050,bound_request_id=request.request_id,bound_scope_digest=request.scope_digest,bound_expires=request.expires)
                # Bound fixture expiry remains no greater than claims expiry.
                result=self.policy.check(claims,'heg_shadow_approval','HEG',1060,request)
                with self.assertRaises(PermissionError):HumanGateway(store).decide(result,row['id'],row['scope'],'APPROVE',1060)
                self.assertEqual(store.task('gated')['state'],'NEEDS_HUMAN')
            finally:store.close()
