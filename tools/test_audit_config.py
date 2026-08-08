#!/usr/bin/env python3
"""Mutation tests for the R12 configuration auditor."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "tools/audit_config.py"
BASE = (ROOT / "Surge.conf").read_text(encoding="utf-8")


def run(text: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        profile = Path(directory) / "Surge.conf"
        profile.write_text(text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(AUDIT), str(profile)],
            capture_output=True,
            text=True,
            check=False,
        )


assert run(BASE).returncode == 0, "baseline"


def group_line(name: str) -> str:
    for line in BASE.splitlines():
        if line.startswith(f"{name} = "):
            return line
    raise AssertionError(f"missing group: {name}")


regional_samples = {
    "HongKong": "🇭🇰香港-Gemini-IEPL",
    "TaiWan": "🇹🇼台湾-IEPL",
    "Japan": "🇯🇵日本-IEPL",
    "Singapore": "🇸🇬新加坡-Gemini-IEPL",
    "America": "🇺🇸美国-IEPL",
}
for group, sample in regional_samples.items():
    line = group_line(group)
    pattern = line.split("policy-regex-filter=", 1)[1].split(", tolerance=", 1)[0]
    assert re.search(pattern, sample), f"regional filter does not match sample: {group}"

mutations = {
    "final_open": ("\nFINAL,Final,dns-failed\n", "\nFINAL,DIRECT\n"),
    "telegram_direct": (
        "\nDOMAIN-SUFFIX,t.me,Telegram\n",
        "\nDOMAIN-SUFFIX,t.me,DIRECT\n",
    ),
    "apns_direct": (
        "\nDOMAIN-SUFFIX,push.apple.com,ApplePush\n",
        "\nDOMAIN-SUFFIX,push.apple.com,DIRECT\n",
    ),
    "capture_apns": ("\ninclude-apns = true\n", "\ninclude-apns = false\n"),
    "capture_all": ("\ninclude-all-networks = true\n", "\ninclude-all-networks = false\n"),
    "encrypted_dns_proxy_loop": (
        "\nencrypted-dns-follow-outbound-mode = false\n",
        "\nencrypted-dns-follow-outbound-mode = true\n",
    ),
    "domestic_dns_bootstrap": (
        "\ndns-server = 223.5.5.5, 114.114.114.114\n",
        "\ndns-server = 1.1.1.1, 9.9.9.9\n",
    ),
    "dns_direct": (
        "\nPROTOCOL,DOH,EncryptedDNS\n",
        "\nPROTOCOL,DOH,DIRECT\n",
    ),
    "china_before_ad": (
        "\nDOMAIN-KEYWORD,-ad.a.yximgs.com,AdBlock\n",
        "\nDOMAIN,acg.tv,Domestic,extended-matching\nDOMAIN-KEYWORD,-ad.a.yximgs.com,AdBlock\n",
    ),
    "allserver_import": (
        "include-all-proxies=true",
        "include-all-proxies=false",
    ),
    "allserver_remote_path": (
        "AllServer = fallback, Fail-Closed, policy-path=YOUR_SUBSTORE_SURGE_URL, update-interval=3600, interval=60, timeout=300, evaluate-before-use=true, no-alert=0, hidden=0, include-all-proxies=true",
        "AllServer = fallback, Fail-Closed, policy-path=https://example.invalid/sub, interval=60, timeout=300, evaluate-before-use=true, no-alert=0, hidden=0, include-all-proxies=true",
    ),
    "allserver_placeholder_removed": (
        "policy-path=YOUR_SUBSTORE_SURGE_URL, ",
        "",
    ),
    "substore_host_mapping": (
        "[Host]\n",
        "[Host]\nsub.store = 127.0.0.1\n",
    ),
    "runtime_ruleset": (
        "\nFINAL,Final,dns-failed\n",
        "\nRULE-SET,https://example.invalid/a.list,Proxy\nFINAL,Final,dns-failed\n",
    ),
}

for name, (old, new) in mutations.items():
    assert old in BASE, f"mutation anchor missing: {name}"
    result = run(BASE.replace(old, new, 1))
    assert result.returncode != 0, f"mutation unexpectedly passed: {name}"

print(f"PASS mutations={len(mutations)}")
