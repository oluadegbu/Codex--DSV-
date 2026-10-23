"""Bounded GitHub Git-data transport. No Git executable; no polling loop.

Only the compiled coordination branch is accessible. The deployment must supply
approved repository-scoped credentials privately. This code enrolls none.
"""
import base64
import json
import hashlib
import re
import ssl
import time
import urllib.error
import urllib.request
from urllib.parse import quote
from .document_bridge import BRANCH, LIMIT, unique_object
from dci.bridge.protocol import ProtocolError, canonical
from .windows_worker import NoRedirect


class GitHubDocuments:
    branch = BRANCH
    def __init__(self, repository, credential_provider, cache_store=None):
        if repository != 'oluadegbu/Codex--DSV-' or not callable(credential_provider):
            raise PermissionError('Explicit approved GitHub repository and private credential provider required')
        self.deadline = time.monotonic() + 60
        self.repository, self.credential = repository, credential_provider
        self.opener = urllib.request.build_opener(NoRedirect())
        self.head_trees = {}
        self.cache_store, self.cache = cache_store, {}
        if cache_store is not None:
            with cache_store.tx():
                cache_store.db.execute('CREATE TABLE IF NOT EXISTS ddb_github_cache(sha TEXT PRIMARY KEY,body TEXT)')

    def request(self, method, path, value=None):
        # Paths are compiled internally, never mailbox input. No auth on redirect.
        remaining = self.deadline - time.monotonic()
        if remaining <= 0: raise TimeoutError('Bounded GitHub invocation deadline')
        token = self.credential()
        if type(token) is not str or not token or '\n' in token or '\r' in token: raise PermissionError('Private GitHub authentication unavailable')
        request = urllib.request.Request('https://api.github.com/repos/'+self.repository+path,
            None if value is None else canonical(value).encode(), method=method,
            headers={'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json',
                     'Authorization': 'Bearer '+token, 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'Directive-DDB/1'})
        try:
            with self.opener.open(request, timeout=min(10, remaining)) as response:
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000: raise ProtocolError('GitHub response limit')
                return json.loads(raw, object_pairs_hook=unique_object)
        except urllib.error.HTTPError as error:
            if error.code in (409, 422) and method == 'PATCH': raise ConnectionError('Branch CAS conflict; re-read before retry') from None
            if error.code >= 500 or error.code == 429: raise ConnectionError('GitHub temporarily unavailable; pending state retained') from None
            raise PermissionError('GitHub authorization/route rejected; no credential details exported') from None
        except urllib.error.URLError as error:
            if isinstance(error.reason, ssl.SSLError): raise PermissionError('GitHub TLS verification failed') from None
            raise ConnectionError('GitHub transport unavailable; pending state retained') from None

    def snapshot(self):
        head = self.request('GET', '/git/ref/heads/'+quote(self.branch, safe='/'))['object']['sha']
        if not re.fullmatch('[0-9a-f]{40}', head): raise ProtocolError('Invalid branch head')
        commit = self.request('GET', '/git/commits/'+head)
        tree = commit['tree']['sha']
        entries = self.request('GET', '/git/trees/'+tree+'?recursive=1')
        if entries.get('truncated') is not False or len(entries['tree']) > 600: raise ProtocolError('Coordination branch capacity reached')
        files = {}
        for entry in entries['tree']:
            path = entry['path']
            if entry['type'] == 'tree': continue
            if entry['type'] != 'blob' or entry['mode'] != '100644' or not re.fullmatch(r'(reports|directives|state)/[A-Za-z0-9_./-]+\.json', path) or '..' in path or entry.get('size', LIMIT+1) > LIMIT:
                raise PermissionError('Dedicated documents-only branch required')
            cached = self.cache_store.db.execute('SELECT body FROM ddb_github_cache WHERE sha=?', (entry['sha'],)).fetchone() if self.cache_store else None
            if cached: raw = cached[0].encode()
            elif entry['sha'] in self.cache: raw = self.cache[entry['sha']].encode()
            else:
                blob = self.request('GET', '/git/blobs/'+entry['sha'])
                if blob['encoding'] != 'base64': raise ProtocolError('Expected bounded Git blob')
                raw = base64.b64decode(blob['content'].replace('\n',''), validate=True)
            if len(raw) > LIMIT or hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest() != entry['sha']:
                raise ProtocolError('Git blob identity/size mismatch')
            value = raw.decode('utf-8')
            if self.cache_store:
                with self.cache_store.tx(): self.cache_store.db.execute('INSERT OR IGNORE INTO ddb_github_cache VALUES (?,?)', (entry['sha'], value))
            else: self.cache[entry['sha']] = value
            files[path] = value
        self.head_trees = {head: tree}
        return head, files

    def publish(self, expected_head, changes):
        if expected_head not in self.head_trees: raise PermissionError('Fresh snapshot required before publication')
        # No arbitrary API paths, branch selection, deletes or executable file modes.
        for path, value in changes.items():
            if not re.fullmatch(r'(reports|directives|state)/[A-Za-z0-9_./-]+\.json', path) or '..' in path or type(value) is not str or len(value.encode()) > LIMIT:
                raise PermissionError('Bounded coordination JSON destinations only')
        tree = self.request('POST', '/git/trees', {'base_tree': self.head_trees[expected_head],
            'tree': [{'path': p, 'mode': '100644', 'type': 'blob', 'content': value} for p, value in changes.items()]})['sha']
        commit = self.request('POST', '/git/commits', {'message': 'DDB atomic document publication', 'tree': tree, 'parents': [expected_head]})['sha']
        # A sibling publication makes this non-fast-forward. Never force a ref.
        self.request('PATCH', '/git/refs/heads/'+self.branch, {'sha': commit, 'force': False})
        return commit


