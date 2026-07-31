#!/usr/bin/env python3
"""Audit the public Surge iOS Stable Fail-Closed R10.5 profile."""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
PROFILE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'Surge.conf'
LOCK=ROOT/'Rules/r10.lock.json'
def fail(msg:str)->None: raise AssertionError(msg)
def parse(text:str):
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
enc=[x.strip() for x in g.get('encrypted-dns-server','').split(',') if x.strip()]
if enc!=['https://dns.alidns.com/dns-query','https://doh.pub/dns-query']: fail(f'encrypted DNS mismatch: {enc}')
host=kv(sec['Host'],'Host')
for k,v in {'sub.store':'127.0.0.1','dns.alidns.com':'223.5.5.5','doh.pub':'1.12.12.12'}.items():
    if host.get(k)!=v: fail(f'host bootstrap mismatch: {k}')
proxies=kv(sec['Proxy'],'Proxy')
if proxies!={'Fail-Closed':'http, 127.0.0.1, 1'}: fail('public profile must contain only Fail-Closed proxy')
groups=kv(sec['Proxy Group'],'Proxy Group')
if len(groups)!=30: fail(f'expected 30 groups, got {len(groups)}')
if groups.get('Final')!='select, Proxy, no-alert=0, hidden=0, include-all-proxies=0': fail('Final group must have only Proxy path')
if 'DIRECT' in [x.strip() for x in groups['Proxy'].split(',')]: fail('Proxy group contains DIRECT')
rules=active(sec['Rule'])
if rules.count('FINAL,Final,dns-failed')!=1 or rules[-1]!='FINAL,Final,dns-failed': fail('FINAL invariant failed')
if any(x.startswith('RULE-SET,') for x in rules): fail('runtime RULE-SET is forbidden')
for r in ['DOMAIN,dns.alidns.com,DIRECT','DOMAIN,doh.pub,DIRECT','DOMAIN,dns.pub,Proxy','DOMAIN,dot.pub,Proxy','DEST-PORT,53,REJECT','DEST-PORT,853,REJECT','DEST-PORT,8853,REJECT','GEOIP,CN,Domestic','PROTOCOL,STUN,Proxy','PROTOCOL,QUIC,Proxy','PROTOCOL,UDP,Proxy']:
    if rules.count(r)!=1: fail(f'missing or duplicated invariant rule: {r}')
# Telegram must be proxied and must not have a DIRECT path.
telegram=[r for r in rules if target(r)=='Telegram']
if not telegram or 'DOMAIN-SUFFIX,t.me,Telegram' not in rules: fail('Telegram routing invariant failed')
if any(('telegram' in r.lower() or ',t.me,' in r.lower()) and target(r)=='DIRECT' for r in rules): fail('Telegram traffic cannot be DIRECT')
# APNs captured rules are DIRECT in R10.5.
apns_expected={
 'DOMAIN-SUFFIX,push.apple.com,DIRECT',
 'DOMAIN-SUFFIX,push-apple.com.akadns.net,DIRECT',
 'DOMAIN-SUFFIX,push-apple.com,DIRECT',
 'IP-CIDR,17.249.0.0/16,DIRECT,no-resolve',
 'IP-CIDR,17.252.0.0/16,DIRECT,no-resolve',
 'IP-CIDR,17.57.144.0/22,DIRECT,no-resolve',
 'IP-CIDR,17.188.128.0/18,DIRECT,no-resolve',
 'IP-CIDR,17.188.20.0/23,DIRECT,no-resolve',
 'IP-CIDR6,2620:149:a44::/48,DIRECT,no-resolve',
 'IP-CIDR6,2403:300:a42::/48,DIRECT,no-resolve',
 'IP-CIDR6,2403:300:a51::/48,DIRECT,no-resolve',
 'IP-CIDR6,2a01:b740:a42::/48,DIRECT,no-resolve',
}
if not apns_expected.issubset(set(rules)): fail('APNs rules must be DIRECT')
# Duplicate complete active rules are not allowed.
seen=set(); dup=[]
for r in rules:
    if r in seen: dup.append(r)
    seen.add(r)
if dup: fail(f'duplicate rules: {dup[:5]}')
if LOCK.exists() and PROFILE.resolve()==(ROOT/'Surge.conf').resolve():
    lock=json.loads(LOCK.read_text(encoding='utf-8'))
    digest=hashlib.sha256(text.encode()).hexdigest()
    if lock.get('profile_sha256')!=digest: fail('Rules/r10.lock.json profile hash is stale')
    if lock.get('active_rules')!=len(rules): fail('Rules/r10.lock.json active rule count is stale')
print(f'PASS profile={PROFILE.name} sections={len(sec)} groups={len(groups)} rules={len(rules)} sha256={hashlib.sha256(text.encode()).hexdigest()}')
