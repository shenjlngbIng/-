#!/usr/bin/env python3
"""Refresh R12 lock metadata after an intentional, reviewed Surge.conf update.
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
lock=json.loads(LOCK.read_text(encoding='utf-8')) if LOCK.exists() else {'schema':4}
lock.update({
    'schema': 4,
    'profile': 'Surge iOS Privacy + Push R12',
    'generated': '2026-08-08',
    'profile_sha256': hashlib.sha256(text.encode()).hexdigest(),
    'profile_lines': len(lines),
    'active_rules': len(active),
    'required_invariants': {
        'final': 'FINAL,Final,dns-failed',
        'telegram': 'forced-proxy',
        'apns_capture': 'enabled',
        'apns_fallback': 'ApplePush_then_DIRECT',
        'encrypted_dns': 'EncryptedDNS_direct_no_proxy_hostname_loop',
        'rule_order': 'AdBlock_then_service_then_ChinaDomain_then_GEOIP_CN',
        'subscription_import': 'single_substore_policy_path_placeholder',
        'capture': {
            'include-all-networks': 'true',
            'include-local-networks': 'false',
            'include-apns': 'true',
            'include-cellular-services': 'false',
        },
    },
    'embedded_sources': sources,
})
LOCK.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'updated {LOCK}: rules={len(active)} sources={len(sources)}')
