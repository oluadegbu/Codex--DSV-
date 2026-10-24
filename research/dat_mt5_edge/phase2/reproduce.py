"""Explicit public-data acquisition followed by offline research; no authority path."""
import argparse,json,hashlib
from pathlib import Path
from .acquire_archive import populate
from .acquire_mirror import run as normalize
from .research import run as research

def reproduce(root,output,offline=False):
    lock=json.loads(Path(__file__).with_name('source_lock.json').read_text())
    root=Path(root)
    if not offline:
        inventory=populate(root,lock['source_pins'])
        for sym,expected in lock['archive_inventory'].items():
            if inventory[sym]['archive_sha256']!=expected['archive_sha256']:raise ValueError('source archive hash drift')
        normalize(root,lock['source_pins'],workers=2)
        p=root/'mirror_manifest.json';manifest=json.loads(p.read_text())
        # Preserve frozen collection-time provenance; this is not a fresh primary check.
        manifest['primary_crossverified']=lock['primary_crossverified']
        manifest['primary_crosscheck']=lock['primary_crosscheck']
        p.write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n',newline='\n')
    manifest=json.loads((root/'mirror_manifest.json').read_text())
    for sym,expected in lock['normalized'].items():
        if manifest['instruments'][sym]['sha256']!=expected['sha256']:raise ValueError('normalized source drift')
    research(root,output)
    return hashlib.sha256((Path(output)/'phase2.json').read_bytes()).hexdigest()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--offline',action='store_true');a=p.parse_args()
    print(reproduce(a.root,a.output,a.offline))
