#!/usr/bin/env python3
"""Audit the public Surge iOS Stable Fail-Closed R10.1 profile."""

from __future__ import annotations

import hashlib
import ipaddress
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "Surge.conf"
REPO = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else PROFILE.parent
PIN = "541641b64bf57ba83ccb9df6c59bd15b447ac265"
SUBSCRIPTION_NOTE = "# 【订阅地址填写处】将下一行占位链接替换为 Sub-Store 转换后的订阅链接"
PUBLIC_POLICY_PATH = "https://example.invalid/REPLACE_WITH_SUB_STORE_URL"


def fail(message: str) -> None:
    raise AssertionError(message)


def parse_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            if current in sections:
                fail(f"duplicate section [{current}] at line {number}")
            sections[current] = []
        elif current is not None:
            sections[current].append(raw)
    return sections


def active(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]


def kv(lines: list[str], section_name: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in active(lines):
        if "=" not in line:
            fail(f"missing '=' in [{section_name}]: {line}")
        key, value = (part.strip() for part in line.split("=", 1))
        if key in result:
            fail(f"duplicate key in [{section_name}]: {key}")
        result[key] = value
    return result


def target_of_rule(line: str) -> str:
    fields = [part.strip() for part in line.split(",")]
    if fields[0] == "RULE-SET":
        return fields[2]
    if fields[0] == "FINAL":
        return fields[1]
    if fields[-1].lower() == "no-resolve":
        return fields[-2]
    return fields[-1]


text = PROFILE.read_text(encoding="utf-8")
if not text.endswith("\n"):
    fail("profile must end with a newline")
if "\r" in text or "\ufeff" in text:
    fail("profile contains CR or BOM")
lines = text.splitlines()
sections = parse_sections(lines)
expected_sections = ["General", "Host", "Proxy", "Proxy Group", "Rule"]
if list(sections) != expected_sections:
    fail(f"section order mismatch: {list(sections)}")

general = kv(sections["General"], "General")
required_general = {
    "loglevel": "warning",
    "auto-suspend": "false",
    "ipv6": "true",
    "ipv6-vif": "auto",
    "compatibility-mode": "1",
    "wifi-assist": "false",
    "all-hybrid": "false",
    "include-all-networks": "false",
    "include-local-networks": "false",
    "include-apns": "true",
    "include-cellular-services": "false",
    "icmp-forwarding": "false",
    "dns-server": "223.5.5.5, 119.29.29.29",
    "hijack-dns": "*:53",
    "allow-dns-svcb": "false",
    "use-local-host-item-for-proxy": "false",
    "allow-wifi-access": "false",
    "allow-hotspot-access": "false",
    "http-api-web-dashboard": "false",
    "proxy-restricted-to-lan": "true",
    "gateway-restricted-to-lan": "true",
    "udp-policy-not-supported-behaviour": "REJECT",
    "block-quic": "all-proxy",
}
for key, expected in required_general.items():
    if general.get(key) != expected:
        fail(f"[General] {key}: expected {expected!r}, got {general.get(key)!r}")

for server in [part.strip() for part in general["dns-server"].split(",")]:
    ipaddress.ip_address(server)
if "system" in general["dns-server"].lower():
    fail("system DNS fallback is forbidden")

for forbidden_key in {
    "encrypted-dns-server",
    "encrypted-dns-follow-outbound-mode",
    "encrypted-dns-skip-cert-verification",
    "tun-excluded-routes",
    "http-api",
    "external-controller-access",
    "managed-config",
}:
    if forbidden_key in general:
        fail(f"forbidden General key: {forbidden_key}")

hosts = kv(sections["Host"], "Host")
if hosts != {"sub.store": "127.0.0.1"}:
    fail(f"unexpected [Host] mapping: {hosts}")

proxies = kv(sections["Proxy"], "Proxy")
if proxies != {"Fail-Closed": "http, 127.0.0.1, 1"}:
    fail(f"public profile contains an unexpected proxy: {proxies}")
proxy_text = "\n".join(active(sections["Proxy"])).lower()
for unsafe in ("skip-cert-verify=true", "sni=off", "= direct", "= reject", "policy-path="):
    if unsafe in proxy_text:
        fail(f"unsafe proxy definition: {unsafe}")

groups = kv(sections["Proxy Group"], "Proxy Group")
if len(groups) != 30:
    fail(f"expected 30 policy groups, got {len(groups)}")
group_lines = [line.strip() for line in sections["Proxy Group"]]
if group_lines.count(SUBSCRIPTION_NOTE) != 1:
    fail("Sub-Store subscription location note is missing or duplicated")
note_index = group_lines.index(SUBSCRIPTION_NOTE)
all_server_index = next(
    (index for index, line in enumerate(group_lines) if line.startswith("AllServer =")),
    None,
)
if all_server_index is None or all_server_index - note_index != 1:
    fail("Sub-Store subscription location note must be directly above AllServer")
if groups.get("Final") != "select, Proxy, no-alert=0, hidden=0, include-all-proxies=0":
    fail("Final group is not a single Proxy path")
if "DIRECT" in groups["Proxy"].split(","):
    fail("Proxy group contains DIRECT")
policy_path_groups = {
    name
    for name, value in groups.items()
    if re.search(r"(?:^|,)\s*policy-path\s*=", value)
}
if policy_path_groups != {"AllServer"}:
    fail(f"policy-path must appear only in AllServer: {sorted(policy_path_groups)}")
all_server_fields = [field.strip() for field in groups["AllServer"].split(",")]
policy_path_fields = [
    field for field in all_server_fields if re.match(r"^policy-path\s*=", field)
]
if policy_path_fields != [f"policy-path={PUBLIC_POLICY_PATH}"]:
    fail("public AllServer must contain exactly one non-routable policy-path placeholder")
if all_server_fields.count("update-interval=86400") != 1:
    fail("AllServer policy-path must use update-interval=86400")
if "include-all-proxies=1" not in groups["AllServer"]:
    fail("AllServer must retain locally audited [Proxy] entries")

region_names = ["HongKong", "TaiWan", "Japan", "Singapore", "America"]
region_samples = {
    "HongKong": ["🇭🇰香港-Gemini-IEPL", "🇭🇰香港 2-IEPL"],
    "TaiWan": ["🇹🇼台湾-IEPL", "🇹🇼台湾 2-IEPL"],
    "Japan": ["🇯🇵日本-IEPL-GPT", "🇯🇵日本 2-IEPL-GPT", "🇯🇵日本 4-IEPL-家宽"],
    "Singapore": ["🇸🇬新加坡-Gemini-IEPL", "🇸🇬新加坡 2-Gemini-IEPL"],
    "America": ["🇺🇸美国-IEPL-GPT", "🇺🇸美国 2-IEPL-GPT"],
}
for name in region_names:
    value = groups.get(name, "")
    for token in ("url-test", "Fail-Closed", "tolerance=150", "interval=1800", "evaluate-before-use=true"):
        if token not in value:
            fail(f"{name} missing {token}")
    if "DIRECT" in value:
        fail(f"{name} contains DIRECT")
    match = re.search(r"(?:^|,\s*)policy-regex-filter=(.*?),\s*tolerance=", value)
    if not match:
        fail(f"{name} is missing a parseable policy-regex-filter")
    try:
        pattern = re.compile(match.group(1))
    except re.error as exc:
        fail(f"{name} has an invalid policy-regex-filter: {exc}")
    for policy_name in region_samples[name]:
        if not pattern.search(policy_name):
            fail(f"{name} excludes expected AI-capability node: {policy_name}")
    if pattern.search(f"{region_samples[name][0]}-专用"):
        fail(f"{name} includes an explicitly dedicated node")

# Resolve the group graph and prove which groups can reach DIRECT.
group_members: dict[str, list[str]] = {}
for name, value in groups.items():
    fields = [part.strip() for part in value.split(",")]
    members: list[str] = []
    for field in fields[1:]:
        if "=" in field:
            continue
        members.append(field)
    group_members[name] = members


def reaches_direct(name: str, visiting: frozenset[str] = frozenset()) -> bool:
    if name == "DIRECT":
        return True
    if name not in group_members or name in visiting:
        return False
    return any(reaches_direct(member, visiting | {name}) for member in group_members[name])


direct_groups = {name for name in groups if reaches_direct(name)}
if direct_groups != {"Apple", "Domestic"}:
    fail(f"unexpected groups can reach DIRECT: {sorted(direct_groups)}")

rules = active(sections["Rule"])
allowed_types = {
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-WILDCARD",
    "IP-CIDR",
    "IP-CIDR6",
    "IP-ASN",
    "USER-AGENT",
    "DEST-PORT",
    "PROTOCOL",
    "RULE-SET",
    "FINAL",
}
for number, line in enumerate(rules, 1):
    rule_type = line.split(",", 1)[0]
    if rule_type not in allowed_types:
        fail(f"unsupported main rule type at active rule {number}: {rule_type}")
    target = target_of_rule(line)
    if target not in {"DIRECT", "REJECT", "REJECT-DROP"} | set(groups) | set(proxies):
        fail(f"undefined policy {target!r} in rule: {line}")

if rules[-1] != "FINAL,Final,dns-failed" or sum(line.startswith("FINAL,") for line in rules) != 1:
    fail("FINAL rule must be unique and exactly FINAL,Final,dns-failed")
if any(line.startswith("RULE-SET,SYSTEM,") or line.startswith("RULE-SET,LAN,") for line in rules):
    fail("mutable internal rule set is forbidden")
if any(line.startswith("PROTOCOL,DOH") or line.startswith("PROTOCOL,DOQ") for line in rules):
    fail("PROTOCOL DOH/DOQ without Surge encrypted DNS is misleading")

apns = [
    "DOMAIN-SUFFIX,push.apple.com,Proxy",
    "DOMAIN-KEYWORD,push-apple.com.akadns.net,Proxy",
    "DOMAIN-SUFFIX,push-apple.com,Proxy",
    "DOMAIN-KEYWORD,apple.com.edgekey.net,Proxy",
    "IP-CIDR,17.249.0.0/16,Proxy,no-resolve",
    "IP-CIDR,17.252.0.0/16,Proxy,no-resolve",
    "IP-CIDR,17.57.144.0/22,Proxy,no-resolve",
    "IP-CIDR,17.188.128.0/18,Proxy,no-resolve",
    "IP-CIDR,17.188.20.0/23,Proxy,no-resolve",
    "IP-CIDR6,2620:149:a44::/48,Proxy,no-resolve",
    "IP-CIDR6,2403:300:a42::/48,Proxy,no-resolve",
    "IP-CIDR6,2403:300:a51::/48,Proxy,no-resolve",
    "IP-CIDR6,2a01:b740:a42::/48,Proxy,no-resolve",
]
for expected in apns:
    if rules.count(expected) != 1:
        fail(f"APNs rule missing or duplicated: {expected}")
first_direct_group_rule = min(
    i for i, line in enumerate(rules) if target_of_rule(line) in {"Apple", "Domestic"}
)
if max(rules.index(line) for line in apns) >= first_direct_group_rule:
    fail("APNs rules must precede Apple/Domestic direct allowlists")

required_dns_rules = {
    "DOMAIN,dns.pub,Proxy",
    "DOMAIN,doh.pub,Proxy",
    "DOMAIN,dot.pub,Proxy",
    "DOMAIN,dns.google,Proxy",
    "DOMAIN-SUFFIX,alidns.com,Proxy",
    "DOMAIN-SUFFIX,cloudflare-dns.com,Proxy",
    "DOMAIN-SUFFIX,quad9.net,Proxy",
    "DOMAIN-SUFFIX,nextdns.io,Proxy",
    "DEST-PORT,53,REJECT",
    "DEST-PORT,853,REJECT",
    "DEST-PORT,8853,REJECT",
}
missing_dns_rules = required_dns_rules - set(rules)
if missing_dns_rules:
    fail(f"missing DNS closure rules: {sorted(missing_dns_rules)}")

udp_gate = ["PROTOCOL,STUN,Proxy", "PROTOCOL,QUIC,Proxy", "PROTOCOL,UDP,Proxy"]
udp_positions = [rules.index(line) for line in udp_gate]
if udp_positions != sorted(udp_positions) or udp_positions[-1] >= first_direct_group_rule:
    fail("STUN/QUIC/UDP gate must precede all Apple/Domestic direct rules")
for port_rule in ("DEST-PORT,53,REJECT", "DEST-PORT,853,REJECT", "DEST-PORT,8853,REJECT"):
    if rules.index(port_rule) >= udp_positions[-1]:
        fail(f"{port_rule} must precede the generic UDP gate")

local_direct = {
    "IP-CIDR,224.0.0.251/32,DIRECT,no-resolve",
    "IP-CIDR,239.255.255.250/32,DIRECT,no-resolve",
    "IP-CIDR6,ff02::fb/128,DIRECT,no-resolve",
    "IP-CIDR6,ff02::c/128,DIRECT,no-resolve",
    "IP-CIDR,192.168.0.0/16,DIRECT,no-resolve",
    "IP-CIDR,10.0.0.0/8,DIRECT,no-resolve",
    "IP-CIDR,172.16.0.0/12,DIRECT,no-resolve",
    "IP-CIDR,127.0.0.0/8,DIRECT,no-resolve",
    "IP-CIDR,169.254.0.0/16,DIRECT,no-resolve",
    "IP-CIDR6,::1/128,DIRECT,no-resolve",
    "IP-CIDR6,fc00::/7,DIRECT,no-resolve",
    "IP-CIDR6,fe80::/10,DIRECT,no-resolve",
    "DOMAIN-SUFFIX,local,DIRECT",
    "DOMAIN,localhost,DIRECT",
    "DOMAIN,sub.store,DIRECT",
}
actual_direct = {line for line in rules if target_of_rule(line) == "DIRECT"}
if actual_direct != local_direct:
    fail(f"unexpected literal DIRECT rules: {sorted(actual_direct ^ local_direct)}")

apple_rules = [line for line in rules if target_of_rule(line) == "Apple"]
domestic_rules = [line for line in rules if target_of_rule(line) == "Domestic"]
if len(apple_rules) != 166:
    fail(f"expected 166 embedded Apple rules, got {len(apple_rules)}")
if len(domestic_rules) != 882:
    fail(f"expected 882 embedded Domestic rules, got {len(domestic_rules)}")
if any(line.startswith(("USER-AGENT,", "IP-ASN,")) for line in apple_rules + domestic_rules):
    fail("broad USER-AGENT/IP-ASN direct rule remains")

for forbidden_domain in (
    "dns.pub",
    "doh.pub",
    "dot.pub",
    "alibabadns.com",
    "alidns.com",
    "bdydns.com",
    "bytednsdoc.com",
    "dns.la",
    "dnspod.cn",
    "dnspod.com",
    "dnsv1.com",
    "jomodns.com",
    "smtcdns.net",
):
    if any(f",{forbidden_domain}," in f",{line}," for line in apple_rules + domestic_rules):
        fail(f"DNS service remains direct: {forbidden_domain}")

for forbidden_direct in (
    "api.goodnotescloud.com",
    "fileball.app",
    "pianyuan.org",
    "google.com",
    "googleapis.com",
    "gvt1.com",
):
    if any(forbidden_direct in line for line in domestic_rules):
        fail(f"foreign/ambiguous item remains Domestic: {forbidden_direct}")

# Reconstruct the 22 proxy/reject sources at the pinned local commit and prove
# that the flat iOS rules match exactly after first-match duplicate elimination.
service_sources = [
    ("Ads_Custom_Extra.list", "AdBlock"),
    ("ChatGPT.list", "ChatGPT"),
    ("Claude.list", "Claude"),
    ("Gemini.list", "Gemini"),
    ("YouTube.list", "YouTube"),
    ("Netflix.list", "NETFLIX"),
    ("Disney.list", "Disney+"),
    ("HBO.list", "HBO"),
    ("PrimeVideo.list", "PrimeVideo"),
    ("Emby.list", "Emby"),
    ("TikTok.list", "TikTok"),
    ("Bahamut.list", "Bahamut"),
    ("BiliBiliIntl.list", "Streaming"),
    ("Spotify.list", "Spotify"),
    ("ProxyMedia.list", "Streaming"),
    ("Telegram.list", "Telegram"),
    ("Github.list", "GitHub"),
    ("Twitter.list", "X"),
    ("Google.list", "Google"),
    ("OneDrive.list", "Microsoft"),
    ("Microsoft.list", "Microsoft"),
    ("Game.list", "Games"),
]


def add_policy(rule: str, policy: str) -> str:
    fields = [part.strip() for part in rule.split(",")]
    if fields[-1].lower() == "no-resolve":
        fields.insert(-1, policy)
    else:
        fields.append(policy)
    return ",".join(fields)


expected_service: list[str] = []
seen_conditions: set[str] = set()
source_count = 0
for filename, policy in service_sources:
    source_path = REPO / "Rules" / filename
    if not source_path.is_file():
        fail(f"embedded service source is missing: {filename}")
    for raw in source_path.read_text(encoding="utf-8").splitlines():
        condition = raw.strip()
        if not condition or condition.startswith("#"):
            continue
        source_count += 1
        if condition in seen_conditions:
            continue
        seen_conditions.add(condition)
        if policy != "AdBlock" and reaches_direct(policy):
            fail(f"embedded service source can reach DIRECT: {filename} -> {policy}")
        expected_service.append(add_policy(condition, policy))

service_begin = rules.index("DEST-PORT,8853,REJECT") + 1
service_end = rules.index("PROTOCOL,STUN,Proxy")
actual_service = rules[service_begin:service_end]
if source_count != 4637 or len(expected_service) != 4483:
    fail(f"unexpected pinned service source totals: {len(expected_service)}/{source_count}")
if actual_service != expected_service:
    fail("embedded proxy/reject service rules no longer match pinned Rules sources")
if any(line.startswith(("RULE-SET,", "DOMAIN-SET,")) for line in rules):
    fail("strict profile must not download any external rule resource")

for forbidden_section in ("[Script]", "[MITM]", "[URL Rewrite]", "[Header Rewrite]", "[Body Rewrite]"):
    if forbidden_section in text:
        fail(f"unexpected active surface: {forbidden_section}")

max_line = max(len(line) for line in lines)
sha256 = hashlib.sha256(PROFILE.read_bytes()).hexdigest()
print("PASS: Surge-Stable-Fail-Closed-R10.1.conf")
print(f"sections={len(sections)} groups={len(groups)} rules={len(rules)}")
print(f"embedded_service={len(actual_service)}/{source_count} embedded_apple={len(apple_rules)} embedded_domestic={len(domestic_rules)}")
print(f"direct_groups={','.join(sorted(direct_groups))} max_line={max_line}")
print(f"sha256={sha256}")
