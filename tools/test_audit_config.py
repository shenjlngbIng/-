#!/usr/bin/env python3
"""Mutation tests for the R12 configuration auditor."""
from __future__ import annotations

import subprocess
import sys
import tempfile
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

mutations = {
    "final_open": ("\nFINAL,Final,dns-failed\n", "\nFINAL,DIRECT\n"),
    "telegram_direct": (
        "\nRULE-SET,https://raw.githubusercontent.com/shenjlngbIng/-/main/Rules/Telegram.list,Telegram\n",
        "\nRULE-SET,https://raw.githubusercontent.com/shenjlngbIng/-/main/Rules/Telegram.list,DIRECT\n",
    ),
    "apns_direct": (
        "\nRULE-SET,https://raw.githubusercontent.com/shenjlngbIng/-/main/Rules/APNs.list,ApplePush\n",
        "\nRULE-SET,https://raw.githubusercontent.com/shenjlngbIng/-/main/Rules/APNs.list,DIRECT\n",
    ),
    "capture_apns": ("\ninclude-apns = true\n", "\ninclude-apns = false\n"),
    "capture_all": ("\ninclude-all-networks = true\n", "\ninclude-all-networks = false\n"),
    "encrypted_dns_follow": (
        "\nencrypted-dns-follow-outbound-mode = false\n",
        "\nencrypted-dns-follow-outbound-mode = true\n",
    ),
    "dns_server": (
        "\ndns-server = 223.5.5.5, 223.6.6.6\n",
        "\ndns-server = system, 223.5.5.5, 119.29.29.29\n",
    ),
    "encrypted_dns_server": (
        "\nencrypted-dns-server = https://dns.alidns.com/dns-query, tls://dns.alidns.com\n",
        "\nencrypted-dns-server = https://1.1.1.1/dns-query, https://9.9.9.9/dns-query\n",
    ),
    "dns_bootstrap": (
        "dns.alidns.com = 223.5.5.5",
        "dns.alidns.com = 1.1.1.1",
    ),
    "test_timeout": ("\ntest-timeout = 8\n", "\ntest-timeout = 5\n"),
    "proxy_default": ("\nProxy = select, AllServer,", "\nProxy = select, HongKong,"),
    "allserver_mode": ("\nAllServer = fallback,", "\nAllServer = select,"),
    "public_subscription": (
        "policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL",
        "policy-path=https://private.example/subscription",
    ),
    "dns_direct": (
        "\nPROTOCOL,DOH,EncryptedDNS\n",
        "\nPROTOCOL,DOH,DIRECT\n",
    ),
    "unsupported_protocol": (
        "\nPROTOCOL,DOH,EncryptedDNS\n",
        "\nPROTOCOL,DNS,EncryptedDNS\n",
    ),
    "runtime_ruleset": (
        "\nFINAL,Final,dns-failed\n",
        "\nRULE-SET,https://example.invalid/a.list,Proxy\nFINAL,Final,dns-failed\n",
    ),
    "remote_host": (
        "https://raw.githubusercontent.com/shenjlngbIng/-/main/Rules/ChatGPT.list",
        "https://example.invalid/ChatGPT.list",
    ),
    "remote_http": (
        "https://raw.githubusercontent.com/shenjlngbIng/-/main/Rules/ChatGPT.list",
        "http://raw.githubusercontent.com/shenjlngbIng/-/main/Rules/ChatGPT.list",
    ),
}

for name, (old, new) in mutations.items():
    assert old in BASE, f"mutation anchor missing: {name}"
    result = run(BASE.replace(old, new, 1))
    assert result.returncode != 0, f"mutation unexpectedly passed: {name}"

print(f"PASS mutations={len(mutations)}")
