"""Download pinned public source archives; select plain tick CSVs without extracting paths."""
from pathlib import Path,PurePosixPath
import urllib.request,tarfile,json,hashlib

def populate(root,pins):
    root=Path(root);rd=root/'mirror_raw';rd.mkdir(parents=True,exist_ok=True);inventory={}
    for sym,pin in pins.items():
        target=root/f'{sym}_{pin}.tar.gz';url=f'https://codeload.github.com/FX-Data/FX-Data-{sym}-DS/tar.gz/{pin}'
        if not target.exists():
            partial=target.with_suffix('.partial');size=0
            with urllib.request.urlopen(url,timeout=30) as response,partial.open('wb')as f:
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk:break
                    size+=len(chunk)
                    if size>1024**3:raise ValueError('archive exceeds 1GiB bound')
                    f.write(chunk)
                    if size%(32*1024*1024)==0:print(sym,'archive_MB',size//1024**2,flush=True)
            partial.replace(target)
        digest=hashlib.sha256(target.read_bytes()).hexdigest();count=0
        with tarfile.open(target,'r|gz')as tar:
            for member in tar:
                parts=PurePosixPath(member.name).parts
                if not member.isfile()or len(parts)!=5:continue
                _,ss,year,month,name=parts
                if ss!=sym or year!='2018' or month not in ('01','04','07')or not name.endswith('h_ticks.csv'):continue
                if member.size>16*1024**2:raise ValueError('oversized tick file')
                # No archive filesystem paths are ever extracted or followed.
                data=tar.extractfile(member).read();(rd/f'{sym}_{name}').write_bytes(data);count+=1
        inventory[sym]=dict(pin=pin,url=url,archive_sha256=digest,archive_bytes=target.stat().st_size,selected_files=count)
        print(sym,'selected_files',count,flush=True)
    (root/'archive_inventory.json').write_text(json.dumps(inventory,sort_keys=True,indent=2)+'\n')
    return inventory
