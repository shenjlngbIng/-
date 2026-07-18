#!/usr/bin/env python3
"""Fail-closed static checks for the public Surge iOS profile."""

from __future__ import annotations

import hashlib
import ipaddress
import re
import sys
from pathlib import Path


DIRECT_GROUPS_ALLOWED = {"Domestic", "Apple"}
FORBIDDEN_SPECIAL_POLICIES = {"APNs Direct", "APNs Proxy", "Apple Push"}
ALLOWED_SECTIONS = {"General", "Host", "Proxy", "Proxy Group", "Rule"}
ALLOWED_PROXY_TYPES = {
    "https",
    "hysteria2",
    "snell",
    "socks5-tls",
    "ss",
    "ssh",
    "trojan",
    "tuic",
    "vmess",
}
ALLOWED_GROUP_TYPES = {"select", "url-test"}
ALLOWED_GROUP_OPTIONS = {
    "evaluate-before-use",
    "hidden",
    "include-all-proxies",
    "include-other-group",
    "interval",
    "no-alert",
    "policy-regex-filter",
    "tolerance",
    "update-interval",
}
BUILTIN_POLICIES = {"DIRECT", "REJECT", "REJECT-DROP", "REJECT-NO-DROP"}
RULE_TRAILING_OPTIONS = {"dns-failed", "extended-matching", "no-resolve"}
ALLOWED_RULE_TYPES = {
    "AND",
    "DEST-PORT",
    "DOMAIN",
    "DOMAIN-KEYWORD",
    "DOMAIN-SUFFIX",
    "FINAL",
    "IP-ASN",
    "IP-CIDR",
    "IP-CIDR6",
    "PROTOCOL",
    "RULE-SET",
}
DIRECT_RULE_TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "IP-CIDR", "IP-CIDR6"}
INLINE_RULESETS = {
    "RS_Ads_Custom_Extra": ("Ads_Custom_Extra.list", 206, "a97509c9cd7a9f22e1f5339e35299fee4b66b163b49f5d7fba1e199ad010af49"),
    "RS_Bahamut": ("Bahamut.list", 10, "78ca9e8af828130ea1807d57f5b0cfb42e40c42d5c6a8eda5bd98a544384f833"),
    "RS_BiliBiliIntl": ("BiliBiliIntl.list", 1, "40502ce8ef7356d89f3c0ab5f78fce58cbbff115950b70c06900086c1e4c5d9d"),
    "RS_ChatGPT": ("ChatGPT.list", 52, "60c87c4a6c2cbf3d846454b7b42f6107526f2f9fa9c11e5c785a2e85bb5943ce"),
    "RS_Claude": ("Claude.list", 6, "6760dfeb03df7d4a169c812b1540916bcbd599ccc77610e9f74121857d3d056c"),
    "RS_Disney": ("Disney.list", 172, "c881730102bda2cdf4582d799bcf363180277a65f32b9d5eaff9260bf8b02db1"),
    "RS_Emby": ("Emby.list", 218, "ba37387017c311ae74ae0050ea42f7751251047ceca88123b0a173e89b87fdd8"),
    "RS_Game": ("Game.list", 597, "d355395a460916e44bc1a2f5fddaf755a05411e96e5111118f5687a36e868014"),
    "RS_Gemini": ("Gemini.list", 21, "f7c6d2ab31f844eb97d0d9379ad6ac5f316bbf668c7f0a5da6598cb317483cc7"),
    "RS_Github": ("Github.list", 31, "95299a16144b19c5ff24298c6ba2ab731dc05b99c22340b566408cedf71124ea"),
    "RS_Google": ("Google.list", 705, "c3d58d4cb256a5770fbf10e0c3bf22106a722756f132011e5c84d777c83d4e1e"),
    "RS_HBO": ("HBO.list", 47, "2c8b931844b331b0b42db6eda6926b5259db0a977da48d0430541b51ef4aae0a"),
    "RS_Microsoft": ("Microsoft.list", 669, "5083f3946f3fbe1b3f34563fb207f38888aafaa98bca084140ae09175b674c48"),
    "RS_Netflix": ("Netflix.list", 1154, "7d91b049f5773883b487ae08248e2da0eafabe29fe0c2af43d615569cb4d19f0"),
    "RS_OneDrive": ("OneDrive.list", 16, "c8f86f71aa796fae87042f301c82219a1acb457e292e98dedfb27e494395cde6"),
    "RS_PrimeVideo": ("PrimeVideo.list", 18, "6f30ff4bcf5d38f317f1333298b36fc499d4161bd3f54c700c85e03ac2ffcd73"),
    "RS_ProxyMedia": ("ProxyMedia.list", 321, "4af6caf4869a48522e7993c81922965cfdd585e47467ec332b335209941639b1"),
    "RS_Reject": ("Reject.list", 6210, "a344f68cc0051dc7581524c86d5ac38fbac5d918b0872b47beca0501f6a90470"),
    "RS_Spotify": ("Spotify.list", 30, "38ec3e72e9bf0a344c0fcff75abc348fae9cbc22d052913369040630bcc545f6"),
    "RS_TikTok": ("TikTok.list", 87, "f39ff9a61ec1ce7eabf9410384252b1130fe475869d0f445c190f0fd34d0c656"),
    "RS_Twitter": ("Twitter.list", 33, "371a1ead914bfa4ff5ff4ca338111d6e088517cf4792dd0bd43448b9331d1eb8"),
    "RS_YouTube": ("YouTube.list", 192, "29d0f6217491bcc2e8b45502cd8b501ec1951962228149951d1b032a16574003"),
}
APNS_PROXY_RULES = {
    "DOMAIN-SUFFIX,push.apple.com,Proxy",
    "DOMAIN-KEYWORD,push-apple.com.akadns.net,Proxy",
    "DOMAIN-SUFFIX,push-apple.com,Proxy",
    "DOMAIN-KEYWORD,apple.com.edgekey.net,Proxy",
    "IP-CIDR,17.249.0.0/16,Proxy,no-resolve",
    "IP-CIDR,17.252.0.0/16,Proxy,no-resolve",
    "IP-CIDR,17.57.144.0/22,Proxy,no-resolve",
    "IP-CIDR,17.188.128.0/18,Proxy,no-resolve",
    "IP-CIDR,17.188.20.0/23,Proxy,no-resolve",
    "IP-CIDR6,2620:149:a44::/48,Proxy,no-resolve",
    "IP-CIDR6,2403:300:a42::/48,Proxy,no-resolve",
    "IP-CIDR6,2403:300:a51::/48,Proxy,no-resolve",
    "IP-CIDR6,2a01:b740:a42::/48,Proxy,no-resolve",
}
APNS_TARGETS = {rule.split(",")[1].lower() for rule in APNS_PROXY_RULES}
DIRECT_IP_RULES = {
    ("IP-CIDR", "10.0.0.0/8", "DIRECT"),
    ("IP-CIDR", "127.0.0.0/8", "DIRECT"),
    ("IP-CIDR", "169.254.0.0/16", "DIRECT"),
    ("IP-CIDR", "172.16.0.0/12", "DIRECT"),
    ("IP-CIDR", "192.168.0.0/16", "DIRECT"),
    ("IP-CIDR", "224.0.0.251/32", "DIRECT"),
    ("IP-CIDR", "239.255.255.250/32", "DIRECT"),
    ("IP-CIDR6", "::1/128", "DIRECT"),
    ("IP-CIDR6", "fc00::/7", "DIRECT"),
    ("IP-CIDR6", "fe80::/10", "DIRECT"),
    ("IP-CIDR6", "ff02::c/128", "DIRECT"),
    ("IP-CIDR6", "ff02::fb/128", "DIRECT"),
}
DIRECT_BUILTIN_DOMAIN_RULES = {
    ("DOMAIN", "localhost"),
    ("DOMAIN", "sub.store"),
    ("DOMAIN-SUFFIX", "local"),
}
EXPECTED_DIRECT_DOMAIN_COUNT = 110
EXPECTED_DIRECT_DOMAIN_SHA256 = "85e52c57478017d849caf5ffa51deb7269ba33fa4f972a2b701e9eb4cf94467c"
EXPECTED_HOSTS = {
    "sub.store": "127.0.0.1",
}
SERVICE_RULE_COMMIT = "c00517ce10760a93728b241923a451dfa617be80"
REQUIRED_PROFILE_COMMENTS = {
    "# Surge iOS · Fail-Closed",
    "# 最低版本: Surge iOS 5.14.6+",
    "# 来源与许可见 NOTICE.md；本次服务规则固定于 "
    f"blackmatrix7@{SERVICE_RULE_COMMIT}（GPL-2.0）。",
}
BUILD_ID = re.compile(r"IOS-HARDENED-[0-9]{8}-REVIEWED-R6-([0-9A-F]{8})")
DOH_BOOTSTRAP_RULE = "AND,((PROTOCOL,DOH),(DOMAIN,223.5.5.5)),DIRECT"
DISCOVERY_DIRECT_RULES = {
    "IP-CIDR,224.0.0.251/32,DIRECT,no-resolve",
    "IP-CIDR,239.255.255.250/32,DIRECT,no-resolve",
    "IP-CIDR6,ff02::fb/128,DIRECT,no-resolve",
    "IP-CIDR6,ff02::c/128,DIRECT,no-resolve",
}
SUBSTORE_REQUIRED_COMMENTS = {
    "# 【Sub-Store 转换订阅地址填写处】只替换下方 policy-path 的中文占位文字",
    "# 零静态节点冷启动：真实链接无“?”时追加 ?proxy=DIRECT；已有“?”时追加 &proxy=DIRECT",
    "# 上述 DIRECT 仅是明确的订阅控制面启动例外；普通境外、未知和失败流量仍不回落直连",
    "# 更严格模式：先在私有 [Proxy] 加入已审核启动节点，再把 DIRECT 改成该节点或策略名",
}
SUBSTORE_POLICY_PATH_PLACEHOLDER = "此处填入Sub-Store转换后的订阅链接"


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
    errors: list[str] = []

    def fail(message: str, line: int | None = None) -> None:
        prefix = f"line {line}: " if line else ""
        errors.append(prefix + message)

    for comment in sorted(REQUIRED_PROFILE_COMMENTS):
        if comment not in source_lines:
            fail(f"required profile metadata is missing: {comment}")
    build_lines = [line for line in source_lines if line.startswith("# 构建: ")]
    if len(build_lines) != 1:
        fail("profile must contain exactly one build identifier")
    else:
        build_id = build_lines[0].removeprefix("# 构建: ")
        match = BUILD_ID.fullmatch(build_id)
        if not match:
            fail(f"invalid or unfinished build identifier: {build_id}")
        else:
            normalized = "\n".join(
                "# 构建: <normalized>" if line == build_lines[0] else line
                for line in source_lines
            ) + "\n"
            expected_digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8].upper()
            if match.group(1) != expected_digest:
                fail(
                    f"build identifier digest mismatch: expected {expected_digest}, "
                    f"got {match.group(1)}"
                )
    sections: dict[str, list[tuple[int, str]]] = {}
    duplicate_sections: list[tuple[int, str]] = []
    current = ""
    for number, raw in enumerate(source_lines, 1):
        line = raw.strip()
        if not line or line.startswith(("#", ";", "//")):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            if current in sections:
                duplicate_sections.append((number, current))
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append((number, line))

    for comment in sorted(SUBSTORE_REQUIRED_COMMENTS):
        if comment not in source_lines:
            fail(f"required Sub-Store bootstrap comment is missing: {comment}")

    for section in sections:
        inline_name = section.removeprefix("Ruleset ")
        is_inline = section.startswith("Ruleset ") and inline_name in INLINE_RULESETS
        if section and section not in ALLOWED_SECTIONS and not is_inline:
            fail(f"forbidden or unparsed section: [{section}]")
    for number, section in duplicate_sections:
        fail(f"duplicate section: [{section}]", number)
    for number, _ in sections.get("", []):
        fail("active content before the first section is forbidden", number)

    inline_entry_total = 0
    for name, (filename, expected_count, expected_digest) in INLINE_RULESETS.items():
        section_name = f"Ruleset {name}"
        entries = sections.get(section_name)
        if entries is None:
            fail(f"required inline ruleset is missing: [{section_name}]")
            continue
        lines = [line for _, line in entries]
        inline_entry_total += len(lines)
        payload = ("\n".join(lines) + "\n").encode("utf-8")
        actual_digest = hashlib.sha256(payload).hexdigest()
        if len(lines) != expected_count or actual_digest != expected_digest:
            fail(
                f"inline ruleset {name} no longer matches Rules/{filename}: "
                f"count={len(lines)} sha256={actual_digest}"
            )

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
        "ipv6-vif": "always",
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
        "compatibility-mode": "3",
        "exclude-simple-hostnames": "false",
        "allow-dns-svcb": "false",
        "use-local-host-item-for-proxy": "false",
        "disable-geoip-db-auto-update": "true",
        "dns-server": "223.5.5.5",
        "encrypted-dns-server": "https://223.5.5.5/dns-query",
        "skip-proxy": "192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 127.0.0.0/8, 169.254.0.0/16, localhost, *.local, ::1/128, fc00::/7, fe80::/10",
        "loglevel": "warning",
        "internet-test-url": "http://www.apple.com/library/test/success.html",
        "proxy-test-url": "http://www.gstatic.com/generate_204",
        "test-timeout": "8",
        "show-error-page-for-reject": "false",
        "always-real-ip": "<simple-hostname>, *.local, *.cmpassport.com, id6.me, open.e.189.cn, mdn.open.wo.cn, opencloud.wostore.cn, auth.wosms.cn, *.10099.com.cn",
        "always-raw-tcp-hosts": "149.154.*, 91.108.*, *.push.apple.com:443, *push-apple.com.akadns.net:443, *.apple.com.edgekey.net:443",
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
            fail(f"required host mapping must be {key} = {value}", item[0] if item else None)
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
        if name in FORBIDDEN_SPECIAL_POLICIES:
            fail(f"obsolete APNs special policy is forbidden: {name}", number)
        if proxy_type == "direct":
            fail(f"direct policy aliases are forbidden: {name}", number)
        if proxy_type in {"external", "external-proxy"}:
            fail(f"external proxy programs are not allowed: {name}", number)
        if name != "Fail-Closed" and proxy_type not in ALLOWED_PROXY_TYPES:
            fail(f"unapproved or unencrypted proxy type: {name} = {proxy_type}", number)
        insecure_parameters = (
            r"\bskip-cert-verify\s*=\s*true\b",
            r"\bskip-common-name-verify\s*=\s*true\b",
            r"\ballow-insecure\s*=\s*true\b",
            r"\btls-verification\s*=\s*false\b",
        )
        if any(re.search(pattern, value, re.IGNORECASE) for pattern in insecure_parameters):
            fail(f"proxy certificate verification weakened for: {name}", number)
        if name == "Fail-Closed" and fields != ["http", "127.0.0.1", "1"]:
            fail("Fail-Closed must remain the local unreachable sentinel", number)
        if name != "Fail-Closed":
            if len(fields) < 3:
                fail(f"proxy definition is incomplete: {name}", number)
            else:
                server = fields[1].strip("[]")
                try:
                    ipaddress.ip_address(server)
                except ValueError:
                    fail(f"proxy server must be an IP literal to avoid bootstrap DNS: {name}", number)
                try:
                    port = int(fields[2])
                    if not 1 <= port <= 65535:
                        raise ValueError
                except ValueError:
                    fail(f"proxy server port must be between 1 and 65535: {name}", number)
            if proxy_type == "ss":
                proxy_options = {
                    key.strip().lower(): option.strip()
                    for field in fields[3:]
                    if "=" in field
                    for key, option in [field.split("=", 1)]
                }
                method = proxy_options.get("encrypt-method", "").lower()
                if not (method.endswith("-gcm") or method.endswith("-poly1305")):
                    fail(f"Shadowsocks must use an AEAD encrypt-method: {name}", number)
                if not proxy_options.get("password"):
                    fail(f"Shadowsocks password is missing: {name}", number)

    for required_proxy in ("Fail-Closed",):
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
        if name in FORBIDDEN_SPECIAL_POLICIES:
            fail(f"obsolete APNs special policy group is forbidden: {name}", number)
        if group_type not in ALLOWED_GROUP_TYPES:
            fail(f"unapproved policy group type: {name} = {group_type}", number)
        for key in options:
            if key not in ALLOWED_GROUP_OPTIONS and key != "policy-path":
                fail(f"unapproved policy group option in {name}: {key}", number)
        policy_path = options.get("policy-path")
        is_substore_placeholder = (
            name == "AllServer" and policy_path == SUBSTORE_POLICY_PATH_PLACEHOLDER
        )
        if policy_path is not None and not is_substore_placeholder:
            fail(f"public profile may only contain the audited Sub-Store placeholder: {name}", number)
        if name == "AllServer" and not is_substore_placeholder:
            fail("AllServer must retain the Sub-Store policy-path placeholder", number)
        if "update-interval" in options and (
            not is_substore_placeholder or options["update-interval"] != "0"
        ):
            fail(f"update-interval is only approved for the AllServer placeholder at 0: {name}", number)
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

    group_states: dict[str, int] = {}

    def visit_group(name: str, stack: tuple[str, ...] = ()) -> None:
        state = group_states.get(name, 0)
        if state == 1:
            fail(f"policy group cycle is forbidden: {' -> '.join(stack + (name,))}")
            return
        if state == 2:
            return
        group_states[name] = 1
        group = groups[name]
        members = list(group["members"])
        options = group["options"]
        assert isinstance(options, dict)
        included = str(options.get("include-other-group", ""))
        if included:
            members.extend(part.strip() for part in included.split(",") if part.strip())
        for member in members:
            if member in groups:
                visit_group(member, stack + (name,))
        group_states[name] = 2

    for group_name in groups:
        visit_group(group_name)

    all_server = groups.get("AllServer")
    if all_server:
        options = all_server["options"]
        assert isinstance(options, dict)
        policy_filter = str(options.get("policy-regex-filter", ""))
        if str(options.get("include-all-proxies", "")).lower() not in {"1", "true"}:
            fail("AllServer must include locally defined proxies", int(all_server["line"]))
        if "Fail-Closed" not in policy_filter:
            fail("AllServer filter must exclude the failure sentinel alias", int(all_server["line"]))
        try:
            compiled_filter = re.compile(policy_filter)
        except re.error as exc:
            fail(f"AllServer policy filter is invalid: {exc}", int(all_server["line"]))
        else:
            if compiled_filter.search("Fail-Closed"):
                fail("AllServer policy filter does not actually exclude the sentinel alias", int(all_server["line"]))
            if not compiled_filter.search("Vetted-US-Node"):
                fail("AllServer policy filter rejects an ordinary vetted node", int(all_server["line"]))

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
    stun_index = doh_index = quic_index = udp_index = dns53_index = None
    doh_bootstrap_index = None
    final_entries: list[tuple[int, str]] = []
    external_rule_count = 0
    inline_references: dict[str, int] = {}
    seen_rules: dict[str, int] = {}
    seen_direct_ip_rules: set[tuple[str, str, str]] = set()
    seen_apns_proxy_rules: set[str] = set()
    apns_rule_indices: list[int] = []
    apple_domain_index = None
    system_ruleset_index = None
    direct_domain_rules: list[str] = []
    direct_rule_indices: list[int] = []
    rule_indices: dict[str, int] = {}

    for index, (number, line) in enumerate(rules):
        if line in seen_rules:
            fail(f"duplicate main rule (first referenced at line {seen_rules[line]})", number)
        else:
            seen_rules[line] = number
            rule_indices[line] = index
        upper = line.upper()
        if line == DOH_BOOTSTRAP_RULE:
            if doh_bootstrap_index is not None:
                fail("duplicate encrypted DNS bootstrap exception", number)
            doh_bootstrap_index = index
        if upper.startswith("PROTOCOL,STUN,"):
            stun_index = index
            if not upper.endswith(",PROXY"):
                fail("STUN must use Proxy", number)
        if upper.startswith("PROTOCOL,QUIC,"):
            quic_index = index
            if not upper.endswith(",PROXY"):
                fail("QUIC must use Proxy", number)
        if upper.startswith("PROTOCOL,UDP,"):
            udp_index = index
            if not upper.endswith(",PROXY"):
                fail("UDP must use Proxy", number)
        if upper.startswith("PROTOCOL,DOH,"):
            doh_index = index
            if not upper.endswith(",PROXY"):
                fail("DoH must use Proxy", number)
        if upper.startswith("PROTOCOL,DOH3,") or upper.startswith("PROTOCOL,DOQ,"):
            if not upper.endswith(",PROXY"):
                fail("DoH3/DoQ must use Proxy", number)
        if upper == "DEST-PORT,53,REJECT":
            dns53_index = index
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
        if rule_type == "AND" and line != DOH_BOOTSTRAP_RULE:
            fail("only the exact encrypted DNS bootstrap AND rule is approved", number)
        if rule_type in {"DOMAIN", "DOMAIN-KEYWORD", "DOMAIN-SUFFIX", "DEST-PORT", "PROTOCOL"} and len(fields) != 3:
            fail(f"malformed {rule_type} rule", number)
        if rule_type in {"IP-ASN", "IP-CIDR", "IP-CIDR6"}:
            if len(fields) not in {3, 4} or (len(fields) == 4 and fields[3].lower() != "no-resolve"):
                fail(f"malformed {rule_type} rule", number)
        if rule_type == "RULE-SET":
            if len(fields) < 3 or any(option.lower() not in {"extended-matching", "no-resolve"} for option in fields[3:]):
                fail("malformed RULE-SET parameters", number)
            if len(fields) >= 2:
                source = fields[1]
                if source.startswith(("http://", "https://")):
                    external_rule_count += 1
                    fail(f"external runtime rules are forbidden; embed the audited snapshot: {source}", number)
                elif source in {"SYSTEM", "LAN"}:
                    if line != "RULE-SET,SYSTEM,Apple":
                        fail(f"unapproved built-in ruleset binding: {line}", number)
                    else:
                        system_ruleset_index = index
                elif source not in INLINE_RULESETS:
                    fail(f"undefined inline ruleset: {source}", number)
                elif source in inline_references:
                    fail(
                        f"duplicate inline ruleset reference: {source} "
                        f"(first referenced at line {inline_references[source]})",
                        number,
                    )
                else:
                    inline_references[source] = number
        if rule_type == "FINAL" and len(fields) not in {2, 3}:
            fail("malformed FINAL rule", number)
        if policy not in groups and policy not in proxy_types and policy not in BUILTIN_POLICIES:
            fail(f"rule uses an undefined policy: {policy}", number)

        target = fields[1].lower() if len(fields) > 1 else ""
        if target in APNS_TARGETS:
            if line not in APNS_PROXY_RULES:
                fail(f"APNs target must use its exact fail-closed Proxy rule: {target}", number)
            else:
                seen_apns_proxy_rules.add(line)
                apns_rule_indices.append(index)
        if rule_type == "DOMAIN-SUFFIX" and target == "akadns.net":
            fail("the whole akadns.net suffix is too broad for the APNs workaround", number)
        if upper == "DOMAIN-SUFFIX,APPLE.COM,APPLE":
            apple_domain_index = index

        direct_rule = reaches_direct(policy) or policy == "DIRECT"
        if direct_rule:
            direct_rule_indices.append(index)
        approved_system_binding = line == "RULE-SET,SYSTEM,Apple"
        approved_doh_bootstrap = line == DOH_BOOTSTRAP_RULE
        if direct_rule and rule_type == "RULE-SET" and not approved_system_binding:
            fail("only the built-in SYSTEM ruleset may feed the DIRECT-capable Apple group", number)
        elif (
            direct_rule
            and rule_type not in DIRECT_RULE_TYPES
            and not approved_system_binding
            and not approved_doh_bootstrap
        ):
            fail(f"rule type may not grant DIRECT: {rule_type}", number)
        if direct_rule and rule_type in {"IP-CIDR", "IP-CIDR6"}:
            target = fields[1] if len(fields) > 1 else ""
            direct_ip_rule = (rule_type, target, policy)
            seen_direct_ip_rules.add(direct_ip_rule)
            if direct_ip_rule not in DIRECT_IP_RULES:
                fail(f"unapproved DIRECT-capable network: {target}", number)
        if direct_rule and rule_type in {"DOMAIN", "DOMAIN-SUFFIX"} and len(fields) > 1:
            direct_domain_rules.append(f"{rule_type},{fields[1].lower()},{policy}")
        if direct_rule and policy == "DIRECT" and rule_type in {"DOMAIN", "DOMAIN-SUFFIX"}:
            target = fields[1].lower() if len(fields) > 1 else ""
            if (rule_type, target) not in DIRECT_BUILTIN_DOMAIN_RULES:
                fail(f"unapproved built-in DIRECT domain: {target}", number)
        if direct_rule and rule_type == "DOMAIN-SUFFIX":
            target = fields[1].lower() if len(fields) > 1 else ""
            if "." not in target and target != "local":
                fail(f"top-level suffix may not grant DIRECT: {target}", number)

    if doh_bootstrap_index is None:
        fail("the exact encrypted DNS bootstrap exception is required")
    if doh_index is None or [line.upper() for _, line in rules[doh_index : doh_index + 3]] != [
        "PROTOCOL,DOH,PROXY",
        "PROTOCOL,DOH3,PROXY",
        "PROTOCOL,DOQ,PROXY",
    ]:
        fail("DoH, DoH3 and DoQ proxy guards must remain contiguous")
    elif doh_bootstrap_index is not None and doh_index != doh_bootstrap_index + 1:
        fail("the exact encrypted DNS bootstrap exception must immediately precede the DoH proxy guards")
    if dns53_index is None or (doh_index is not None and dns53_index < doh_index + 3):
        fail("plain DNS port 53 guard must follow the encrypted DNS guards")

    missing_discovery_rules = sorted(DISCOVERY_DIRECT_RULES - seen_rules.keys())
    if missing_discovery_rules:
        fail(f"required local discovery exceptions are missing: {missing_discovery_rules}")
    multicast_reject_rules = {
        "IP-CIDR,224.0.0.0/4,REJECT,no-resolve",
        "IP-CIDR6,ff00::/8,REJECT,no-resolve",
    }
    missing_multicast_rejects = sorted(multicast_reject_rules - seen_rules.keys())
    if missing_multicast_rejects:
        fail(f"required multicast reject rules are missing: {missing_multicast_rejects}")
    elif not missing_discovery_rules and max(rule_indices[rule] for rule in DISCOVERY_DIRECT_RULES) >= min(
        rule_indices[rule] for rule in multicast_reject_rules
    ):
        fail("local mDNS/SSDP discovery exceptions must precede the broad multicast rejects")

    lan_direct_index = rule_indices.get("IP-CIDR,10.0.0.0/8,DIRECT,no-resolve")
    if dns53_index is not None and lan_direct_index is not None and dns53_index > lan_direct_index:
        fail("plain DNS port 53 guard must precede ordinary LAN direct rules")
    if None in {stun_index, quic_index, udp_index}:
        fail("STUN, QUIC and UDP proxy guards are all required")
    elif [line.upper() for _, line in rules[stun_index : stun_index + 3]] != [
        "PROTOCOL,STUN,PROXY",
        "PROTOCOL,QUIC,PROXY",
        "PROTOCOL,UDP,PROXY",
    ]:
        fail("STUN, QUIC and UDP proxy guards must remain contiguous")
    elif direct_rule_indices and stun_index is not None and stun_index <= max(direct_rule_indices):
        fail("generic STUN/QUIC/UDP fallback must follow every explicit DIRECT-capable rule")

    ordered_pairs = (
        ("RULE-SET,RS_ChatGPT,ChatGPT,extended-matching", "PROTOCOL,STUN,Proxy"),
        ("RULE-SET,RS_YouTube,YouTube,extended-matching", "RULE-SET,RS_Google,Google,extended-matching"),
        ("RULE-SET,RS_OneDrive,Microsoft,extended-matching", "RULE-SET,RS_Microsoft,Microsoft,extended-matching"),
        ("RULE-SET,RS_Game,Games,extended-matching", "RULE-SET,RS_Microsoft,Microsoft,extended-matching"),
        ("RULE-SET,RS_Microsoft,Microsoft,extended-matching", "PROTOCOL,STUN,Proxy"),
    )
    for before, after in ordered_pairs:
        left = rule_indices.get(before)
        right = rule_indices.get(after)
        if left is None or right is None or left >= right:
            fail(f"required rule precedence is missing: {before} before {after}")
    if len(final_entries) != 1 or final_entries[0][1].upper() != "FINAL,FINAL,DNS-FAILED":
        fail("profile must have exactly one FINAL,Final,dns-failed rule")
    if rules and final_entries and final_entries[0][0] != rules[-1][0]:
        fail("FINAL must be the last active rule", final_entries[0][0])
    final_index = rule_indices.get("FINAL,Final,dns-failed")
    if udp_index is not None and final_index is not None and udp_index + 1 != final_index:
        fail("generic UDP fallback must immediately precede FINAL")
    if external_rule_count:
        fail(f"expected no external runtime rules, found {external_rule_count}")
    for required_rule in ("DOMAIN,localhost,DIRECT", "DOMAIN,sub.store,DIRECT"):
        if required_rule not in seen_rules:
            fail(f"required local-only rule is missing: {required_rule}")
    missing_apns_proxy_rules = sorted(APNS_PROXY_RULES - seen_apns_proxy_rules)
    if missing_apns_proxy_rules:
        fail(f"required APNs Proxy rules are missing: {missing_apns_proxy_rules}")
    if apple_domain_index is None:
        fail("the audited Apple domain rule is missing")
    elif apns_rule_indices and max(apns_rule_indices) > apple_domain_index:
        fail("all APNs Proxy rules must precede the broad Apple domain rule")
    if system_ruleset_index is None:
        fail("the built-in RULE-SET,SYSTEM,Apple binding is missing")
    elif apns_rule_indices and max(apns_rule_indices) > system_ruleset_index:
        fail("all APNs Proxy rules must precede RULE-SET,SYSTEM,Apple")
    missing_direct_ip_rules = sorted(DIRECT_IP_RULES - seen_direct_ip_rules)
    if missing_direct_ip_rules:
        fail(f"required DIRECT-capable networks are missing: {missing_direct_ip_rules}")
    direct_domain_payload = ("\n".join(sorted(direct_domain_rules)) + "\n").encode("utf-8")
    direct_domain_digest = hashlib.sha256(direct_domain_payload).hexdigest()
    if (
        len(direct_domain_rules) != EXPECTED_DIRECT_DOMAIN_COUNT
        or direct_domain_digest != EXPECTED_DIRECT_DOMAIN_SHA256
    ):
        fail(
            "DIRECT-capable domain allowlist changed: "
            f"count={len(direct_domain_rules)} sha256={direct_domain_digest}"
        )
    missing_inline_rulesets = sorted(INLINE_RULESETS.keys() - inline_references.keys())
    unexpected_inline_rulesets = sorted(inline_references.keys() - INLINE_RULESETS.keys())
    if missing_inline_rulesets:
        fail(f"required inline rulesets are not referenced: {', '.join(missing_inline_rulesets)}")
    if unexpected_inline_rulesets:
        fail(f"unapproved inline rulesets are referenced: {', '.join(unexpected_inline_rulesets)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAIL: {len(errors)} issue(s)", file=sys.stderr)
        return 1

    print(
        f"PASS: {profile} | groups={len(groups)} rules={len(rules)} "
        f"inline_rulesets={len(inline_references)} inline_entries={inline_entry_total} "
        f"external_rules={external_rule_count} "
        f"direct_groups={','.join(sorted(DIRECT_GROUPS_ALLOWED))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
