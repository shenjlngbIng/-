# Changelog

## 2026-08-01 · R10.6

- 修复 Telegram 后台通知与 iOS APNs 路由冲突。
- 保持 `include-apns = false`，避免 Surge VIF 强制接管系统 APNs 长连接。
- 保留 APNs 精确 `DIRECT` 规则，作为已被捕获连接的兜底路径。
- 补充 Telegram 核心 IPv4 网段并保持全部 Telegram 流量强制进入代理策略。
- 保持 `FINAL,Final,dns-failed`，未知流量不回落到 DIRECT。
- 同步更新配置审计器、规则锁、回归测试、GitHub Actions 和说明文档。
- 清理 `SHA256SUMS.txt` 中已删除临时文件的陈旧记录。

## 2026-07-31 · R10.5

- 增加 AliDNS 与 DNSPod DoH。
- 增加 DoH 主机引导映射。
- APNs 精确规则直连；Telegram 保持代理。
- 审计器、规则锁、GitHub Actions、回归测试与文档同步升级到 R10.5。
