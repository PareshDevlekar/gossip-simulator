#!/usr/bin/env python3
from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1]
files=[root/'project2-bonus',root/'README.md',root/'Makefile',root/'Report-bonus.pdf']
for name in ['src','tests','scripts','results']:
 files.extend(p for p in (root/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
with zipfile.ZipFile(root.parent/'project2-bonus.zip','w',zipfile.ZIP_DEFLATED) as z:
 for file in sorted(files):z.write(file,Path('project2-bonus')/file.relative_to(root))
(root.parent/'Report-bonus.pdf').write_bytes((root/'Report-bonus.pdf').read_bytes())
print(f'Packaged {len(files)} bonus files; copied Report-bonus.pdf to project root.')
