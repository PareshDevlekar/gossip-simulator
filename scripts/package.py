#!/usr/bin/env python3
from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1]
files=[root/'project2',root/'Makefile',root/'README.md',root/'Report.pdf']
for directory in ['src','tests','scripts','results']:
    files.extend(p for p in (root/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
with zipfile.ZipFile(root/'project2.zip','w',zipfile.ZIP_DEFLATED) as z:
    for file in sorted(files): z.write(file,Path('project2')/file.relative_to(root))
print(f'Packaged {len(files)} files into project2.zip')
