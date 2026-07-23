#!/usr/bin/env python3
"""Mutation regression tests for the R10.1 configuration auditor."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
AUDITOR = ROOT / "tools" / "audit_config.py"
SUBSCRIPTION_NOTE = "# 【订阅地址填写处】将下一行占位链接替换为 Sub-Store 转换后的订阅链接"
PUBLIC_POLICY_PATH = "https://example.invalid/REPLACE_WITH_SUB_STORE_URL"


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise AssertionError(f"mutation anchor must occur once: {old!r}")
    return source.replace(old, new, 1)


def swap_once(source: str, first: str, second: str) -> str:
    if source.count(first) != 1 or source.count(second) != 1:
        raise AssertionError("swap anchors must occur once")
    marker = "__R10_AUDIT_SWAP__"
    return source.replace(first, marker, 1).replace(second, first, 1).replace(marker, second, 1)


baseline = PROFILE.read_text(encoding="utf-8")
cases = {
    "subscription note removed": replace_once(
        baseline,
        SUBSCRIPTION_NOTE,
        "# Sub-Store",
    ),
    "final direct fallback": replace_once(
        baseline,
        "Final = select, Proxy, no-alert=0, hidden=0, include-all-proxies=0",
        "Final = select, DIRECT, Proxy, no-alert=0, hidden=0, include-all-proxies=0",
    ),
    "duplicate policy path": replace_once(
        baseline,
        "AllServer = select, Fail-Closed,",
        "AllServer = select, Fail-Closed, policy-path=https://example.com/nodes,",
    ),
    "public subscription leak": replace_once(
        baseline,
        PUBLIC_POLICY_PATH,
        "https://example.com/private-subscription-token",
    ),
    "policy path removed": replace_once(
        baseline,
        f"policy-path={PUBLIC_POLICY_PATH}, ",
        "",
    ),
    "renamed direct proxy": replace_once(
        baseline,
        "Fail-Closed = http, 127.0.0.1, 1",
        "Fail-Closed = direct",
    ),
    "APNs domain direct": replace_once(
        baseline,
        "DOMAIN-SUFFIX,push.apple.com,Proxy",
        "DOMAIN-SUFFIX,push.apple.com,Apple",
    ),
    "APNs IPv6 direct": replace_once(
        baseline,
        "IP-CIDR6,2620:149:a44::/48,Proxy,no-resolve",
        "IP-CIDR6,2620:149:a44::/48,Apple,no-resolve",
    ),
    "UDP gate after direct": swap_once(
        baseline,
        "PROTOCOL,UDP,Proxy",
        "DOMAIN,api.smoot.apple.cn,Apple",
    ),
    "UDP unsupported direct": replace_once(
        baseline,
        "udp-policy-not-supported-behaviour = REJECT",
        "udp-policy-not-supported-behaviour = DIRECT",
    ),
    "known DoH direct": replace_once(
        baseline,
        "DOMAIN,doh.360.cn,Proxy",
        "DOMAIN,doh.360.cn,Domestic",
    ),
    "system DNS fallback": replace_once(
        baseline,
        "dns-server = 223.5.5.5, 119.29.29.29",
        "dns-server = system, 223.5.5.5, 119.29.29.29",
    ),
    "mutable SYSTEM direct": replace_once(
        baseline,
        "FINAL,Final,dns-failed",
        "RULE-SET,SYSTEM,Apple\nFINAL,Final,dns-failed",
    ),
    "remote resource restored": replace_once(
        baseline,
        "FINAL,Final,dns-failed",
        "RULE-SET,https://example.com/direct.list,Domestic\nFINAL,Final,dns-failed",
    ),
    "broad UA direct": replace_once(
        baseline,
        "FINAL,Final,dns-failed",
        "USER-AGENT,WeChat*,Domestic\nFINAL,Final,dns-failed",
    ),
    "all networks forced": replace_once(
        baseline,
        "include-all-networks = false",
        "include-all-networks = true",
    ),
    "cellular services forced": replace_once(
        baseline,
        "include-cellular-services = false",
        "include-cellular-services = true",
    ),
    "AI capability labels excluded from Singapore": replace_once(
        baseline,
        "policy-regex-filter=(?i)^(?!.*(?:专用|專用|解锁|解鎖)).*(?:新加坡|",
        "policy-regex-filter=(?i)^(?!.*(?:Gemini|GPT|ChatGPT|Claude|OpenAI|专用|專用|解锁|解鎖)).*(?:新加坡|",
    ),
    "automatic suspension": replace_once(
        baseline,
        "auto-suspend = false",
        "auto-suspend = true",
    ),
    "ICMP leak": replace_once(
        baseline,
        "icmp-forwarding = false",
        "icmp-forwarding = true",
    ),
}

baseline_result = subprocess.run(
    [sys.executable, str(AUDITOR), str(PROFILE)],
    capture_output=True,
    text=True,
    check=False,
)
if baseline_result.returncode != 0:
    raise AssertionError(baseline_result.stderr or baseline_result.stdout)

with tempfile.TemporaryDirectory() as directory:
    candidate = Path(directory) / "candidate.conf"
    for name, mutation in cases.items():
        candidate.write_text(mutation, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(AUDITOR), str(candidate), str(ROOT)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            raise AssertionError(f"auditor accepted mutation: {name}")
        print(f"PASS rejected: {name}")

print(f"PASS: baseline + {len(cases)} security mutations")
