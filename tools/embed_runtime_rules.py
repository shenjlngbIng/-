#!/usr/bin/env python3
"""Embed the audited runtime rule snapshots into the Surge profile."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


RULESET_FILES = {
    "RS_Ads_SukkaW_Extra": "Ads_SukkaW_Extra.list",
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
FILE_TO_RULESET = {filename: name for name, filename in RULESET_FILES.items()}
MANAGED_SECTION = re.compile(r"^\[Ruleset (RS_[^]]+)\]$")
GENERATED_PREAMBLE = {
    "# 运行时规则已内嵌；不再依赖 GitHub、jsDelivr、TLS 或外部规则缓存",
    "# 下列内容由 tools/embed_runtime_rules.py 从 Rules/ 的固定快照生成",
}


def active_lines(path: Path) -> list[str]:
    return [
        line
        for raw in path.read_text(encoding="utf-8-sig").splitlines()
        if (line := raw.strip()) and not line.startswith(("#", ";", "//"))
    ]


def strip_managed_sections(lines: list[str]) -> list[str]:
    result: list[str] = []
    skipping = False
    for line in lines:
        if line in GENERATED_PREAMBLE:
            continue
        if line.startswith("[") and line.endswith("]"):
            match = MANAGED_SECTION.fullmatch(line.strip())
            skipping = bool(match and match.group(1) in RULESET_FILES)
            if skipping:
                continue
        if not skipping:
            result.append(line)
    return result


def replace_external_references(lines: list[str]) -> list[str]:
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        fields = [field.strip() for field in stripped.split(",")]
        if len(fields) >= 3 and fields[0].upper() == "RULE-SET" and "://" in fields[1]:
            filename = Path(unquote(urlsplit(fields[1]).path)).name
            ruleset = FILE_TO_RULESET.get(filename)
            if ruleset:
                fields[1] = ruleset
                line = ",".join(fields)
        result.append(line)
    return result


def build_rulesets(root: Path) -> list[str]:
    blocks = [*sorted(GENERATED_PREAMBLE, reverse=True), ""]
    for ruleset, filename in RULESET_FILES.items():
        path = root / "Rules" / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        blocks.extend(
            [
                f"[Ruleset {ruleset}]",
                f"# 固定快照: Rules/{filename}",
                *active_lines(path),
                "",
            ]
        )
    return blocks


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    profile = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "Surge.conf"
    lines = profile.read_text(encoding="utf-8-sig").splitlines()
    lines = replace_external_references(strip_managed_sections(lines))
    try:
        rule_index = lines.index("[Rule]")
    except ValueError:
        print(f"ERROR: [Rule] section not found: {profile}", file=sys.stderr)
        return 1
    prefix = lines[:rule_index]
    while prefix and not prefix[-1].strip():
        prefix.pop()
    output = prefix + [""] + build_rulesets(root) + lines[rule_index:]
    profile.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    print(f"PASS: embedded {len(RULESET_FILES)} rule snapshots into {profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
