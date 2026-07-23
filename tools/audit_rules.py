#!/usr/bin/env python3
"""Validate the rule snapshots and the immutable R10 embedding lock."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
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
    "URL-REGEX": "URL matching is excluded from this no-MITM profile",
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="Rules", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: rules directory not found: {root}", file=sys.stderr)
        return 2

    errors: list[str] = []
    lock_path = root / "r10.lock.json"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {lock_path}: {exc}", file=sys.stderr)
        return 2

    if lock.get("schema") != 1:
        errors.append("Rules/r10.lock.json has an unsupported schema")
    if not re.fullmatch(r"[0-9a-f]{40}", str(lock.get("source_commit", ""))):
        errors.append("R10 source_commit must be a full lowercase Git commit")

    locked_items = [dict(item) for item in lock.get("files", [])]
    locked: dict[str, dict[str, object]] = {}
    for item in locked_items:
        filename = str(item.get("file", ""))
        if not filename.endswith(".list") or "/" in filename or "\\" in filename:
            errors.append(f"invalid locked filename: {filename!r}")
            continue
        if filename in locked:
            errors.append(f"duplicate R10 lock entry: {filename}")
            continue
        locked[filename] = item
        role = item.get("role")
        policy = item.get("policy")
        if role == "service" and policy in {"DIRECT", "Apple", "Domestic"}:
            errors.append(f"service rule source can reach direct: {filename} -> {policy}")
        elif role == "direct_allowlist" and policy not in {"Apple", "Domestic"}:
            errors.append(f"invalid direct allowlist policy: {filename} -> {policy}")
        elif role not in {"service", "direct_allowlist"}:
            errors.append(f"invalid R10 source role: {filename} -> {role}")

    if len(locked) != 26:
        errors.append(f"R10 lock must contain 26 files, got {len(locked)}")

    files = sorted(root.glob("*.list"))
    if len(files) != 26:
        errors.append(f"Rules must contain exactly the 26 locked .list files, got {len(files)}")
    total_entries = 0
    locked_source_entries = 0
    for path in files:
        try:
            payload = path.read_bytes()
            entries = active_lines(path)
        except (OSError, UnicodeError) as exc:
            errors.append(f"{path}: {exc}")
            continue
        total_entries += len(entries)
        header_count = declared_count(path)
        if header_count is not None and header_count != len(entries):
            errors.append(
                f"{path}: declared count is {header_count}, actual active entries are {len(entries)}"
            )

        item = locked.get(path.name)
        if item is not None:
            locked_source_entries += len(entries)
            digest = hashlib.sha256(payload).hexdigest()
            if item.get("sha256") != digest:
                errors.append(
                    f"{path}: R10 lock digest mismatch: expected {item.get('sha256')}, got {digest}"
                )
            if item.get("active_entries") != len(entries):
                errors.append(f"{path}: R10 lock active count mismatch")

        seen: dict[str, int] = {}
        is_domain_set = path.name == "Ads_SukkaW_Domain.list"
        require_no_resolve = bool(item and item.get("role") == "service")
        for number, line in entries:
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
                if require_no_resolve and (len(fields) != 3 or fields[2].lower() != "no-resolve"):
                    errors.append(f"{location}: embedded service IP rules require no-resolve")
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
                    errors.append(f"{location}: invalid {rule_type}: {exc}")
            elif rule_type == "AND":
                if not line.startswith("AND,((") or not line.endswith("))"):
                    errors.append(f"{location}: malformed logical rule")
            else:
                errors.append(f"{location}: unsupported rule type: {rule_type}")

    for filename in sorted(set(locked) - {path.name for path in files}):
        errors.append(f"locked R10 source is missing: {filename}")

    service_source = sum(
        int(item.get("active_entries", -1))
        for item in locked.values()
        if item.get("role") == "service"
    )
    service_embedded = sum(
        int(item.get("embedded_entries", -1))
        for item in locked.values()
        if item.get("role") == "service"
    )
    direct_embedded = sum(
        int(item.get("embedded_entries", -1))
        for item in locked.values()
        if item.get("role") == "direct_allowlist"
    )
    expected_totals = {
        "service_source_entries": service_source,
        "service_embedded_entries": service_embedded,
        "direct_embedded_entries": direct_embedded,
    }
    for key, actual in expected_totals.items():
        if lock.get(key) != actual:
            errors.append(f"R10 lock aggregate mismatch for {key}: {lock.get(key)} != {actual}")

    if total_entries != 5726:
        errors.append(f"unexpected complete Rules entry count: {total_entries}")

    if errors:
        for error in errors[:100]:
            print(f"ERROR: {error}", file=sys.stderr)
        if len(errors) > 100:
            print(f"ERROR: {len(errors) - 100} additional issue(s) omitted", file=sys.stderr)
        print(f"FAIL: {len(errors)} issue(s)", file=sys.stderr)
        return 1

    print(
        "PASS: Rules | "
        f"files={len(files)} active_entries={total_entries} "
        f"locked_files={len(locked)} embedded={service_embedded + direct_embedded}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
