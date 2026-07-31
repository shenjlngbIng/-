#!/usr/bin/env python3
"""Mutation regression tests for the R10.5 configuration auditor."""
from __future__ import annotations
import subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
AUDIT=ROOT/'tools/audit_config.py'; PROFILE=ROOT/'Surge.conf'
base=PROFILE.read_text(encoding='utf-8')
def run(text):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'Surge.conf'; p.write_text(text,encoding='utf-8')
        return subprocess.run([sys.executable,str(AUDIT),str(p)],capture_output=True,text=True)
# Baseline should pass when lock is not beside the temporary profile.
assert run(base).returncode==0
mutations={
 'final_open':('FINAL,Final,dns-failed','FINAL,DIRECT'),
 'telegram_direct':('DOMAIN-SUFFIX,t.me,Telegram','DOMAIN-SUFFIX,t.me,DIRECT'),
 'remove_doh':('encrypted-dns-server = https://dns.alidns.com/dns-query, https://doh.pub/dns-query','encrypted-dns-server = https://dns.alidns.com/dns-query'),
 'apns_proxy':('DOMAIN-SUFFIX,push.apple.com,DIRECT','DOMAIN-SUFFIX,push.apple.com,Proxy'),
 'capture_all':('include-all-networks = false','include-all-networks = true'),
 'runtime_ruleset':('FINAL,Final,dns-failed','RULE-SET,https://example.invalid/a.list,Proxy\nFINAL,Final,dns-failed'),
}
for name,(old,new) in mutations.items():
    assert old in base,f'mutation anchor missing: {name}'
    result=run(base.replace(old,new,1))
    assert result.returncode!=0,f'mutation unexpectedly passed: {name}'
print(f'PASS mutations={len(mutations)}')
