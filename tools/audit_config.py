#!/usr/bin/env python3
"""Audit Surge iOS Stable Fail-Closed R11 LTS profile."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
PROFILE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'Surge.conf'
LOCK=ROOT/'Rules/r10.lock.json'
def fail(msg): raise AssertionError(msg)
def parse(text):
    sections={}; current=None
    for n,raw in enumerate(text.splitlines(),1):
        s=raw.strip()
        if s.startswith('[') and s.endswith(']'):
            current=s[1:-1]
            if current in sections: fail(f'duplicate section {current} at line {n}')
            sections[current]=[]
        elif current: sections[current].append(raw)
    return sections
def active(lines): return [x.strip() for x in lines if x.strip() and not x.lstrip().startswith('#')]
def kv(lines,name):
    out={}
    for line in active(lines):
        if '=' not in line: fail(f'missing = in [{name}]: {line}')
        k,v=(x.strip() for x in line.split('=',1))
        if k in out: fail(f'duplicate key [{name}] {k}')
        out[k]=v
    return out
def target(rule):
    f=[x.strip() for x in rule.split(',')]
    return f[1] if f[0]=='FINAL' else f[2]
text=PROFILE.read_text(encoding='utf-8')
if not text.endswith('\n') or '\r' in text or '\ufeff' in text: fail('profile must be UTF-8 LF and end with newline')
sec=parse(text)
if list(sec)!=['General','Host','Proxy','Proxy Group','Rule']: fail(f'section order mismatch: {list(sec)}')
g=kv(sec['General'],'General')
required={'include-all-networks':'false','include-local-networks':'false','include-apns':'false','include-cellular-services':'false','ipv6':'true','compatibility-mode':'3','hijack-dns':'*:53','allow-dns-svcb':'false','use-local-host-item-for-proxy':'false','encrypted-dns-follow-outbound-mode':'false','udp-policy-not-supported-behaviour':'REJECT','block-quic':'all-proxy'}
for k,v in required.items():
    if g.get(k)!=v: fail(f'[General] {k}: expected {v!r}, got {g.get(k)!r}')
groups=kv(sec['Proxy Group'],'Proxy Group')
if len(groups)!=30: fail(f'expected 30 groups, got {len(groups)}')
rules=active(sec['Rule'])
if rules[-1]!='FINAL,Final,dns-failed': fail('FINAL invariant failed')
if any(x.startswith('RULE-SET,') for x in rules): fail('runtime RULE-SET is forbidden')
for r in ['DOMAIN-SUFFIX,t.me,Telegram','DOMAIN-SUFFIX,push.apple.com,DIRECT','IP-CIDR,91.108.4.0/22,Telegram,no-resolve','IP-CIDR,149.154.160.0/20,Telegram,no-resolve']:
    if r not in rules: fail(f'missing invariant: {r}')
if any(('telegram' in r.lower() or ',t.me,' in r.lower()) and target(r)=='DIRECT' for r in rules): fail('Telegram traffic cannot be DIRECT')
if len(rules)!=len(set(rules)): fail('duplicate active rules detected')
if LOCK.exists() and PROFILE.resolve()==(ROOT/'Surge.conf').resolve():
    lock=json.loads(LOCK.read_text(encoding='utf-8'))
    if lock['profile_sha256']!=hashlib.sha256(text.encode()).hexdigest(): fail('lock hash stale')
    if lock['active_rules']!=len(rules): fail('lock active rule count stale')
print(f'PASS R11 LTS rules={len(rules)} sha256={hashlib.sha256(text.encode()).hexdigest()}')