class GitHubCLIDocuments(GitHubDocuments):
    """Use already-enrolled official gh authentication; never extract its token.

    Explicitly selected, never a silent fallback after token failure. Auth repair
    or managed-secret enrollment requires the operator's approved mechanism.
    """
    def __init__(self, repository, cache_store=None):
        super().__init__(repository, lambda: None, cache_store)

    def request(self, method, path, value=None):
        import subprocess
        remaining=self.deadline-time.monotonic()
        if remaining<=0: raise TimeoutError('Bounded GitHub invocation deadline')
        argv=['gh','api','--hostname','github.com','--method',method,
              '/repos/'+self.repository+path,'-H','Accept: application/vnd.github+json',
              '-H','X-GitHub-Api-Version: 2022-11-28']
        if value is not None: argv += ['--input','-']
        try:
            result=subprocess.run(argv,input=None if value is None else canonical(value).encode(),
                capture_output=True,timeout=min(10,remaining),shell=False)
        except subprocess.TimeoutExpired:
            raise TimeoutError('GitHub CLI deadline; pending state retained') from None
        if result.returncode:
            detail=result.stderr.lower()
            if method=='PATCH' and any(code in detail for code in (b'http 409',b'http 422')):
                raise ConnectionError('GitHub branch CAS conflict')
            if any(code in detail for code in (b'http 500',b'http 502',b'http 503',b'http 429')):
                raise ConnectionError('GitHub temporarily unavailable')
            raise PermissionError('Existing GitHub CLI authentication/connectivity rejected; no credential details exported')
        if len(result.stdout)>2000000: raise ProtocolError('GitHub response limit')
        return json.loads(result.stdout,object_pairs_hook=unique_object)


class WindowsGitHubDocuments(GitHubDocuments):
    """Fresh reviewed namespace; never reinterpret quarantined Linux history.

    Branch creation/enrollment is a separate approval gate. This transport never
    creates the ref and accepts no arbitrary branch from a mailbox/configuration.
    """
    branch = 'coordination/dmb-ddb-windows-0011'
