#!/usr/bin/env python3
"""Validate the R11 LTS profile lock and committed rule snapshots."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
DEFAULT_RULES = ROOT / "Rules"
RULES = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_RULES
LOCK = RULES / "r10.lock.json"


def active_lines(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
    ]


def fail(message: str) -> None:
    raise AssertionError(message)


if not LOCK.is_file():
    fail(f"lock file not found: {LOCK}")

lock = json.loads(LOCK.read_text(encoding="utf-8"))
if lock.get("schema") != 4:
    fail(f"unsupported lock schema: {lock.get('schema')!r}")
if lock.get("profile") != "Surge iOS Stable Fail-Closed R11 LTS":
    fail("lock profile name mismatch")

# A staged ZIP may contain Rules without Surge.conf. In that mode, validate only
# the rule inventory. The repository checkout additionally validates profile metadata.
profile = PROFILE if RULES == DEFAULT_RULES else RULES.parent / "Surge.conf"
if profile.is_file():
    text = profile.read_text(encoding="utf-8")
    rule_text = text.split("[Rule]", 1)[1]
    active_rules = [
        line.strip()
        for line in rule_text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if lock.get("profile_sha256") != hashlib.sha256(text.encode()).hexdigest():
        fail("profile hash mismatch")
    if lock.get("profile_lines") != len(text.splitlines()):
        fail("profile line count mismatch")
    if lock.get("active_rules") != len(active_rules):
        fail("active rule count mismatch")

errors: list[str] = []
for item in lock.get("embedded_sources", []):
    filename = str(item["file"])
    path = RULES / filename
    if not path.is_file():
        errors.append(f"missing source: {filename}")
        continue
    actual = len(active_lines(path))
    expected = int(item["active_entries"])
    if actual != expected:
        errors.append(f"{filename}: expected {expected}, got {actual}")

if errors:
    raise AssertionError("\n".join(errors))

print(
    f"PASS R11 LTS sources={len(lock.get('embedded_sources', []))} "
    f"rules={lock.get('active_rules')}"
)
