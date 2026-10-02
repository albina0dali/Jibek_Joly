"""Validate the delivered portable files against CHECKSUMS.json."""
import hashlib
import json
import sys
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
rows=json.loads((root/'CHECKSUMS.json').read_text(encoding='utf-8'))
for row in rows:
    file=root/row['path']
    assert file.is_file(),f'Missing {row["path"]}'
    assert hashlib.sha256(file.read_bytes()).hexdigest()==row['sha256'],f'Changed {row["path"]}'
print(f'Integrity verified: {len(rows)} files.')
