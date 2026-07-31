# Changelog

## 2026-07-31 · R10.5

- 增加 AliDNS 与 DNSPod DoH：`https://dns.alidns.com/dns-query`、`https://doh.pub/dns-query`。
- 增加 DoH 主机引导映射，避免加密 DNS 首次解析形成循环依赖。
- `dns.alidns.com` 与 `doh.pub` 固定直连，其余未批准 DNS 继续进入代理或拒绝闭环。
- 保持 `FINAL,Final,dns-failed`，不允许未知流量回落到 DIRECT。
- 保持 iOS 稳定接管边界：四项 `include-*` 均为 `false`。
- APNs 精确捕获规则调整为 DIRECT；Telegram 保持代理。
- 审计器、规则锁、GitHub Actions、回归测试与文档同步升级到 R10.5。
- 当前有效规则：5546；完整规则重复项：0。
