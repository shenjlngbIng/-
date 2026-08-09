#!/usr/bin/env python3
"""Convert the R12 profile from embedded rules to repository-hosted RULE-SETs.

The repository remains the source of truth for the curated rule snapshots.  The
Surge profile loads those snapshots at runtime through the repository's Raw URL.
This keeps the hand-reviewed exclusions and ordering while allowing rule files
to be updated without rebuilding the profile text.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
REMOTE_BASE = "https://raw.githubusercontent.com/shenjlngbIng/-/main/Rules/"

# Keep this order aligned with the original embedded profile.  Earlier rules
# intentionally win over broader domestic/geoip fallbacks later in the file.
REMOTE_RULES: tuple[tuple[str, str, str], ...] = (
    ("AppleCN.list", "AppleCN · Apple", "Apple"),
    ("WeChat.list", "WeChat · Domestic", "Domestic"),
    ("Direct.list", "Direct · Domestic", "Domestic"),
    ("Ads_Custom_Extra.list", "Ads_Custom_Extra · AdBlock", "AdBlock"),
    ("ChatGPT.list", "ChatGPT", "ChatGPT"),
    ("Claude.list", "Claude", "Claude"),
    ("Gemini.list", "Gemini", "Gemini"),
    ("YouTube.list", "YouTube", "YouTube"),
    ("Netflix.list", "Netflix", "NETFLIX"),
    ("Disney.list", "Disney+", "Disney+"),
    ("HBO.list", "HBO", "HBO"),
    ("PrimeVideo.list", "PrimeVideo", "PrimeVideo"),
    ("Emby.list", "Emby", "Emby"),
    ("TikTok.list", "TikTok", "TikTok"),
    ("Bahamut.list", "Bahamut", "Bahamut"),
    ("BiliBiliIntl.list", "BiliBiliIntl · Streaming", "Streaming"),
    ("Spotify.list", "Spotify", "Spotify"),
    ("ProxyMedia.list", "ProxyMedia · Streaming", "Streaming"),
    ("Telegram.list", "Telegram", "Telegram"),
    ("Github.list", "Github", "GitHub"),
    ("Twitter.list", "Twitter", "X"),
    ("Google.list", "Google", "Google"),
    ("OneDrive.list", "OneDrive", "Microsoft"),
    ("Microsoft.list", "Microsoft", "Microsoft"),
    ("Game.list", "Game", "Games"),
    ("APNs.list", "APNs", "ApplePush"),
    ("ChinaDomain.list", "ChinaDomain · Domestic", "Domestic"),
)


def remote_line(filename: str, policy: str) -> str:
    return f"RULE-SET,{REMOTE_BASE}{filename},{policy}"


def render_remote_block() -> str:
    lines = [
        "# Repository-hosted remote rule sets",
        "# The Raw URLs point to the curated files in this repository.",
        "# Aegis-style modular security feeds are intentionally not enabled here",
        "# until their threat-intelligence sources are independently reviewed.",
        "",
        "# Apple / domestic precedence",
    ]
    filename, label, policy = REMOTE_RULES[25]
    lines[5:5] = ["# APNs", f"# {label}", remote_line(filename, policy), ""]
    for filename, label, policy in REMOTE_RULES[:3]:
        lines.append(f"# {label}")
        lines.append(remote_line(filename, policy))

    lines.extend(("", "# Advertising", f"# {REMOTE_RULES[3][1]}", remote_line(*REMOTE_RULES[3][::2])))

    lines.extend(("", "# Artificial intelligence"))
    for filename, label, policy in REMOTE_RULES[4:7]:
        lines.extend((f"# {label}", remote_line(filename, policy)))

    lines.extend(("", "# Streaming"))
    for filename, label, policy in REMOTE_RULES[7:18]:
        lines.extend((f"# {label}", remote_line(filename, policy)))

    lines.extend(("", "# International services"))
    for filename, label, policy in REMOTE_RULES[18:25]:
        lines.extend((f"# {label}", remote_line(filename, policy)))

    lines.extend(("", "# ChinaDomain is deliberately after international service sets."))
    filename, label, policy = REMOTE_RULES[26]
    lines.extend((f"# {label}", remote_line(filename, policy)))
    return "\n".join(lines)


def main() -> int:
    text = PROFILE.read_text(encoding="utf-8")
    marker = "# Embedded rules\n"
    if marker not in text:
        if "# Repository-hosted remote rule sets" in text:
            print("PASS: profile already uses repository-hosted remote rule sets")
            return 0
        raise SystemExit("embedded rule marker not found")

    before, after = text.split(marker, 1)
    tail_marker = "# China IP\n"
    if tail_marker not in after:
        raise SystemExit("China IP tail marker not found")
    _, tail = after.split(tail_marker, 1)

    before = before.replace(
        "# 未匹配流量进入 FINAL,Final,dns-failed",
        "# 远程规则集失效时仍进入 FINAL,Final,dns-failed；不静默直连",
    )
    apns_block = (
        "# APNs\n"
        "# APNs.list · 12/12 · ApplePush\n"
        "DOMAIN-SUFFIX,push.apple.com,ApplePush\n"
        "DOMAIN-SUFFIX,push-apple.com.akadns.net,ApplePush\n"
        "DOMAIN-SUFFIX,push-apple.com,ApplePush\n"
        "IP-CIDR,17.249.0.0/16,ApplePush,no-resolve\n"
        "IP-CIDR,17.252.0.0/16,ApplePush,no-resolve\n"
        "IP-CIDR,17.57.144.0/22,ApplePush,no-resolve\n"
        "IP-CIDR,17.188.128.0/18,ApplePush,no-resolve\n"
        "IP-CIDR,17.188.20.0/23,ApplePush,no-resolve\n"
        "IP-CIDR6,2620:149:a44::/48,ApplePush,no-resolve\n"
        "IP-CIDR6,2403:300:a42::/48,ApplePush,no-resolve\n"
        "IP-CIDR6,2403:300:a51::/48,ApplePush,no-resolve\n"
        "IP-CIDR6,2a01:b740:a42::/48,ApplePush,no-resolve\n\n"
    )
    before = before.replace(apns_block, "")
    before = before.replace(
        "Final = select, Proxy, no-alert=0, hidden=0, include-all-proxies=0",
        "Final = select, Proxy, REJECT, no-alert=0, hidden=0, include-all-proxies=0",
    )
    rendered = before + render_remote_block() + "\n\n# China IP\n" + tail
    if not rendered.endswith("\n"):
        rendered += "\n"
    PROFILE.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"updated {PROFILE}: remote_rules={len(REMOTE_RULES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
