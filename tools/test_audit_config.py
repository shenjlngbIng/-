#!/usr/bin/env python3
"""Regression tests for fail-closed profile invariants."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
AUDITOR = ROOT / "tools" / "audit_config.py"
PROFILE = ROOT / "Surge.conf"


def audit(text: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        candidate = Path(directory) / "Surge.conf"
        candidate.write_text(text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(AUDITOR), str(candidate)],
            check=False,
            capture_output=True,
            text=True,
        )


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise AssertionError(f"fixture anchor must occur exactly once: {old!r}")
    return source.replace(old, new, 1)


def swap_once(source: str, first: str, second: str) -> str:
    if source.count(first) != 1 or source.count(second) != 1:
        raise AssertionError(f"swap anchors must occur exactly once: {first!r}, {second!r}")
    marker = "__SURGE_AUDIT_SWAP_MARKER__"
    if marker in source:
        raise AssertionError("swap marker unexpectedly appears in fixture")
    return source.replace(first, marker, 1).replace(second, first, 1).replace(marker, second, 1)


def main() -> int:
    baseline = PROFILE.read_text(encoding="utf-8-sig")
    result = audit(baseline)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        print("FAIL: baseline profile did not pass its auditor", file=sys.stderr)
        return 1

    build_line = next(
        line for line in baseline.splitlines() if line.startswith("# 构建: ")
    )
    tampered_build = build_line[:-1] + ("0" if build_line[-1] != "0" else "1")

    cases = {
        "minimum version metadata removed": replace_once(
            baseline,
            "# 最低版本: Surge iOS 5.14.6+\n",
            "",
        ),
        "service provenance metadata removed": replace_once(
            baseline,
            "# 来源与许可见 NOTICE.md；本次服务规则固定于 blackmatrix7@c00517ce10760a93728b241923a451dfa617be80（GPL-2.0）。\n",
            "",
        ),
        "build digest tampered": replace_once(
            baseline,
            build_line,
            tampered_build,
        ),
        "runtime policy subscription": replace_once(
            baseline,
            "policy-path=此处填入Sub-Store转换后的订阅链接",
            "policy-path=https://example.com/nodes",
        ),
        "Sub-Store placeholder comment removed": replace_once(
            baseline,
            "# 【Sub-Store 转换订阅地址填写处】只替换下方 policy-path 的中文占位文字\n",
            "",
        ),
        "Sub-Store bootstrap instruction removed": replace_once(
            baseline,
            "# 零静态节点冷启动：真实链接无“?”时追加 ?proxy=DIRECT；已有“?”时追加 &proxy=DIRECT\n",
            "",
        ),
        "Sub-Store policy-path placeholder removed": replace_once(
            baseline,
            ", policy-path=此处填入Sub-Store转换后的订阅链接, update-interval=0",
            "",
        ),
        "renamed direct policy": replace_once(
            baseline,
            "Fail-Closed = http, 127.0.0.1, 1\n",
            "Fail-Closed = http, 127.0.0.1, 1\n香港-1 = direct\n",
        ),
        "hostname proxy endpoint": replace_once(
            baseline,
            "Fail-Closed = http, 127.0.0.1, 1\n",
            "Fail-Closed = http, 127.0.0.1, 1\nNode = ss, example.com, 443, encrypt-method=aes-128-gcm, password=test\n",
        ),
        "APNs direct fallback policy": replace_once(
            baseline,
            "# 运行时规则已内嵌；不再依赖 GitHub、jsDelivr、TLS 或外部规则缓存\n",
            "Apple Push = select, DIRECT\n\n# 运行时规则已内嵌；不再依赖 GitHub、jsDelivr、TLS 或外部规则缓存\n",
        ),
        "APNs domain direct regression": replace_once(
            baseline,
            "DOMAIN-SUFFIX,push.apple.com,Proxy",
            "DOMAIN-SUFFIX,push.apple.com,Apple",
        ),
        "APNs IPv6 direct regression": replace_once(
            baseline,
            "IP-CIDR6,2620:149:a44::/48,Proxy,no-resolve",
            "IP-CIDR6,2620:149:a44::/48,Apple,no-resolve",
        ),
        "overbroad APNs Akamai match": replace_once(
            baseline,
            "DOMAIN-SUFFIX,push.apple.com,Proxy",
            "DOMAIN-SUFFIX,akadns.net,Proxy\nDOMAIN-SUFFIX,push.apple.com,Proxy",
        ),
        "APNs raw TCP exception removed": replace_once(
            baseline,
            "always-raw-tcp-hosts = 149.154.*, 91.108.*, *.push.apple.com:443, *push-apple.com.akadns.net:443, *.apple.com.edgekey.net:443",
            "always-raw-tcp-hosts = 149.154.*, 91.108.*",
        ),
        "UDP direct fallback": replace_once(
            baseline,
            "PROTOCOL,UDP,Proxy",
            "PROTOCOL,UDP,DIRECT",
        ),
        "encrypted DNS bootstrap removed": replace_once(
            baseline,
            "AND,((PROTOCOL,DOH),(DOMAIN,223.5.5.5)),DIRECT\n",
            "",
        ),
        "encrypted DNS bootstrap broadened": replace_once(
            baseline,
            "AND,((PROTOCOL,DOH),(DOMAIN,223.5.5.5)),DIRECT",
            "PROTOCOL,DOH,DIRECT",
        ),
        "mDNS IPv4 exception removed": replace_once(
            baseline,
            "IP-CIDR,224.0.0.251/32,DIRECT,no-resolve\n",
            "",
        ),
        "mDNS exception broadened": replace_once(
            baseline,
            "IP-CIDR,224.0.0.251/32,DIRECT,no-resolve",
            "IP-CIDR,224.0.0.0/24,DIRECT,no-resolve",
        ),
        "discovery exception follows multicast reject": swap_once(
            baseline,
            "IP-CIDR,224.0.0.251/32,DIRECT,no-resolve",
            "IP-CIDR,224.0.0.0/4,REJECT,no-resolve",
        ),
        "generic UDP fallback precedes LAN": swap_once(
            baseline,
            "IP-CIDR,10.0.0.0/8,DIRECT,no-resolve",
            "PROTOCOL,STUN,Proxy",
        ),
        "Google shadows YouTube": swap_once(
            baseline,
            "RULE-SET,RS_YouTube,YouTube,extended-matching",
            "RULE-SET,RS_Google,Google,extended-matching",
        ),
        "Microsoft shadows Game": swap_once(
            baseline,
            "RULE-SET,RS_Game,Games,extended-matching",
            "RULE-SET,RS_Microsoft,Microsoft,extended-matching",
        ),
        "legacy ad ruleset reference": replace_once(
            baseline,
            "RULE-SET,RS_Ads_Custom_Extra,AdBlock,extended-matching",
            "RULE-SET,RS_Ads_SukkaW_Extra,AdBlock,extended-matching",
        ),
        "top-level CN direct suffix": replace_once(
            baseline,
            "# Final\n",
            "DOMAIN-SUFFIX,cn,Domestic\n\n# Final\n",
        ),
        "CGNAT direct network": replace_once(
            baseline,
            "IP-CIDR,169.254.0.0/16,DIRECT,no-resolve",
            "IP-CIDR,100.64.0.0/10,DIRECT,no-resolve\nIP-CIDR,169.254.0.0/16,DIRECT,no-resolve",
        ),
        "extra DNS host mapping": replace_once(
            baseline,
            "sub.store = 127.0.0.1\n",
            "sub.store = 127.0.0.1\nproxy.example = server:223.5.5.5\n",
        ),
        "conditional IPv6 takeover": replace_once(
            baseline,
            "ipv6-vif = always",
            "ipv6-vif = auto",
        ),
        "automatic compatibility mode": replace_once(
            baseline,
            "compatibility-mode = 3",
            "compatibility-mode = 0",
        ),
        "unapproved smart group": replace_once(
            baseline,
            "Final = select, Proxy",
            "Final = smart, Proxy",
        ),
        "new direct-capable domain": replace_once(
            baseline,
            "# Final\n",
            "DOMAIN-SUFFIX,example.cn,Domestic\n\n# Final\n",
        ),
        "Sub-Store sent to remote proxy": replace_once(
            baseline,
            "DOMAIN,sub.store,DIRECT",
            "DOMAIN,sub.store,Proxy",
        ),
        "unapproved proxy type": replace_once(
            baseline,
            "Fail-Closed = http, 127.0.0.1, 1\n",
            "Fail-Closed = http, 127.0.0.1, 1\nNode = future-proxy, 192.0.2.1, 443\n",
        ),
        "weak Shadowsocks cipher": replace_once(
            baseline,
            "Fail-Closed = http, 127.0.0.1, 1\n",
            "Fail-Closed = http, 127.0.0.1, 1\nNode = ss, 192.0.2.1, 443, encrypt-method=aes-128-cfb, password=test\n",
        ),
        "weakened TLS hostname verification": replace_once(
            baseline,
            "Fail-Closed = http, 127.0.0.1, 1\n",
            "Fail-Closed = http, 127.0.0.1, 1\nNode = https, 192.0.2.1, 443, skip-common-name-verify=true\n",
        ),
        "policy group cycle": replace_once(
            baseline,
            "# 运行时规则已内嵌；不再依赖 GitHub、jsDelivr、TLS 或外部规则缓存\n",
            "Loop A = select, Loop B\nLoop B = select, Loop A\n\n# 运行时规则已内嵌；不再依赖 GitHub、jsDelivr、TLS 或外部规则缓存\n",
        ),
        "external runtime ruleset restored": replace_once(
            baseline,
            "RULE-SET,RS_ChatGPT,ChatGPT,extended-matching",
            "RULE-SET,https://example.com/ChatGPT.list,ChatGPT,extended-matching",
        ),
        "inline ruleset content changed": replace_once(
            baseline,
            "DOMAIN,bahamut.akamaized.net\n",
            "DOMAIN,changed-invalid.example\n",
        ),
        "inline ruleset section renamed": replace_once(
            baseline,
            "[Ruleset RS_Bahamut]",
            "[Ruleset RS_Bahamut_Unknown]",
        ),
        "SYSTEM ruleset bypasses Apple choice": replace_once(
            baseline,
            "RULE-SET,SYSTEM,Apple",
            "RULE-SET,SYSTEM,DIRECT",
        ),
    }

    missed: list[str] = []
    for name, candidate in cases.items():
        if audit(candidate).returncode == 0:
            missed.append(name)
    if missed:
        print(f"FAIL: auditor accepted forbidden mutations: {', '.join(missed)}", file=sys.stderr)
        return 1

    print(f"PASS: audit_config regression cases={len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
