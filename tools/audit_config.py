#!/usr/bin/env python3
"""Fail-closed static checks for the public Surge iOS profile."""

from __future__ import annotations

import ipaddress
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


DIRECT_GROUPS_ALLOWED = {"Domestic", "Apple", "Apple Push"}
IMMUTABLE_REVISION = re.compile(r"(?:@|/)[0-9a-f]{40}(?:/|$)", re.IGNORECASE)
ALLOWED_SECTIONS = {"General", "Host", "Proxy", "Proxy Group", "Rule"}
ALLOWED_GROUP_TYPES = {"select", "url-test", "fallback", "smart"}
ALLOWED_GROUP_OPTIONS = {
    "evaluate-before-use",
    "hidden",
    "include-all-proxies",
    "include-other-group",
    "interval",
    "no-alert",
    "policy-priority",
    "policy-regex-filter",
    "timeout",
    "tolerance",
}
BUILTIN_POLICIES = {"DIRECT", "REJECT", "REJECT-DROP", "REJECT-NO-DROP"}
RULE_TRAILING_OPTIONS = {"dns-failed", "extended-matching", "no-resolve"}
ALLOWED_RULE_TYPES = {
    "AND",
    "DEST-PORT",
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "FINAL",
    "IP-ASN",
    "IP-CIDR",
    "IP-CIDR6",
    "PROTOCOL",
    "RULE-SET",
}
DIRECT_RULE_TYPES = {"AND", "DOMAIN", "DOMAIN-SUFFIX", "IP-CIDR", "IP-CIDR6"}
REMOTE_RULE_PREFIXES = {
    "https://cdn.jsdelivr.net/gh/shenjlngbIng/-@8099f3036f0f1ebde038abff98cbaec9409cd430/Rules/",
}
RUNTIME_RULE_FILES = {
    "Ads_SukkaW_Extra.list",
    "Bahamut.list",
    "BiliBiliIntl.list",
    "ChatGPT.list",
    "Claude.list",
    "Disney.list",
    "Emby.list",
    "Game.list",
    "Gemini.list",
    "Github.list",
    "Google.list",
    "HBO.list",
    "Microsoft.list",
    "Netflix.list",
    "OneDrive.list",
    "PrimeVideo.list",
    "ProxyMedia.list",
    "Reject.list",
    "Spotify.list",
    "TikTok.list",
    "Twitter.list",
    "YouTube.list",
}
DIRECT_IP_RULES = {
    ("IP-CIDR", "10.0.0.0/8", "DIRECT"),
    ("IP-CIDR", "100.64.0.0/10", "DIRECT"),
    ("IP-CIDR", "127.0.0.0/8", "DIRECT"),
    ("IP-CIDR", "169.254.0.0/16", "DIRECT"),
    ("IP-CIDR", "172.16.0.0/12", "DIRECT"),
    ("IP-CIDR", "192.168.0.0/16", "DIRECT"),
    ("IP-CIDR", "17.188.20.0/23", "Apple Push"),
    ("IP-CIDR", "17.188.128.0/18", "Apple Push"),
    ("IP-CIDR", "17.249.0.0/16", "Apple Push"),
    ("IP-CIDR", "17.252.0.0/16", "Apple Push"),
    ("IP-CIDR", "17.57.144.0/22", "Apple Push"),
    ("IP-CIDR6", "2403:300:a42::/48", "Apple Push"),
    ("IP-CIDR6", "2403:300:a51::/48", "Apple Push"),
    ("IP-CIDR6", "2620:149:a44::/48", "Apple Push"),
    ("IP-CIDR6", "2a01:b740:a42::/48", "Apple Push"),
    ("IP-CIDR6", "::1/128", "DIRECT"),
    ("IP-CIDR6", "fc00::/7", "DIRECT"),
    ("IP-CIDR6", "fe80::/10", "DIRECT"),
}
DIRECT_BUILTIN_DOMAIN_RULES = {
    ("DOMAIN", "captive.apple.com"),
    ("DOMAIN", "miwifi.com"),
    ("DOMAIN", "p.to"),
    ("DOMAIN", "router.asus.com"),
    ("DOMAIN", "tplogin.cn"),
    ("DOMAIN-SUFFIX", "lan"),
    ("DOMAIN-SUFFIX", "local"),
}
EXPECTED_HOSTS = {
    "push.apple.com": "server:https://223.6.6.6/dns-query",
    "*.push.apple.com": "server:https://223.6.6.6/dns-query",
    "push-apple.com.akadns.net": "server:https://223.6.6.6/dns-query",
    "*.push-apple.com.akadns.net": "server:https://223.6.6.6/dns-query",
    "apple.com.edgekey.net": "server:https://223.6.6.6/dns-query",
    "*.apple.com.edgekey.net": "server:https://223.6.6.6/dns-query",
    "www.apple.com": "server:https://223.6.6.6/dns-query",
}


