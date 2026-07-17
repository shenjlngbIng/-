#!/usr/bin/env python3
"""Validate local rule snapshots for the Surge iOS-only profile."""

from __future__ import annotations

import argparse
import ipaddress
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


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
        path = unquote(urlsplit(source).path) if "://" in source else source
        filename = Path(path).name
        if not filename.endswith(".list"):
            errors.append(f"{profile}:{number}: RULE-SET does not name a .list file: {source}")
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

    for path in files:
        try:
            lines = active_lines(path)
            expected_count = declared_count(path)
        except (OSError, UnicodeError) as exc:
            errors.append(f"{path}: {exc}")
            continue

        total_rules += len(lines)
        is_runtime = path.name in runtime_files
        if is_runtime:
            runtime_rules += len(lines)
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
