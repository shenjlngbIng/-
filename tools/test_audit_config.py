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


def main() -> int:
    baseline = PROFILE.read_text(encoding="utf-8-sig")
    result = audit(baseline)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        print("FAIL: baseline profile did not pass its auditor", file=sys.stderr)
        return 1

    cases = {
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
