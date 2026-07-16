#!/usr/bin/env python3
"""Validate the syntax envelope of local Surge rule snapshots."""

from __future__ import annotations

import ipaddress
import sys
from pathlib import Path


TWO_FIELD_TYPES = {
    "DOMAIN",
    "DOMAIN-KEYWORD",
    "DOMAIN-SUFFIX",
    "DOMAIN-WILDCARD",
    "PROCESS-NAME",
    "URL-REGEX",
    "USER-AGENT",
}
NO_RESOLVE_TYPES = {"IP-ASN", "IP-CIDR", "IP-CIDR6"}
POLICY_NAMES = {"DIRECT", "REJECT", "REJECT-DROP", "REJECT-NO-DROP"}


def active_lines(path: Path) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if line and not line.startswith(("#", ";", "//")):
            result.append((number, line))
    return result


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "Rules")
    if not root.is_dir():
        print(f"ERROR: rules directory not found: {root}", file=sys.stderr)
        return 2

    errors: list[str] = []
    files = sorted(root.glob("*.list"))
    total_rules = 0
    if not files:
        errors.append("no .list files found")

    for path in files:
        try:
            lines = active_lines(path)
        except (OSError, UnicodeError) as exc:
            errors.append(f"{path}: {exc}")
            continue

        total_rules += len(lines)
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
            if rule_type in TWO_FIELD_TYPES:
                if len(fields) != 2 or not fields[1]:
                    errors.append(f"{location}: {rule_type} requires exactly one value")
            elif rule_type in NO_RESOLVE_TYPES:
                if len(fields) not in {2, 3} or (len(fields) == 3 and fields[2].lower() != "no-resolve"):
                    errors.append(f"{location}: invalid {rule_type} parameters")
                    continue
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
                if any(line.endswith(f",{policy}") for policy in POLICY_NAMES):
                    errors.append(f"{location}: external rules must not embed a policy")
            else:
                errors.append(f"{location}: unsupported rule type: {rule_type}")

    if errors:
        for error in errors[:100]:
            print(f"ERROR: {error}", file=sys.stderr)
        if len(errors) > 100:
            print(f"ERROR: {len(errors) - 100} additional issue(s) omitted", file=sys.stderr)
        print(f"FAIL: {len(errors)} issue(s)", file=sys.stderr)
        return 1

    print(f"PASS: {root} | files={len(files)} active_entries={total_rules}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
