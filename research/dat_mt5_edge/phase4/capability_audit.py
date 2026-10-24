"""Source-level boundary check for the pinned passive consumer, not a host sandbox."""
import ast,json,hashlib
from pathlib import Path

def audit(path):
    raw=Path(path).read_bytes();tree=ast.parse(raw);imports=[];issues=[]
    forbidden={'open','exec','eval','compile','__import__','getattr','setattr','delattr','globals','locals','vars','input','breakpoint'}
    allowed_attributes={'loads','is_finite','max_age_ms','source_id','symbol','tick','max_spread','sequence','timestamp'}
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):imports.extend(x.name for x in n.names)
        if isinstance(n,ast.ImportFrom):imports.append(n.module)
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in forbidden:issues.append(n.func.id)
        if isinstance(n,ast.Attribute) and n.attr not in allowed_attributes:issues.append('unexpected attribute:'+n.attr)
    if set(imports)!={'json','decimal'}:issues.append('import boundary drift')
    return {'collector_sha256':hashlib.sha256(raw).hexdigest(),'imports':sorted(imports),'issues':sorted(set(issues)),
            'pass':not issues,'scope':'Pinned consumer source only; not proof of external exporter, Python host isolation or future broker connection.'}

if __name__=='__main__':
    r=audit(Path(__file__).with_name('collector.py'));print(json.dumps(r,sort_keys=True,indent=2))
    if not r['pass']:raise SystemExit(1)
