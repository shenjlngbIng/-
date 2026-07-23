#!/usr/bin/env python3
"""Regenerate R10's embedded service and direct-allowlist rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SERVICE_LAYOUT = [
    (
        "# 小型广告补充；大型 Reject 与 SukkaW 域名表默认不加载",
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
        "# 流媒体与服务",
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
        "# 其他境外服务",
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
SERVICE_START = SERVICE_LAYOUT[0][0]
SERVICE_END = "# 服务专用策略之后、所有互联网直连之前封闭 UDP；不支持 UDP 的节点直接拒绝"
DIRECT_START = "# 直连敏感规则固定内嵌，避免远程更新把未知流量引入 DIRECT"
DIRECT_END = "# 境外、未知、未解析成功的 IPv4/IPv6 最终均进入 Proxy"

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


def add_policy(rule: str, policy: str) -> str:
    fields = [part.strip() for part in rule.split(",")]
    if fields[-1].lower() == "no-resolve":
        fields.insert(-1, policy)
    else:
        fields.append(policy)
    return ",".join(fields)


def lock_data(root: Path) -> tuple[str, dict[str, dict[str, object]]]:
    data = json.loads((root / "Rules" / "r10.lock.json").read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise ValueError("unsupported Rules/r10.lock.json schema")
    files = {str(item["file"]): dict(item) for item in data["files"]}
    return str(data["source_commit"]), files


def build_service_block(root: Path) -> list[str]:
    commit, locked = lock_data(root)
    seen: set[str] = set()
    output: list[str] = []
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
            if item.get("active_entries") != len(source) or item.get("embedded_entries") != len(kept):
                raise ValueError(f"locked count mismatch for {filename}")
            output.append(
                f"# 内嵌 {filename}: {len(kept)}/{len(source)} 条，策略 {policy}，来源提交 {commit}"
            )
            output.extend(add_policy(rule, policy) for rule in kept)
    output.append("")
    return output


def build_direct_block(root: Path) -> list[str]:
    commit, locked = lock_data(root)
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
        f"# AppleCN: {len(apple)} 条，来源提交 {commit}",
        *[add_policy(rule, "Apple") for rule in apple],
        "",
        f"# WeChat: {len(wechat)} 条；删除 2 条 USER-AGENT 与 1 条宽泛 IP-ASN",
        *[add_policy(rule, "Domestic") for rule in wechat],
        "",
        f"# Direct 精选: {len(direct)} 条；仅保留明确国内目标",
        *[add_policy(rule, "Domestic") for rule in direct],
        "",
        f"# ChinaDomain: {len(china)} 条；另删除 3 条 USER-AGENT、13 条 DNS 服务域名与 4 条重复规则",
        *[add_policy(rule, "Domestic") for rule in china],
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
    lines = replace_block(lines, SERVICE_START, SERVICE_END, build_service_block(root))
    lines = replace_block(lines, DIRECT_START, DIRECT_END, build_direct_block(root))
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
    print(f"PASS: regenerated R10 embedded rules in {profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
