#!/usr/bin/env python3
"""Validate local rule snapshots for the Surge iOS-only profile."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import re
import sys
from pathlib import Path
TWO_FIELD_TYPES = {
    "DOMAIN",
    "DOMAIN-KEYWORD",
    "DOMAIN-SUFFIX",
    "DOMAIN-WILDCARD",
    "USER-AGENT",
}
NO_RESOLVE_TYPES = {"IP-ASN", "IP-CIDR", "IP-CIDR6"}
BANNED_IOS_TYPES = {
    "PROCESS-NAME": "Surge iOS does not execute process-name rules",
    "URL-REGEX": "URL matching is excluded from this no-MITM mobile profile",
}
COUNT_HEADER = re.compile(r"^#\s*规则统计:\s*(\d+)\s*$")
RUNTIME_RULE_SHA256 = {
    "Ads_Custom_Extra.list": "71571e6b76fa0ce46902350bd394d76dbb8c62322a016534af592446ce469bc3",
    "Bahamut.list": "0b13d4544efaca1e7a2b205abda73a78d782450a885b9803d668ef072a4cb6b5",
    "BiliBiliIntl.list": "6972713a9cc71733590b8bb10bb73a28c39092f0a6c469324f90045b10ac92f0",
    "ChatGPT.list": "46c8e3b5ae1be413c7107d28689f09d251d987a2cf5250cb3c63847a33dbe866",
    "Claude.list": "53c5106b39756280f6ab9eca5aaba81d2472bf529c6c030d619f369c550bb3a5",
    "Disney.list": "9d676639f5e3a4e9f3b5d0e55d827978e00118b39b25276ccd190919103e500b",
    "Emby.list": "efdcd06070fdc944351694b8467707b6aa9aa0b5b5ccaa0720c3adb49a771246",
    "Game.list": "5d407cae765790d095a51b44476b94edb433f6193f37d361575d3ddfd340617f",
    "Gemini.list": "cc824670ed0b8baee93a12aebeb6c401bfeb4764b63d6d7806e3fd9289c6f228",
    "Github.list": "ecefa7e1163dd595b73c4dc2e42d9b48cac48bb2ccbfe0d7d6215bdea7258059",
    "Google.list": "ae5daa812c36be55847806bcb098f9b90f13e238c2d90024ff8d5183096fe1cb",
    "HBO.list": "4b3fd64e4be8b1497bcba563f814702bb0ce0c403734ce55bd3084fa88928d92",
    "Microsoft.list": "c6efd7c71cdc19cb80687b020108a406914d6dcb37fdd6973c94bafc39a7bfe3",
    "Netflix.list": "7201c869ae378b252d467fe09762ff4e405a8b50e2e359aa8eb6d09d3dc3a91c",
    "OneDrive.list": "3735ccb2620f489ee1e77b7ea3c64a9aba82f9ac19d9f0d2a8f8b90e5a5314b0",
    "PrimeVideo.list": "4466a46e37280b52f60c447dbb9d6a4273b5d656b27f0a5ea72f258c9afb4d01",
    "ProxyMedia.list": "6d99612bb86179253258fcdd90ed337ac1159e4564136464f918f615323676c5",
    "Reject.list": "7ded2b5e007442ebfd969b299e7a51f8a312ed05947eb28f5d88535462681ea3",
    "Spotify.list": "2b415fdf1a57fb6af6a28d1b4f7fd85afe9ce0c58be0f567ad452aa45674d543",
    "TikTok.list": "3d54df7d8bef801e579f9d10fb9c514c7ad142f0b50a7941870d065c1a1a2aee",
    "Twitter.list": "e8a3e2e72cfd546eadca02ea58c9d556da252cdea6b25f2abbd71432c14670d6",
    "YouTube.list": "4c8202c27e5f7d321bf7a85a377a15dbd4fc1d572d914956c8c73533007adcb6",
}
INLINE_RULESET_FILES = {
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


def active_lines(path: Path) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if line and not line.startswith(("#", ";", "//")):
            result.append((number, line))
    return result


def declared_count(path: Path) -> int | None:
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        match = COUNT_HEADER.fullmatch(raw.strip())
        if match:
            return int(match.group(1))
    return None


def profile_rule_files(profile: Path, errors: list[str]) -> set[str]:
    try:
        lines = profile.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        errors.append(f"{profile}: {exc}")
        return set()

    current = ""
    referenced: dict[str, int] = {}
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith(("#", ";", "//")):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            continue
        if current != "Rule":
            continue
        fields = [field.strip() for field in line.split(",")]
        if not fields or fields[0].upper() != "RULE-SET" or len(fields) < 2:
            continue
        source = fields[1]
        if source in {"SYSTEM", "LAN"}:
            continue
        if source.startswith(("http://", "https://")):
            errors.append(f"{profile}:{number}: external runtime RULE-SET is forbidden: {source}")
            continue
        filename = INLINE_RULESET_FILES.get(source, "")
        if not filename:
            errors.append(f"{profile}:{number}: undefined inline RULE-SET: {source}")
            continue
        if filename in referenced:
            errors.append(
                f"{profile}:{number}: duplicate RULE-SET file {filename} "
                f"(first referenced at line {referenced[filename]})"
            )
            continue
        referenced[filename] = number

    if not referenced:
        errors.append(f"{profile}: no RULE-SET files found in [Rule]")
    return set(referenced)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit local rule snapshots against the Surge iOS rule envelope."
    )
    parser.add_argument("root", nargs="?", default="Rules", type=Path)
    parser.add_argument(
        "--profile",
        type=Path,
        help="also require every RULE-SET referenced by this Surge profile",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root: Path = args.root
    if not root.is_dir():
        print(f"ERROR: rules directory not found: {root}", file=sys.stderr)
        return 2
    if args.profile is not None and not args.profile.is_file():
        print(f"ERROR: profile not found: {args.profile}", file=sys.stderr)
        return 2

    errors: list[str] = []
    runtime_files = profile_rule_files(args.profile, errors) if args.profile else set()
    files = sorted(root.glob("*.list"))
    paths_by_name = {path.name: path for path in files}
    total_rules = 0
    runtime_rules = 0
    if not files:
        errors.append("no .list files found")
    for filename in sorted(runtime_files - paths_by_name.keys()):
        errors.append(f"runtime RULE-SET file is missing: {filename}")
    if args.profile:
        for filename in sorted(runtime_files - RUNTIME_RULE_SHA256.keys()):
            errors.append(f"runtime RULE-SET has no pinned digest: {filename}")
        for filename in sorted(RUNTIME_RULE_SHA256.keys() - runtime_files):
            errors.append(f"pinned runtime RULE-SET is not referenced: {filename}")

    for path in files:
        try:
            payload = path.read_bytes()
            lines = active_lines(path)
            expected_count = declared_count(path)
        except (OSError, UnicodeError) as exc:
            errors.append(f"{path}: {exc}")
            continue

        total_rules += len(lines)
        is_runtime = path.name in runtime_files
        if is_runtime:
            runtime_rules += len(lines)
            expected_digest = RUNTIME_RULE_SHA256.get(path.name)
            actual_digest = hashlib.sha256(payload).hexdigest()
            if expected_digest is not None and actual_digest != expected_digest:
                errors.append(
                    f"{path}: pinned digest mismatch: expected {expected_digest}, got {actual_digest}"
                )
        if expected_count is not None and expected_count != len(lines):
            errors.append(
                f"{path}: declared count is {expected_count}, actual active entries are {len(lines)}"
            )

        seen: dict[str, int] = {}
        is_domain_set = path.name == "Ads_SukkaW_Domain.list"
        for number, line in lines:
            location = f"{path}:{number}"
            if len(line.encode("utf-8")) > 8192:
                errors.append(f"{location}: rule exceeds 8192 bytes")
            if line in seen:
                errors.append(f"{location}: duplicate of line {seen[line]}")
            else:
                seen[line] = number

            if is_domain_set:
                if any(character.isspace() for character in line) or "," in line:
                    errors.append(f"{location}: malformed domain-set entry")
                continue

            fields = [field.strip() for field in line.split(",")]
            rule_type = fields[0].upper()
            if rule_type in BANNED_IOS_TYPES:
                errors.append(f"{location}: {BANNED_IOS_TYPES[rule_type]}")
            elif rule_type in TWO_FIELD_TYPES:
                if len(fields) != 2 or not fields[1]:
                    errors.append(f"{location}: {rule_type} requires exactly one value")
            elif rule_type in NO_RESOLVE_TYPES:
                if len(fields) not in {2, 3} or (
                    len(fields) == 3 and fields[2].lower() != "no-resolve"
                ):
                    errors.append(f"{location}: invalid {rule_type} parameters")
                    continue
                if is_runtime and (len(fields) != 3 or fields[2].lower() != "no-resolve"):
                    errors.append(f"{location}: runtime IP rules must include no-resolve")
                try:
                    if rule_type == "IP-ASN":
                        if int(fields[1]) <= 0:
                            raise ValueError("ASN must be positive")
                    else:
                        network = ipaddress.ip_network(fields[1], strict=False)
                        expected_version = 6 if rule_type == "IP-CIDR6" else 4
                        if network.version != expected_version:
                            raise ValueError(f"expected IPv{expected_version}")
                except ValueError as exc:
                    errors.append(f"{location}: invalid {rule_type} value: {exc}")
            elif rule_type == "AND":
                if not line.startswith("AND,((") or not line.endswith("))"):
                    errors.append(f"{location}: malformed logical rule")
            else:
                errors.append(f"{location}: unsupported rule type: {rule_type}")

    if errors:
        for error in errors[:100]:
            print(f"ERROR: {error}", file=sys.stderr)
        if len(errors) > 100:
            print(f"ERROR: {len(errors) - 100} additional issue(s) omitted", file=sys.stderr)
        print(f"FAIL: {len(errors)} issue(s)", file=sys.stderr)
        return 1

    details = f"files={len(files)} active_entries={total_rules} target=Surge-iOS"
    if args.profile:
        details += f" runtime_files={len(runtime_files)} runtime_entries={runtime_rules}"
    print(f"PASS: {root} | {details}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
