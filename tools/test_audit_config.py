#!/usr/bin/env python3
"""Mutation tests for R10.6 auditor."""
import subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
AUDIT=ROOT/'tools/audit_config.py'; base=(ROOT/'Surge.conf').read_text(encoding='utf-8')
def run(text):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'Surge.conf'; p.write_text(text,encoding='utf-8')
        return subprocess.run([sys.executable,str(AUDIT),str(p)],capture_output=True,text=True)
assert run(base).returncode==0
mutations={
'final_open':('FINAL,Final,dns-failed','FINAL,DIRECT'),
'telegram_direct':('DOMAIN-SUFFIX,t.me,Telegram','DOMAIN-SUFFIX,t.me,DIRECT'),
'apns_proxy':('DOMAIN-SUFFIX,push.apple.com,DIRECT','DOMAIN-SUFFIX,push.apple.com,Proxy'),
'capture_apns':('include-apns = false','include-apns = true'),
'ruleset':('FINAL,Final,dns-failed','RULE-SET,https://example.invalid/a.list,Proxy\nFINAL,Final,dns-failed')}
for name,(old,new) in mutations.items():
    assert old in base,name
    assert run(base.replace(old,new,1)).returncode!=0,name
print(f'PASS mutations={len(mutations)}')
