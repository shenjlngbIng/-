#!/usr/bin/env python3
"""Validate R10.5 rule inventory and embedding metadata."""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
LOCK=ROOT/'Rules/r10.lock.json'
PROFILE=ROOT/'Surge.conf'
def active(path): return [x.strip() for x in path.read_text(encoding='utf-8').splitlines() if x.strip() and not x.lstrip().startswith('#')]
lock=json.loads(LOCK.read_text(encoding='utf-8'))
text=PROFILE.read_text(encoding='utf-8')
assert hashlib.sha256(text.encode()).hexdigest()==lock['profile_sha256'],'profile hash mismatch'
assert len([x for x in text.split('[Rule]',1)[1].splitlines() if x.strip() and not x.lstrip().startswith('#')])==lock['active_rules'],'active rule count mismatch'
errors=[]
source_files=list((ROOT/'Rules').glob('*.list'))
if not source_files:
    print(f'PASS package-mode sources=not-included profile_rules={lock["active_rules"]}')
    raise SystemExit(0)
for item in lock.get('embedded_sources',[]):
    path=ROOT/'Rules'/item['file']
    if not path.exists():
        errors.append(f'missing source: {item["file"]}')
        continue
    count=len(active(path))
    if count!=item['active_entries']: errors.append(f'{item["file"]}: expected {item["active_entries"]}, got {count}')
if errors:
    print('\n'.join(errors),file=sys.stderr); raise SystemExit(1)
print(f'PASS sources={len(lock.get("embedded_sources",[]))} profile_rules={lock["active_rules"]}')
