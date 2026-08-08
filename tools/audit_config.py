#!/usr/bin/env python3
"""Audit the Surge iOS Privacy + Push R12 profile."""
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
if list(sec)!=['General','Host','Proxy','Proxy Group','MITM','Script','Rule']: fail(f'section order mismatch: {list(sec)}')
g=kv(sec['General'],'General')
required={'include-all-networks':'true','include-local-networks':'false','include-apns':'true','include-cellular-services':'false','ipv6':'true','compatibility-mode':'3','hijack-dns':'*:53','allow-dns-svcb':'false','use-local-host-item-for-proxy':'false','encrypted-dns-follow-outbound-mode':'false','udp-policy-not-supported-behaviour':'REJECT','block-quic':'all-proxy'}
for k,v in required.items():
    if g.get(k)!=v: fail(f'[General] {k}: expected {v!r}, got {g.get(k)!r}')
if any(line.lower().replace(' ','').startswith('sub.store=') for line in active(sec['Host'])):
    fail('sub.store must not be mapped to a local IP when policy-path uses sub.store')
mitm=kv(sec['MITM'],'MITM')
if mitm.get('hostname')!='%APPEND% sub.store':
    fail('[MITM] must append sub.store for the embedded Sub-Store rewrite')
scripts=kv(sec['Script'],'Script')
core=scripts.get('Sub-Store Core','')
simple=scripts.get('Sub-Store Simple','')
core_pattern=r'pattern=^https?:\/\/sub\.store\/((download)|api\/(preview|sync|(utils\/node-info)))'
if 'Sub-Store Core' not in scripts or 'type=http-request' not in core or core_pattern not in core:
    fail('embedded Sub-Store Core rewrite is missing or changed')
if 'Sub-Store Simple' not in scripts or 'type=http-request' not in simple or 'pattern=^https?:\\/\\/sub\\.store' not in simple:
    fail('embedded Sub-Store Simple rewrite is missing or changed')
expected_scripts = {
    'Sub-Store Core': 'script-path=https://cdn.jsdelivr.net/gh/sub-store-org/Sub-Store@b43580e93e3ca2171d62ab17d1806afdc5fadd01/sub-store-1.min.js',
    'Sub-Store Simple': 'script-path=https://cdn.jsdelivr.net/gh/sub-store-org/Sub-Store@b43580e93e3ca2171d62ab17d1806afdc5fadd01/sub-store-0.min.js',
}
for name,value in (('Sub-Store Core',core),('Sub-Store Simple',simple)):
    if expected_scripts[name] not in value:
        fail(f'{name} must use the repository-pinned Sub-Store script')
groups=kv(sec['Proxy Group'],'Proxy Group')
if len(groups)!=32: fail(f'expected 32 groups, got {len(groups)}')
rules=active(sec['Rule'])
if rules[-1]!='FINAL,Final,dns-failed': fail('FINAL invariant failed')
if any(x.startswith('RULE-SET,') for x in rules): fail('runtime RULE-SET is forbidden')
ad_anchor='DOMAIN-KEYWORD,-ad.a.yximgs.com,AdBlock'
china_anchor='DOMAIN,acg.tv,Domestic,extended-matching'
geoip_anchor='GEOIP,CN,Domestic'
if rules.index(ad_anchor) > rules.index(china_anchor): fail('AdBlock must precede ChinaDomain')
if rules.index(china_anchor) > rules.index(geoip_anchor): fail('ChinaDomain must precede GEOIP,CN')
if 'DOMAIN-SUFFIX,cn,DIRECT,no-resolve' in rules: fail('broad .cn DIRECT rule is forbidden')
all_server=groups.get('AllServer','')
all_server_parts=[part.strip().lower() for part in all_server.split(',')]
if all_server_parts[:2] != ['fallback', 'fail-closed']:
    fail('AllServer must start with fallback, Fail-Closed')
if 'include-all-proxies=true' not in all_server_parts:
    fail('AllServer must collect proxies imported into [Proxy]')
policy_paths=[part for part in all_server_parts if part.startswith('policy-path=')]
if policy_paths != ['policy-path=your_substore_surge_url']:
    fail('AllServer must contain exactly one subscription placeholder policy-path')
if 'sub.store' in all_server.lower() or 'example.invalid' in all_server.lower():
    fail('AllServer contains an unsafe or placeholder subscription URL')
required_rules = [
    'DOMAIN-SUFFIX,t.me,Telegram',
    'DOMAIN-SUFFIX,push.apple.com,ApplePush',
    'DOMAIN-SUFFIX,push-apple.com.akadns.net,ApplePush',
    'DOMAIN-SUFFIX,push-apple.com,ApplePush',
    'PROTOCOL,DOH,EncryptedDNS',
    'PROTOCOL,DOH3,EncryptedDNS',
    'PROTOCOL,DOQ,EncryptedDNS',
    'PROTOCOL,DOT,EncryptedDNS',
    'PROTOCOL,DNS,EncryptedDNS',
    'IP-CIDR,91.108.4.0/22,Telegram,no-resolve',
    'IP-CIDR,149.154.160.0/20,Telegram,no-resolve',
]
required_rules += [
    f'IP-CIDR,{network},ApplePush,no-resolve'
    for network in (
        '17.249.0.0/16',
        '17.252.0.0/16',
        '17.57.144.0/22',
        '17.188.128.0/18',
        '17.188.20.0/23',
    )
]
required_rules += [
    f'IP-CIDR6,{network},ApplePush,no-resolve'
    for network in (
        '2620:149:a44::/48',
        '2403:300:a42::/48',
        '2403:300:a51::/48',
        '2a01:b740:a42::/48',
    )
]
for r in required_rules:
    if r not in rules: fail(f'missing invariant: {r}')
if any(('telegram' in r.lower() or ',t.me,' in r.lower()) and target(r)=='DIRECT' for r in rules): fail('Telegram traffic cannot be DIRECT')
if any(('push.apple.com' in r or 'push-apple.com' in r) and target(r)=='DIRECT' for r in rules): fail('APNs traffic cannot be DIRECT')
if groups.get('EncryptedDNS','').split(',')[0].strip()!='fallback': fail('EncryptedDNS must be fallback')
if groups.get('ApplePush','').split(',')[0].strip()!='fallback': fail('ApplePush must be fallback')
if 'Proxy' not in groups.get('EncryptedDNS','') or 'DIRECT' not in groups.get('EncryptedDNS',''): fail('EncryptedDNS fallback members missing')
if 'Proxy' not in groups.get('ApplePush','') or 'DIRECT' not in groups.get('ApplePush',''): fail('ApplePush fallback members missing')
if g.get('encrypted-dns-server') != 'https://dns.alidns.com/dns-query, https://doh.pub/dns-query': fail('domestic encrypted DNS endpoint invariant failed')
if g.get('dns-server') != '223.5.5.5, 114.114.114.114': fail('domestic DNS bootstrap invariant failed')
if 'system' in g.get('dns-server','').lower(): fail('system DNS cannot be an upstream')
if len(rules)!=len(set(rules)): fail('duplicate active rules detected')
if LOCK.exists() and PROFILE.resolve()==(ROOT/'Surge.conf').resolve():
    lock=json.loads(LOCK.read_text(encoding='utf-8'))
    if lock['profile_sha256']!=hashlib.sha256(text.encode()).hexdigest(): fail('lock hash stale')
    if lock['active_rules']!=len(rules): fail('lock active rule count stale')
print(f'PASS R12 rules={len(rules)} sha256={hashlib.sha256(text.encode()).hexdigest()}')
