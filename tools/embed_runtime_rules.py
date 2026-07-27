#!/usr/bin/env python3
"""Regenerate R10.2's embedded domestic, service, and protocol rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SERVICE_LAYOUT = [
    (
        "# 广告补充",
        [("Ads_Custom_Extra.list", "AdBlock")],
    ),
    (
        "# AI",
        [
            ("ChatGPT.list", "ChatGPT"),
            ("Claude.list", "Claude"),
            ("Gemini.list", "Gemini"),
        ],
    ),
    (
        "# 流媒体",
        [
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
        ],
    ),
    ("# Telegram", [("Telegram.list", "Telegram")]),
    (
        "# 境外服务",
        [
            ("Github.list", "GitHub"),
            ("Twitter.list", "X"),
            ("Google.list", "Google"),
            ("OneDrive.list", "Microsoft"),
            ("Microsoft.list", "Microsoft"),
            ("Game.list", "Games"),
        ],
    ),
]
RUNTIME_START = "# 运行时规则（固定快照）"
RUNTIME_END = "# 兜底：境外/未知/解析失败走代理"
UDP_HEADING = "# UDP/STUN/QUIC：已知国内/服务先分类，未知流量代理"
DIRECT_START = "# 直连白名单（固定快照）"

# These exact game endpoints are otherwise swallowed by earlier, broad Netflix
# cloud CIDRs. Keep only the four precise exceptions ahead of the service block;
# their original Game.list occurrences are removed by first-match de-duplication.
SERVICE_PRIORITY_OVERRIDES = [
    ("Game.list", "IP-CIDR,34.220.160.16/32,no-resolve", "Games"),
    ("Game.list", "IP-CIDR,52.13.150.128/32,no-resolve", "Games"),
    ("Game.list", "IP-CIDR,52.13.42.120/32,no-resolve", "Games"),
    ("Game.list", "IP-CIDR,52.50.131.212/32,no-resolve", "Games"),
]

DIRECT_EXTRA_ALLOW = {
    "DOMAIN,fairplay.l.qq.com",
    "DOMAIN,livew.l.qq.com",
    "DOMAIN,vd.l.qq.com",
    "DOMAIN,vi.l.qq.com",
    "DOMAIN-SUFFIX,goodnotesapp.com.cn",
}
DNS_SENSITIVE_DOMESTIC = {
    "DOMAIN,dns.pub",
    "DOMAIN,doh.pub",
    "DOMAIN,dot.pub",
    "DOMAIN-SUFFIX,alibabadns.com",
    "DOMAIN-SUFFIX,alidns.com",
    "DOMAIN-SUFFIX,bdydns.com",
    "DOMAIN-SUFFIX,bytednsdoc.com",
    "DOMAIN-SUFFIX,dns.la",
    "DOMAIN-SUFFIX,dnspod.cn",
    "DOMAIN-SUFFIX,dnspod.com",
    "DOMAIN-SUFFIX,dnsv1.com",
    "DOMAIN-SUFFIX,jomodns.com",
    "DOMAIN-SUFFIX,smtcdns.net",
}


def active_rules(root: Path, filename: str) -> list[str]:
    path = root / "Rules" / filename
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
    ]


def add_policy(rule: str, policy: str, *, extended_matching: bool = False) -> str:
    fields = [part.strip() for part in rule.split(",")]
    if fields[-1].lower() == "no-resolve":
        fields.insert(-1, policy)
    else:
        fields.append(policy)
    if extended_matching and fields[0] in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
        fields.append("extended-matching")
    return ",".join(fields)


def lock_data(root: Path) -> tuple[str, dict[str, dict[str, object]]]:
    data = json.loads((root / "Rules" / "r10.lock.json").read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise ValueError("unsupported Rules/r10.lock.json schema")
    files = {str(item["file"]): dict(item) for item in data["files"]}
    return str(data["source_commit"]), files


def build_service_block(root: Path) -> list[str]:
    _, locked = lock_data(root)
    seen: set[str] = set()
    priority_count: dict[str, int] = {}
    output: list[str] = [
        "# 服务精确优先级修正",
        "# Games 精确 IP 先于 Netflix 公有云大网段",
    ]
    for filename, rule, policy in SERVICE_PRIORITY_OVERRIDES:
        source = active_rules(root, filename)
        item = locked.get(filename)
        if item is None:
            raise ValueError(f"missing R10 lock entry: {filename}")
        if item.get("policy") != policy:
            raise ValueError(f"locked policy mismatch for {filename}")
        if rule not in source:
            raise ValueError(f"service priority override is missing from {filename}: {rule}")
        if rule in seen:
            raise ValueError(f"duplicate service priority override: {rule}")
        seen.add(rule)
        priority_count[filename] = priority_count.get(filename, 0) + 1
        output.append(add_policy(rule, policy))
    output.append("")

    for group_index, (heading, items) in enumerate(SERVICE_LAYOUT):
        if group_index:
            output.append("")
        output.append(heading)
        for filename, policy in items:
            source = active_rules(root, filename)
            kept: list[str] = []
            for rule in source:
                if rule in seen:
                    continue
                seen.add(rule)
                kept.append(rule)
            item = locked.get(filename)
            if item is None:
                raise ValueError(f"missing R10 lock entry: {filename}")
            if item.get("policy") != policy:
                raise ValueError(f"locked policy mismatch for {filename}")
            emitted = len(kept) + priority_count.get(filename, 0)
            if item.get("active_entries") != len(source) or item.get("embedded_entries") != emitted:
                raise ValueError(f"locked count mismatch for {filename}")
            output.append(f"# {filename} · {len(kept)}/{len(source)} · {policy}")
            output.extend(add_policy(rule, policy) for rule in kept)
    output.append("")
    return output


def build_direct_block(root: Path) -> list[str]:
    _, locked = lock_data(root)
    apple = active_rules(root, "AppleCN.list")
    wechat = [
        rule
        for rule in active_rules(root, "WeChat.list")
        if not rule.startswith("USER-AGENT,") and not rule.startswith("IP-ASN,")
    ]
    direct = [
        rule for rule in active_rules(root, "Direct.list") if rule in DIRECT_EXTRA_ALLOW
    ]
    if set(direct) != DIRECT_EXTRA_ALLOW:
        raise ValueError("Direct.list no longer contains the complete R10 allowlist")
    china = [
        rule
        for rule in active_rules(root, "ChinaDomain.list")
        if not rule.startswith("USER-AGENT,") and rule not in DNS_SENSITIVE_DOMESTIC
    ]
    earlier_domestic = set(wechat) | set(direct)
    china = [rule for rule in china if rule not in earlier_domestic]

    generated = {
        "AppleCN.list": apple,
        "WeChat.list": wechat,
        "Direct.list": direct,
        "ChinaDomain.list": china,
    }
    for filename, rules in generated.items():
        item = locked.get(filename)
        if item is None or item.get("embedded_entries") != len(rules):
            raise ValueError(f"locked direct count mismatch for {filename}")

    return [
        DIRECT_START,
        f"# AppleCN · {len(apple)} · Apple",
        *[add_policy(rule, "Apple", extended_matching=True) for rule in apple],
        "",
        f"# WeChat · {len(wechat)} · Domestic（剔除宽泛 UA/ASN）",
        *[add_policy(rule, "Domestic", extended_matching=True) for rule in wechat],
        "",
        f"# Direct · {len(direct)} · Domestic（精选）",
        *[add_policy(rule, "Domestic", extended_matching=True) for rule in direct],
        "",
        f"# ChinaDomain · {len(china)} · Domestic（剔除宽泛/敏感项）",
        *[add_policy(rule, "Domestic", extended_matching=True) for rule in china],
        "",
    ]


def build_runtime_block(root: Path) -> list[str]:
    return [
        RUNTIME_START,
        "",
        *build_direct_block(root),
        *build_service_block(root),
        "# 中国大陆 IP 兜底；未知国内域名由本地解析后判定",
        "GEOIP,CN,Domestic",
        "",
        UDP_HEADING,
        "PROTOCOL,STUN,Proxy",
        "PROTOCOL,QUIC,Proxy",
        "PROTOCOL,UDP,Proxy",
        "",
    ]


def replace_block(lines: list[str], start: str, end: str, replacement: list[str]) -> list[str]:
    if lines.count(start) != 1 or lines.count(end) != 1:
        raise ValueError(f"profile anchors are missing or duplicated: {start!r}, {end!r}")
    start_index = lines.index(start)
    end_index = lines.index(end)
    if start_index >= end_index:
        raise ValueError(f"profile anchors are out of order: {start!r}, {end!r}")
    return lines[:start_index] + replacement + lines[end_index:]


def render(profile: Path, root: Path) -> str:
    lines = profile.read_text(encoding="utf-8-sig").splitlines()
    lines = replace_block(lines, RUNTIME_START, RUNTIME_END, build_runtime_block(root))
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", nargs="?", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    profile = (args.profile or root / "Surge.conf").resolve()
    try:
        current = profile.read_text(encoding="utf-8-sig")
        generated = render(profile, root)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.check:
        if current != generated:
            print(f"ERROR: generated profile is stale: {profile}", file=sys.stderr)
            return 1
        print(f"PASS: generated profile is current: {profile}")
        return 0
    profile.write_text(generated, encoding="utf-8", newline="\n")
    print(f"PASS: regenerated R10.2 embedded rules in {profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
