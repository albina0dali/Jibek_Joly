"""Create checksums and an archive containing only portable deliverables."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path
root=Path(sys.argv[1]).resolve()
excluded={'node_modules','.venv','dist','__pycache__'}
def portable(p):
    return p.is_file() and not excluded.intersection(p.relative_to(root).parts) and p.suffix not in {'.pyc','.tsbuildinfo','.sqlite'} and not p.name.endswith(('.sqlite-wal','.sqlite-shm'))
files=sorted(p for p in root.rglob('*') if portable(p) and p.name!='CHECKSUMS.json')
checksums=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
(root/'CHECKSUMS.json').write_text(json.dumps(checksums,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archive=root.parent/(root.name+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in [*files,root/'CHECKSUMS.json']:z.write(p,root.name+'/'+p.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(f'{len(files)+1} portable files; ZIP {archive.stat().st_size} bytes; integrity OK.')
