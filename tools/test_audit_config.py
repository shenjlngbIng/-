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
        "\nDOMAIN-SUFFIX,t.me,Telegram\n",
        "\nDOMAIN-SUFFIX,t.me,DIRECT\n",
    ),
    "apns_direct": (
        "\nDOMAIN-SUFFIX,push.apple.com,ApplePush\n",
        "\nDOMAIN-SUFFIX,push.apple.com,DIRECT\n",
    ),
    "capture_apns": ("\ninclude-apns = true\n", "\ninclude-apns = false\n"),
    "capture_all": ("\ninclude-all-networks = true\n", "\ninclude-all-networks = false\n"),
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
}

for name, (old, new) in mutations.items():
    assert old in BASE, f"mutation anchor missing: {name}"
    result = run(BASE.replace(old, new, 1))
    assert result.returncode != 0, f"mutation unexpectedly passed: {name}"

print(f"PASS mutations={len(mutations)}")
