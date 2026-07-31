#!/usr/bin/env python3
"""Refresh R10.5 lock metadata after an intentional, reviewed Surge.conf update.
This does not download or replace rules. It records the checked profile hash, line count,
active rule count, and source counts already declared in embedded block comments.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
PROFILE=ROOT/'Surge.conf'; LOCK=ROOT/'Rules/r10.lock.json'
text=PROFILE.read_text(encoding='utf-8'); lines=text.splitlines(); rule_text=text.split('[Rule]',1)[1]
active=[x.strip() for x in rule_text.splitlines() if x.strip() and not x.lstrip().startswith('#')]
sources=[]
for line in rule_text.splitlines():
    m=re.match(r'#\s+([^ ]+\.list)\s+·\s+(\d+)/(\d+)\s+·\s+(.+)$',line.strip())
    if m: sources.append({'file':m.group(1),'embedded_entries':int(m.group(2)),'active_entries':int(m.group(3)),'policy':m.group(4)})
lock=json.loads(LOCK.read_text(encoding='utf-8')) if LOCK.exists() else {'schema':2}
lock.update({'profile':'Surge iOS Stable Fail-Closed R10.5','profile_sha256':hashlib.sha256(text.encode()).hexdigest(),'profile_lines':len(lines),'active_rules':len(active),'embedded_sources':sources})
LOCK.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'updated {LOCK}: rules={len(active)} sources={len(sources)}')
