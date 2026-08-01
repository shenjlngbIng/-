#!/usr/bin/env python3
"""Validate R11 LTS lock metadata."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
text=(ROOT/'Surge.conf').read_text(encoding='utf-8')
lock=json.loads((ROOT/'Rules/r10.lock.json').read_text(encoding='utf-8'))
rules=[x.strip() for x in text.split('[Rule]',1)[1].splitlines() if x.strip() and not x.lstrip().startswith('#')]
assert lock['profile']=='Surge iOS Stable Fail-Closed R11 LTS'
assert lock['profile_sha256']==hashlib.sha256(text.encode()).hexdigest()
assert lock['profile_lines']==len(text.splitlines())
assert lock['active_rules']==len(rules)
print(f'PASS R11 LTS lock rules={len(rules)}')
