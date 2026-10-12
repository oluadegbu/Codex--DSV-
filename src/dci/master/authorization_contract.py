"""Offline OAuth resource-policy fixtures, never token verification or live auth.

No bearer token is accepted, decoded or issued. Only .invalid HTTPS origins and
synthetic principals are allowed. Output cannot authorize execution or a human
decision. Live MCP requires independently certified OAuth/signature validation.
"""
from dataclasses import dataclass
from urllib.parse import urlsplit
from dci.bridge.protocol import identifier

TOOL_SCOPES={
    'dmb_submit_job':'dmb:shadow:submit',
    'dmb_job_status':'dmb:shadow:read',
    'dmb_portfolio_report':'dmb:shadow:read',
    'dmb_control':'dmb:shadow:control',
    'heg_shadow_approval':'heg:shadow:approve',
}


def fixture_origin(value):
    if not isinstance(value,str):raise PermissionError('synthetic HTTPS origin required')
    parsed=urlsplit(value)
    if parsed.scheme!='https' or not parsed.hostname or not parsed.hostname.endswith('.invalid') or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise PermissionError('only offline .invalid resources are allowed')


@dataclass(frozen=True)
class FixtureClaims:
    issuer: str
    audience: tuple[str,...]
    subject: str
    client_id: str
    token_id: str
    scopes: tuple[str,...]
    issued_at: int
    not_before: int
    expires: int
    bound_request_id: str | None = None
    bound_scope_digest: str | None = None
    bound_expires: int | None = None
    fixture_only: bool = True


@dataclass(frozen=True)
class FixtureApprovalRequest:
    request_id: str
    scope_digest: str
    expires: int
    category: str = 'APPROVAL'
    fixture_only: bool = True


@dataclass(frozen=True)
class ShadowPolicyResult:
    principal: str
    tool: str
    project_id: str
    fixture_policy_allows: bool = True
    fixture_only: bool = True
    external_identity_verified: bool = False
    live_execution_allowed: bool = False
    human_approval: bool = False


class ShadowResourcePolicy:
    def __init__(self,issuer,resource,fixture_acl):
        fixture_origin(issuer);fixture_origin(resource)
        self.issuer,self.resource=issuer,resource
        self.acl={}
        for subject,rule in fixture_acl.items():
            if not isinstance(subject,str) or not subject.startswith('synthetic-') or set(rule)!={'client_id','scopes','projects'}:
                raise PermissionError('fixed synthetic subject ACL required')
            identifier(subject);identifier(rule['client_id'])
            if not rule['client_id'].startswith('synthetic-') or not set(rule['scopes'])<=set(TOOL_SCOPES.values()):
                raise PermissionError('invalid fixture client or scopes')
            for project in rule['projects']:identifier(project)
            self.acl[subject]={'client_id':rule['client_id'],'scopes':frozenset(rule['scopes']),'projects':frozenset(rule['projects'])}

    def check(self,claims,tool,project_id,now,approval=None):
        if type(claims) is not FixtureClaims or claims.fixture_only is not True or type(now) is not int or now<0:
            raise PermissionError('fixture claims required; no bearer tokens accepted')
        if claims.issuer!=self.issuer or claims.audience!=(self.resource,):
            raise PermissionError('issuer or exact resource audience mismatch')
        rule=self.acl.get(claims.subject)
        if rule is None or claims.client_id!=rule['client_id']:
            raise PermissionError('subject/client not authorized; no identity fallback')
        identifier(claims.token_id)
        if not claims.token_id.startswith('synthetic-'):
            raise PermissionError('synthetic token identity required')
        times=(claims.issued_at,claims.not_before,claims.expires)
        if any(type(t) is not int for t in times) or not 0<=claims.issued_at<=claims.not_before<=now<claims.expires or not 1<=claims.expires-claims.issued_at<=300:
            raise PermissionError('expired/future/unbounded fixture validity')
        if type(claims.scopes) is not tuple or any(not isinstance(s,str) for s in claims.scopes) or len(set(claims.scopes))!=len(claims.scopes) or not set(claims.scopes)<=rule['scopes']:
            raise PermissionError('excess, malformed or duplicate scope claims')
        if tool not in TOOL_SCOPES or TOOL_SCOPES[tool] not in claims.scopes or project_id not in rule['projects']:
            raise PermissionError('tool/project/scope not authorized')
        if tool=='heg_shadow_approval':
            if type(approval) is not FixtureApprovalRequest or approval.fixture_only is not True or approval.category!='APPROVAL':
                raise PermissionError('ordinary exact fixture request required; no degraded-outcome approval')
            identifier(approval.request_id)
            if not isinstance(approval.scope_digest,str) or len(approval.scope_digest)!=64 or any(c not in '0123456789abcdef' for c in approval.scope_digest) or type(approval.expires) is not int or type(claims.bound_expires) is not int:
                raise PermissionError('invalid fixture approval scope/expiry')
            if (claims.bound_request_id,claims.bound_scope_digest,claims.bound_expires)!=(approval.request_id,approval.scope_digest,approval.expires) or not now<approval.expires<=claims.expires:
                raise PermissionError('request/scope/expiry binding mismatch')
        elif approval is not None or any(v is not None for v in (claims.bound_request_id,claims.bound_scope_digest,claims.bound_expires)):
            raise PermissionError('approval bindings cannot authorize ordinary tools')
        return ShadowPolicyResult(claims.subject,tool,project_id)