def split_fields(value: str) -> list[str]:
    return [field.strip() for field in value.split(",")]


def main() -> int:
    profile = Path(sys.argv[1] if len(sys.argv) > 1 else "Surge.conf")
    if not profile.is_file():
        print(f"ERROR: profile not found: {profile}", file=sys.stderr)
        return 2

    try:
        source_lines = profile.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        print(f"ERROR: cannot read profile: {exc}", file=sys.stderr)
        return 2
    sections: dict[str, list[tuple[int, str]]] = {}
    current = ""
    for number, raw in enumerate(source_lines, 1):
        line = raw.strip()
        if not line or line.startswith(("#", ";", "//")):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append((number, line))

    errors: list[str] = []

    def fail(message: str, line: int | None = None) -> None:
        prefix = f"line {line}: " if line else ""
        errors.append(prefix + message)

    for section in sections:
        if section and section not in ALLOWED_SECTIONS:
            fail(f"forbidden or unparsed section: [{section}]")
    for number, _ in sections.get("", []):
        fail("active content before the first section is forbidden", number)

    for number, raw in enumerate(source_lines, 1):
        directive = raw.strip().lower()
        if directive.startswith(("#!include", "#!managed-config")):
            fail("unparsed include/managed-profile directives are forbidden", number)

    general: dict[str, tuple[int, str]] = {}
    for number, line in sections.get("General", []):
        if "=" not in line:
            fail("malformed [General] entry", number)
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if key in general:
            fail(f"duplicate [General] key: {key}", number)
        general[key] = (number, value)

    required_general = {
        "include-all-networks": "true",
        "include-local-networks": "true",
        "include-apns": "true",
        "include-cellular-services": "true",
        "ipv6": "true",
        "ipv6-vif": "auto",
        "auto-suspend": "false",
        "icmp-forwarding": "false",
        "udp-policy-not-supported-behaviour": "REJECT",
        "encrypted-dns-follow-outbound-mode": "true",
        "encrypted-dns-skip-cert-verification": "false",
        "hijack-dns": "*:53",
        "block-quic": "all-proxy",
        "allow-wifi-access": "false",
        "allow-hotspot-access": "false",
        "proxy-restricted-to-lan": "true",
        "gateway-restricted-to-lan": "true",
        "http-api-web-dashboard": "false",
        "wifi-assist": "false",
        "all-hybrid": "false",
        "compatibility-mode": "0",
        "exclude-simple-hostnames": "false",
        "allow-dns-svcb": "false",
        "use-local-host-item-for-proxy": "false",
        "disable-geoip-db-auto-update": "true",
        "dns-server": "223.5.5.5",
        "encrypted-dns-server": "https://223.5.5.5/dns-query",
        "skip-proxy": "192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, localhost, *.local, *.lan, ::1/128, fc00::/7, fe80::/10",
        "loglevel": "warning",
        "internet-test-url": "http://www.apple.com/library/test/success.html",
        "proxy-test-url": "http://www.gstatic.com/generate_204",
        "test-timeout": "8",
        "show-error-page-for-reject": "false",
        "always-real-ip": "<simple-hostname>, *.lan, *.local, *.direct, *.cmpassport.com, id6.me, open.e.189.cn, mdn.open.wo.cn, opencloud.wostore.cn, auth.wosms.cn, *.10099.com.cn",
        "always-raw-tcp-hosts": "149.154.*, 91.108.*, *.push.apple.com:443, *.push-apple.com.akadns.net:443, *.apple.com.edgekey.net:443",
    }
    for key, expected in required_general.items():
        item = general.get(key)
        if not item or item[1].lower() != expected.lower():
            fail(f"{key} must be {expected}", item[0] if item else None)

    for key, (number, _) in general.items():
        if key not in required_general:
            fail(f"unapproved [General] option: {key}", number)

    for key in ("http-api", "external-controller-access", "http-listen", "socks5-listen", "tun-excluded-routes"):
        if key in general:
            fail(f"forbidden exposed/bypass option: {key}", general[key][0])

    for key in ("internet-test-url", "proxy-test-url"):
        item = general.get(key)
        if not item or not item[1].lower().startswith("http://"):
            fail(f"{key} must use an HTTP endpoint supported by Surge iOS testing", item[0] if item else None)

    encrypted_dns = general.get("encrypted-dns-server")
    if encrypted_dns and not re.fullmatch(r"https://(?:\d{1,3}\.){3}\d{1,3}/dns-query", encrypted_dns[1]):
        fail("encrypted DNS must use a single IP-literal HTTPS endpoint (no bootstrap DNS)", encrypted_dns[0])

    hosts: dict[str, tuple[int, str]] = {}
    for number, line in sections.get("Host", []):
        if "=" not in line:
            fail("malformed [Host] entry", number)
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if key in hosts:
            fail(f"duplicate [Host] key: {key}", number)
        hosts[key] = (number, value)
    for key, value in EXPECTED_HOSTS.items():
        item = hosts.get(key)
        if not item or item[1] != value:
            fail(f"APNs host override must be {key} = {value}", item[0] if item else None)
    for key, (number, _) in hosts.items():
        if key not in EXPECTED_HOSTS:
            fail(f"unapproved host override: {key}", number)

    proxy_types: dict[str, str] = {}
    for number, line in sections.get("Proxy", []):
        if "=" not in line:
            fail("malformed [Proxy] entry", number)
            continue
        name, value = (part.strip() for part in line.split("=", 1))
        if name in proxy_types:
            fail(f"duplicate [Proxy] name: {name}", number)
        fields = split_fields(value)
        proxy_type = fields[0].lower() if fields else ""
        proxy_types[name] = proxy_type
        if name.upper() in BUILTIN_POLICIES:
            fail(f"proxy may not shadow a built-in policy: {name}", number)
        if proxy_type == "direct" and name != "APNs Direct":
            fail(f"unapproved direct policy alias: {name}", number)
        if proxy_type in {"external", "external-proxy"}:
            fail(f"external proxy programs are not allowed: {name}", number)
        if proxy_type in {"http", "socks5"} and name != "Fail-Closed":
            fail(f"unencrypted proxy type is not allowed: {name}", number)
        if re.search(r"\bskip-cert-verify\s*=\s*true\b", value, re.IGNORECASE):
            fail(f"certificate verification disabled for: {name}", number)
        if name == "Fail-Closed" and fields != ["http", "127.0.0.1", "1"]:
            fail("Fail-Closed must remain the local unreachable sentinel", number)
        if name == "APNs Direct" and fields != [
            "direct",
            "test-url=http://www.apple.com/library/test/success.html",
            "test-timeout=5",
        ]:
            fail("APNs Direct definition changed", number)
        if name not in {"Fail-Closed", "APNs Direct"}:
            if len(fields) < 3:
                fail(f"proxy definition is incomplete: {name}", number)
            else:
                server = fields[1].strip("[]")
                try:
                    ipaddress.ip_address(server)
                except ValueError:
                    fail(f"proxy server must be an IP literal to avoid bootstrap DNS: {name}", number)

    for required_proxy in ("Fail-Closed", "APNs Direct"):
        if required_proxy not in proxy_types:
            fail(f"required proxy policy is missing: {required_proxy}")

    groups: dict[str, dict[str, object]] = {}
    for number, line in sections.get("Proxy Group", []):
        if "=" not in line:
            fail("malformed [Proxy Group] entry", number)
            continue
        name, value = (part.strip() for part in line.split("=", 1))
        if name in groups:
            fail(f"duplicate [Proxy Group] name: {name}", number)
        fields = split_fields(value)
        if not fields:
            fail(f"empty policy group: {name}", number)
            continue
        group_type = fields[0].lower()
        members: list[str] = []
        options: dict[str, str] = {}
        for field in fields[1:]:
            if "=" in field:
                key, option = (part.strip() for part in field.split("=", 1))
                options[key.lower()] = option.strip('"')
            else:
                members.append(field)
        groups[name] = {
            "line": number,
            "type": group_type,
            "members": members,
            "options": options,
        }
        if group_type not in ALLOWED_GROUP_TYPES:
            fail(f"unapproved policy group type: {name} = {group_type}", number)
        for key in options:
            if key not in ALLOWED_GROUP_OPTIONS and key != "policy-path":
                fail(f"unapproved policy group option in {name}: {key}", number)
        if "policy-path" in options:
            fail(f"runtime external policy subscription is forbidden: {name}", number)
        includes_all = str(options.get("include-all-proxies", "")).lower() in {"1", "true"}
        if includes_all and name != "AllServer":
            fail(f"only AllServer may dynamically include local proxies: {name}", number)
        if group_type == "url-test":
            if "update-interval" in options:
                fail(f"url-test must use interval, not update-interval: {name}", number)
            if options.get("evaluate-before-use", "").lower() != "true":
                fail(f"url-test must evaluate before first use: {name}", number)
            if options.get("interval") != "600":
                fail(f"url-test interval must remain 600 seconds: {name}", number)

    for name, group in groups.items():
        if name in proxy_types or name.upper() in BUILTIN_POLICIES:
            fail(f"policy group shadows another policy: {name}", int(group["line"]))
        members = list(group["members"])
        options = group["options"]
        assert isinstance(options, dict)
        included = str(options.get("include-other-group", ""))
        if included:
            members.extend(part.strip() for part in included.split(",") if part.strip())
        for member in members:
            if member not in groups and member not in proxy_types and member not in BUILTIN_POLICIES:
                fail(f"undefined policy member in {name}: {member}", int(group["line"]))

    all_server = groups.get("AllServer")
    if all_server:
        options = all_server["options"]
        assert isinstance(options, dict)
        policy_filter = str(options.get("policy-regex-filter", ""))
        if str(options.get("include-all-proxies", "")).lower() not in {"1", "true"}:
            fail("AllServer must include locally defined proxies", int(all_server["line"]))
        if "Fail-Closed" not in policy_filter or "APNs Direct" not in policy_filter:
            fail("AllServer filter must exclude reserved direct/sentinel aliases", int(all_server["line"]))
        try:
            compiled_filter = re.compile(policy_filter)
        except re.error as exc:
            fail(f"AllServer policy filter is invalid: {exc}", int(all_server["line"]))
        else:
            if compiled_filter.search("Fail-Closed") or compiled_filter.search("APNs Direct"):
                fail("AllServer policy filter does not actually exclude reserved aliases", int(all_server["line"]))
            if not compiled_filter.search("Vetted-US-Node"):
                fail("AllServer policy filter rejects an ordinary vetted node", int(all_server["line"]))

    apns_proxy = groups.get("APNs Proxy")
    if not apns_proxy:
        fail("APNs Proxy group is missing")
    else:
        apns_proxy_options = apns_proxy["options"]
        assert isinstance(apns_proxy_options, dict)
        if apns_proxy["type"] != "smart" or list(apns_proxy["members"]):
            fail("APNs Proxy must remain a smart group without direct members", int(apns_proxy["line"]))
        if apns_proxy_options.get("include-other-group") != "AllServer":
            fail("APNs Proxy must source vetted policies from AllServer", int(apns_proxy["line"]))
        if apns_proxy_options.get("policy-priority") != "^Fail-Closed$:1000":
            fail("APNs Proxy must strongly de-prioritize Fail-Closed", int(apns_proxy["line"]))

    apple_push = groups.get("Apple Push")
    if not apple_push:
        fail("Apple Push group is missing")
    else:
        apple_push_options = apple_push["options"]
        assert isinstance(apple_push_options, dict)
        if apple_push["type"] != "fallback" or list(apple_push["members"]) != ["APNs Proxy", "APNs Direct"]:
            fail("Apple Push must remain proxy-first with APNs Direct as final fallback", int(apple_push["line"]))
        if apple_push_options.get("interval") != "600" or apple_push_options.get("timeout") != "5":
            fail("Apple Push fallback timing changed", int(apple_push["line"]))

    direct_cache: dict[str, bool] = {}

    def reaches_direct(policy: str, stack: tuple[str, ...] = ()) -> bool:
        if policy == "DIRECT":
            return True
        if proxy_types.get(policy) == "direct":
            return True
        if policy in direct_cache:
            return direct_cache[policy]
        if policy in stack or policy not in groups:
            return False
        group = groups[policy]
        members = list(group["members"])
        options = group["options"]
        assert isinstance(options, dict)
        included = options.get("include-other-group", "")
        if included:
            members.extend(part.strip() for part in str(included).split(",") if part.strip())
        result = any(reaches_direct(member, stack + (policy,)) for member in members)
        direct_cache[policy] = result
        return result

    for name, group in groups.items():
        if reaches_direct(name) and name not in DIRECT_GROUPS_ALLOWED:
            fail(f"policy group unexpectedly reaches DIRECT: {name}", int(group["line"]))

    rules = sections.get("Rule", [])
    stun_index = doh_index = apns_doh_index = None
    first_broad_direct = None
    push_index = apple_suffix_index = None
    final_entries: list[tuple[int, str]] = []
    remote_count = 0
    remote_files: dict[str, int] = {}

    for index, (number, line) in enumerate(rules):
        upper = line.upper()
        if upper.startswith("PROTOCOL,STUN,"):
            stun_index = index
            if not upper.endswith(",PROXY"):
                fail("STUN must use Proxy", number)
        if upper.startswith("PROTOCOL,DOH,"):
            doh_index = index
            if not upper.endswith(",PROXY"):
                fail("DoH must use Proxy", number)
        if "PROTOCOL,DOH" in upper and "223.6.6.6" in line and upper.endswith(",DIRECT"):
            apns_doh_index = index
        if upper.startswith("PROTOCOL,DOH3,") or upper.startswith("PROTOCOL,DOQ,"):
            if not upper.endswith(",PROXY"):
                fail("DoH3/DoQ must use Proxy", number)
        if upper.startswith("DOMAIN-SUFFIX,PUSH.APPLE.COM,APPLE PUSH"):
            push_index = index
        if upper.startswith("DOMAIN-SUFFIX,APPLE.COM,APPLE"):
            apple_suffix_index = index
        if upper.startswith("FINAL,"):
            final_entries.append((number, line))

        fields = split_fields(line)
        policy_fields = list(fields)
        while policy_fields and policy_fields[-1].lower() in RULE_TRAILING_OPTIONS:
            policy_fields.pop()
        policy = policy_fields[-1] if policy_fields else ""
        rule_type = fields[0].upper() if fields else ""
        if rule_type not in ALLOWED_RULE_TYPES:
            fail(f"unsupported main rule type: {rule_type}", number)
        if rule_type in {"DOMAIN", "DOMAIN-SUFFIX", "DEST-PORT", "PROTOCOL"} and len(fields) != 3:
            fail(f"malformed {rule_type} rule", number)
        if rule_type in {"IP-ASN", "IP-CIDR", "IP-CIDR6"}:
            if len(fields) not in {3, 4} or (len(fields) == 4 and fields[3].lower() != "no-resolve"):
                fail(f"malformed {rule_type} rule", number)
        if rule_type == "RULE-SET":
            if len(fields) < 3 or any(option.lower() not in {"extended-matching", "no-resolve"} for option in fields[3:]):
                fail("malformed RULE-SET parameters", number)
        if rule_type == "FINAL" and len(fields) not in {2, 3}:
            fail("malformed FINAL rule", number)
        if policy not in groups and policy not in proxy_types and policy not in BUILTIN_POLICIES:
            fail(f"rule uses an undefined policy: {policy}", number)
        direct_rule = reaches_direct(policy) or policy == "DIRECT"
        narrow_apns_dns = "PROTOCOL,DOH" in upper and "223.6.6.6" in line
        if direct_rule and not narrow_apns_dns and first_broad_direct is None:
            first_broad_direct = index
        if direct_rule and rule_type not in DIRECT_RULE_TYPES:
            fail(f"rule type may not grant DIRECT: {rule_type}", number)
        if direct_rule and rule_type in {"IP-CIDR", "IP-CIDR6"}:
            target = fields[1] if len(fields) > 1 else ""
            if (rule_type, target, policy) not in DIRECT_IP_RULES:
                fail(f"unapproved DIRECT-capable network: {target}", number)
        if direct_rule and policy == "DIRECT" and rule_type in {"DOMAIN", "DOMAIN-SUFFIX"}:
            target = fields[1].lower() if len(fields) > 1 else ""
            if (rule_type, target) not in DIRECT_BUILTIN_DOMAIN_RULES:
                fail(f"unapproved built-in DIRECT domain: {target}", number)
        if direct_rule and rule_type == "AND" and line != "AND,((PROTOCOL,DOH),(DEST-PORT,443),(IP-CIDR,223.6.6.6/32)),DIRECT":
            fail("only the exact APNs DoH logical rule may grant DIRECT", number)

        if len(fields) >= 2 and fields[0].upper() in {"RULE-SET", "DOMAIN-SET"} and fields[1].startswith(("http://", "https://")):
            remote_count += 1
            url = fields[1]
            parsed_url = urlsplit(url)
            filename = Path(unquote(parsed_url.path)).name
            if parsed_url.query or parsed_url.fragment:
                fail(f"remote rule URL must not contain a query or fragment: {url}", number)
            if filename in remote_files:
                fail(
                    f"duplicate remote rule file: {filename} "
                    f"(first referenced at line {remote_files[filename]})",
                    number,
                )
            else:
                remote_files[filename] = number
            if not url.startswith("https://"):
                fail(f"remote rule must use HTTPS: {url}", number)
            if not any(url.startswith(prefix) for prefix in REMOTE_RULE_PREFIXES):
                fail(f"remote rule source is not allowlisted: {url}", number)
            if "/master/" in url or "/main/" in url or not IMMUTABLE_REVISION.search(url):
                fail(f"remote rule is not pinned to a full commit: {url}", number)
            if direct_rule:
                fail("remote rules may not feed a DIRECT-capable policy", number)

    if apns_doh_index is None or doh_index is None or doh_index != apns_doh_index + 1:
        fail("APNs DoH exception must immediately precede the generic DoH proxy guard")
    elif [line.upper() for _, line in rules[doh_index : doh_index + 3]] != [
        "PROTOCOL,DOH,PROXY",
        "PROTOCOL,DOH3,PROXY",
        "PROTOCOL,DOQ,PROXY",
    ]:
        fail("DoH, DoH3 and DoQ proxy guards must remain contiguous")
    if stun_index is None or (first_broad_direct is not None and stun_index > first_broad_direct):
        fail("STUN guard must precede all broad DIRECT-capable rules")
    if push_index is None or (apple_suffix_index is not None and push_index > apple_suffix_index):
        fail("push.apple.com must enter Apple Push before broad Apple rules")
    if len(final_entries) != 1 or final_entries[0][1].upper() != "FINAL,FINAL,DNS-FAILED":
        fail("profile must have exactly one FINAL,Final,dns-failed rule")
    if rules and final_entries and final_entries[0][0] != rules[-1][0]:
        fail("FINAL must be the last active rule", final_entries[0][0])
    if remote_count != 22:
        fail(f"expected 22 immutable remote rules, found {remote_count}")
    missing_remote_files = sorted(RUNTIME_RULE_FILES - remote_files.keys())
    unexpected_remote_files = sorted(remote_files.keys() - RUNTIME_RULE_FILES)
    if missing_remote_files:
        fail(f"required runtime rule files are missing: {', '.join(missing_remote_files)}")
    if unexpected_remote_files:
        fail(f"unapproved runtime rule files are present: {', '.join(unexpected_remote_files)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAIL: {len(errors)} issue(s)", file=sys.stderr)
        return 1

    print(
        f"PASS: {profile} | groups={len(groups)} rules={len(rules)} "
        f"remote_rules={remote_count} direct_groups={','.join(sorted(DIRECT_GROUPS_ALLOWED))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
