#!/usr/bin/env python3
"""Embed the audited runtime snapshots into the Surge profile deterministically."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


RULESET_FILES = {
    "RS_Ads_Custom_Extra": "Ads_Custom_Extra.list",
    "RS_Bahamut": "Bahamut.list",
    "RS_BiliBiliIntl": "BiliBiliIntl.list",
    "RS_ChatGPT": "ChatGPT.list",
    "RS_Claude": "Claude.list",
    "RS_Disney": "Disney.list",
    "RS_Emby": "Emby.list",
    "RS_Game": "Game.list",
    "RS_Gemini": "Gemini.list",
    "RS_Github": "Github.list",
    "RS_Google": "Google.list",
    "RS_HBO": "HBO.list",
    "RS_Microsoft": "Microsoft.list",
    "RS_Netflix": "Netflix.list",
    "RS_OneDrive": "OneDrive.list",
    "RS_PrimeVideo": "PrimeVideo.list",
    "RS_ProxyMedia": "ProxyMedia.list",
    "RS_Reject": "Reject.list",
    "RS_Spotify": "Spotify.list",
    "RS_TikTok": "TikTok.list",
    "RS_Twitter": "Twitter.list",
    "RS_YouTube": "YouTube.list",
}
LEGACY_RULESET_ALIASES = {
    "RS_Ads_SukkaW_Extra": "RS_Ads_Custom_Extra",
}
FILE_TO_RULESET = {filename: name for name, filename in RULESET_FILES.items()}
MANAGED_SECTION = re.compile(r"^\[Ruleset (RS_[^]]+)\]$")
BUILD_LINE = re.compile(r"(?m)^# 构建: .+$")
GENERATED_PREAMBLE_LINES = (
    "# 运行时规则已内嵌；不再依赖 GitHub、jsDelivr、TLS 或外部规则缓存",
    "# 下列内容由构建流程从本地快照与固定上游提交合并、过滤、去重后生成",
)
REMOVABLE_PREAMBLE_LINES = {
    *GENERATED_PREAMBLE_LINES,
    "# 下列内容由 tools/embed_runtime_rules.py 从 Rules/ 的固定快照生成",
}


def active_lines(path: Path) -> list[str]:
    return [
        line
        for raw in path.read_text(encoding="utf-8-sig").splitlines()
        if (line := raw.strip()) and not line.startswith(("#", ";", "//"))
    ]


def strip_managed_sections(lines: list[str]) -> list[str]:
    managed = set(RULESET_FILES) | set(LEGACY_RULESET_ALIASES)
    result: list[str] = []
    skipping = False
    for line in lines:
        if line in REMOVABLE_PREAMBLE_LINES:
            continue
        if line.startswith("[") and line.endswith("]"):
            match = MANAGED_SECTION.fullmatch(line.strip())
            skipping = bool(match and match.group(1) in managed)
            if skipping:
                continue
        if not skipping:
            result.append(line)
    return result


def replace_rule_references(lines: list[str]) -> list[str]:
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        fields = [field.strip() for field in stripped.split(",")]
        if len(fields) >= 3 and fields[0].upper() == "RULE-SET":
            if "://" in fields[1]:
                filename = Path(unquote(urlsplit(fields[1]).path)).name
                ruleset = FILE_TO_RULESET.get(filename)
                if ruleset:
                    fields[1] = ruleset
                    line = ",".join(fields)
            elif fields[1] in LEGACY_RULESET_ALIASES:
                fields[1] = LEGACY_RULESET_ALIASES[fields[1]]
                line = ",".join(fields)
        result.append(line)
    return result


def provenance(root: Path) -> tuple[str, dict[str, dict[str, object]]]:
    lock_path = root / "Rules" / "upstreams.lock.json"
    data = json.loads(lock_path.read_text(encoding="utf-8"))
    upstream = dict(data["upstream"])
    services = {
        str(item["ruleset"]): dict(item)
        for raw in data["services"]
        if (item := dict(raw))
    }
    return str(upstream["commit"]), services


def ruleset_comments(
    ruleset: str, filename: str, commit: str, services: dict[str, dict[str, object]]
) -> list[str]:
    if ruleset == "RS_Ads_Custom_Extra":
        return [
            "# 固定快照: Rules/Ads_Custom_Extra.list（移动端自定义补充，非 SukkaW 官方 reject_extra 全量）"
        ]
    if ruleset in services:
        return [
            f"# 固定快照: 本地规则 + blackmatrix7@{commit}/{services[ruleset]['upstream_path']}",
            "# iOS 构建过滤: 不导入 PROCESS-NAME/宽泛新 IP-ASN/非唯一归属的共享平台；精确去重，域名优先、IP 后置",
        ]
    return [f"# 固定快照: Rules/{filename}"]


def build_rulesets(root: Path) -> list[str]:
    commit, services = provenance(root)
    blocks = [*GENERATED_PREAMBLE_LINES, ""]
    for ruleset, filename in RULESET_FILES.items():
        path = root / "Rules" / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        blocks.extend(
            [
                f"[Ruleset {ruleset}]",
                *ruleset_comments(ruleset, filename, commit, services),
                *active_lines(path),
                "",
            ]
        )
    return blocks


def finalize_build_id(text: str) -> str:
    match = BUILD_LINE.search(text)
    if not match:
        raise ValueError("build identifier is missing")
    current = match.group(0).removeprefix("# 构建: ")
    prefix = re.sub(r"-[0-9A-Fa-f]{8}$", "", current)
    if prefix == current and current.endswith("-PENDING"):
        prefix = current.removesuffix("-PENDING")
    normalized = BUILD_LINE.sub("# 构建: <normalized>", text, count=1)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8].upper()
    return BUILD_LINE.sub(f"# 构建: {prefix}-{digest}", text, count=1)


def render(profile: Path, root: Path) -> str:
    lines = profile.read_text(encoding="utf-8-sig").splitlines()
    lines = replace_rule_references(strip_managed_sections(lines))
    try:
        rule_index = lines.index("[Rule]")
    except ValueError as exc:
        raise ValueError(f"[Rule] section not found: {profile}") from exc
    prefix = lines[:rule_index]
    while prefix and not prefix[-1].strip():
        prefix.pop()
    output = prefix + [""] + build_rulesets(root) + lines[rule_index:]
    text = "\n".join(output).rstrip() + "\n"
    return finalize_build_id(text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", nargs="?", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parent.parent
    profile = args.profile or root / "Surge.conf"
    try:
        output = render(profile, root)
        current = profile.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.check:
        if current != output:
            print(f"ERROR: generated profile is stale: {profile}", file=sys.stderr)
            return 1
        print(f"PASS: generated profile is current: {profile}")
        return 0
    profile.write_text(output, encoding="utf-8", newline="\n")
    print(f"PASS: embedded {len(RULESET_FILES)} rule snapshots into {profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
