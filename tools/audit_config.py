#!/usr/bin/env python3
"""Audit the Surge iOS Privacy + Push R12 profile."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

from convert_to_remote_rules import (
    REMOTE_BASE,
    REMOTE_RULES,
    UPSTREAM_BASE,
    UPSTREAM_COMMIT,
    UPSTREAM_ROUTING_RULES,
)
ROOT=Path(__file__).resolve().parent.parent
PROFILE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'Surge.conf'
LOCK=ROOT/'Rules/r10.lock.json'
UPSTREAM_LOCK=ROOT/'Rules/upstreams.lock.json'
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
        if k in out and name != 'Host': fail(f'duplicate key [{name}] {k}')
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
required={'include-all-networks':'true','include-local-networks':'false','include-apns':'true','include-cellular-services':'true','ipv6':'true','compatibility-mode':'3','hijack-dns':'*:53','allow-dns-svcb':'false','use-local-host-item-for-proxy':'false','dns-server':'223.5.5.5, 223.6.6.6','encrypted-dns-server':'https://dns.alidns.com/dns-query, tls://dns.alidns.com','encrypted-dns-follow-outbound-mode':'false','udp-policy-not-supported-behaviour':'REJECT','block-quic':'all-proxy','test-timeout':'8'}
for k,v in required.items():
    if g.get(k)!=v: fail(f'[General] {k}: expected {v!r}, got {g.get(k)!r}')
h=kv(sec['Host'],'Host')
bootstrap_values=[line.split('=',1)[1].strip() for line in active(sec['Host']) if line.split('=',1)[0].strip()=='dns.alidns.com']
if bootstrap_values != ['223.5.5.5','223.6.6.6','2400:3200::1']: fail('DNS bootstrap mappings for dns.alidns.com are missing or incorrect')
if 'system' in g.get('dns-server','').lower(): fail('system DNS is forbidden in the public privacy profile')
groups=kv(sec['Proxy Group'],'Proxy Group')
if len(groups)!=32: fail(f'expected 32 groups, got {len(groups)}')
proxy_group=[part.strip() for part in groups.get('Proxy','').split(',')]
if len(proxy_group)<2 or proxy_group[:2]!=['select','AllServer']:
    fail('Proxy must default to AllServer before regional groups')
all_server=groups.get('AllServer','')
if not all_server.startswith('fallback,'):
    fail('AllServer must use fallback mode')
for option in ('update-interval=3600','interval=60','timeout=300','evaluate-before-use=true','include-all-proxies=true'):
    if option not in all_server:
        fail(f'AllServer missing legacy stability option: {option}')
if 'policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL' not in all_server:
    fail('public profile must keep the non-routable subscription placeholder')
if not any(part.strip() == 'REJECT' for part in groups.get('Final','').split(',')):
    fail('Final must expose the strict REJECT choice')
for region in ('HongKong', 'TaiWan', 'Japan', 'Singapore', 'America'):
    if '(?!.*(?:专用|專用|解锁|解鎖))' in groups.get(region, ''):
        fail(f'{region} must not exclude streaming-optimized nodes')
rules=active(sec['Rule'])
if rules[-1]!='FINAL,Final,dns-failed': fail('FINAL invariant failed')
remote_rules = [x for x in rules if x.startswith(f'RULE-SET,{REMOTE_BASE}')]
expected_remote_rules = {
    f'RULE-SET,{REMOTE_BASE}{filename},{policy}'
    for filename, _label, policy in REMOTE_RULES
}
if set(remote_rules) != expected_remote_rules or len(remote_rules) != len(expected_remote_rules):
    missing = sorted(expected_remote_rules - set(remote_rules))
    unexpected = sorted(set(remote_rules) - expected_remote_rules)
    fail(f'remote RULE-SET inventory mismatch: missing={missing}, unexpected={unexpected}')
for rule in remote_rules:
    fields = rule.split(',')
    if len(fields) != 3 or not fields[1].startswith(REMOTE_BASE):
        fail(f'RULE-SET must use the repository CDN base: {rule}')
    if not fields[1].startswith('https://') or '..' in fields[1]:
        fail(f'unsafe remote RULE-SET URL: {rule}')
expected_routing_rules = {
    f'{kind},{url},{policy}' for kind, url, _label, policy in UPSTREAM_ROUTING_RULES
}
upstream_lock = json.loads(UPSTREAM_LOCK.read_text(encoding='utf-8'))
routing_lock = dict(upstream_lock.get('routing', {}))
if routing_lock.get('commit') != UPSTREAM_COMMIT:
    fail('routing upstream commit is not pinned to the profile')
if routing_lock.get('download_base') != UPSTREAM_BASE:
    fail('routing upstream download base is stale')
expected_from_lock = {
    f"{item['kind']},{UPSTREAM_BASE}{item['path']},{item['policy']}"
    for item in routing_lock.get('sources', [])
}
if expected_from_lock != expected_routing_rules:
    fail('routing upstream lock inventory does not match the profile')
actual_routing_rules = {
    rule
    for rule in rules
    if rule.startswith(('RULE-SET,https://cdn.jsdelivr.net/gh/blackmatrix7/',
                        'DOMAIN-SET,https://cdn.jsdelivr.net/gh/blackmatrix7/'))
}
if actual_routing_rules != expected_routing_rules:
    missing = sorted(expected_routing_rules - actual_routing_rules)
    unexpected = sorted(actual_routing_rules - expected_routing_rules)
    fail(f'upstream routing inventory mismatch: missing={missing}, unexpected={unexpected}')
for rule in actual_routing_rules:
    fields = rule.split(',', 2)
    if len(fields) != 3 or fields[0] not in {'RULE-SET', 'DOMAIN-SET'}:
        fail(f'upstream routing rule is malformed: {rule}')
    if not fields[1].startswith('https://cdn.jsdelivr.net/gh/blackmatrix7/'):
        fail(f'upstream routing URL must use the pinned CDN: {rule}')
expected_external_rules = expected_remote_rules | expected_routing_rules
actual_external_rules = {
    rule for rule in rules if rule.startswith(('RULE-SET,', 'DOMAIN-SET,'))
}
if actual_external_rules != expected_external_rules:
    missing = sorted(expected_external_rules - actual_external_rules)
    unexpected = sorted(actual_external_rules - expected_external_rules)
    fail(f'external rule inventory mismatch: missing={missing}, unexpected={unexpected}')
if '# Embedded rules' in text or 'embedded_sources' in text:
    fail('embedded rule content is forbidden; use external RULE-SET/DOMAIN-SET references')
snapshot_rules = {
    line.strip()
    for path in (ROOT / 'Rules').glob('*.list')
    for line in path.read_text(encoding='utf-8-sig').splitlines()
    if line.strip() and not line.lstrip().startswith(('#', ';', '//'))
}
embedded = sorted(set(rules) & snapshot_rules)
if embedded:
    fail(f'profile contains embedded rule snapshot content: {embedded[:3]}')

def rule_position(prefix: str) -> int:
    for index, rule in enumerate(rules):
        if rule.startswith(prefix):
            return index
    fail(f'missing ordering anchor: {prefix}')

youtube_pos = rule_position(f'RULE-SET,{REMOTE_BASE}YouTube.list,')
google_pos = rule_position(f'RULE-SET,{REMOTE_BASE}Google.list,')
china_pos = rule_position('RULE-SET,https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@ccc2d6b711007324bacb55cdfbbf7e36ad48145a/rule/Surge/China/China.list,')
global_pos = rule_position('RULE-SET,https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@ccc2d6b711007324bacb55cdfbbf7e36ad48145a/rule/Surge/Global/Global.list,')
global_domain_pos = rule_position('DOMAIN-SET,https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@ccc2d6b711007324bacb55cdfbbf7e36ad48145a/rule/Surge/Global/Global_Domain.list,')
local_china_pos = rule_position(f'RULE-SET,{REMOTE_BASE}ChinaDomain.list,')
geoip_pos = rule_position('GEOIP,CN,DIRECT')
if youtube_pos >= google_pos:
    fail('YouTube must precede Google')
for filename, _label, _policy in REMOTE_RULES:
    if filename == 'ChinaDomain.list':
        continue
    if rule_position(f'RULE-SET,{REMOTE_BASE}{filename},') >= global_pos:
        fail(f'{filename} must precede the upstream Global fallback')
if not (china_pos < global_pos < global_domain_pos < local_china_pos < geoip_pos):
    fail('upstream China/Global rules and local ChinaDomain supplement are out of order')
required_rules = [
    'PROTOCOL,DOH,EncryptedDNS',
    'PROTOCOL,DOH3,EncryptedDNS',
    'PROTOCOL,DOQ,EncryptedDNS',
]
required_rules += sorted(expected_remote_rules)
for r in required_rules:
    if r not in rules: fail(f'missing invariant: {r}')
valid_protocols = {'HTTP', 'HTTPS', 'TCP', 'UDP', 'DOH', 'DOH3', 'DOQ', 'QUIC', 'STUN'}
for r in rules:
    if r.startswith('PROTOCOL,'):
        fields = r.split(',')
        if len(fields) < 3 or fields[1].upper() not in valid_protocols:
            fail(f'unsupported PROTOCOL rule: {r}')
if any(('telegram' in r.lower() or ',t.me,' in r.lower()) and target(r)=='DIRECT' for r in rules): fail('Telegram traffic cannot be DIRECT')
if any(('APNs.list' in r or 'push.apple.com' in r or 'push-apple.com' in r) and target(r)=='DIRECT' for r in rules): fail('APNs traffic cannot be DIRECT')
if groups.get('EncryptedDNS','').split(',')[0].strip()!='fallback': fail('EncryptedDNS must be fallback')
if groups.get('ApplePush','').split(',')[0].strip()!='fallback': fail('ApplePush must be fallback')
if 'Proxy' not in groups.get('EncryptedDNS','') or 'DIRECT' not in groups.get('EncryptedDNS',''): fail('EncryptedDNS fallback members missing')
if 'Proxy' not in groups.get('ApplePush','') or 'DIRECT' not in groups.get('ApplePush',''): fail('ApplePush fallback members missing')
if len(rules)!=len(set(rules)): fail('duplicate active rules detected')
if LOCK.exists() and PROFILE.resolve()==(ROOT/'Surge.conf').resolve():
    lock=json.loads(LOCK.read_text(encoding='utf-8'))
    if lock['profile_sha256']!=hashlib.sha256(text.encode()).hexdigest(): fail('lock hash stale')
    if lock['active_rules']!=len(rules): fail('lock active rule count stale')
print(f'PASS R12 rules={len(rules)} sha256={hashlib.sha256(text.encode()).hexdigest()}')
