# 更新日志

## 2026-08-01 R11 LTS

### 优化

- 将配置注释统一为简短文字标题，移除装饰性分隔线和重复说明。
- 重写 README，补充安装、策略、DNS、Telegram、APNs、维护和故障排查说明。
- 统一审计脚本、锁文件和 GitHub Actions 的版本标识。
- 更新校验和并补充安全与贡献文档。

### 保持

- Telegram 强制代理。
- 系统 APNs 不由 Surge VIF 接管。
- APNs 精确直连兜底。
- `FINAL,Final,dns-failed` 失败关闭。
- 5546 条有效规则及原有规则顺序。

## 2026-08-01 R10.6

- 修复 Telegram 后台通知与 APNs 路由冲突。
- 补充 Telegram 核心网段。
- 清理旧校验和记录。

## 2026-07-31 R10.5

- 启用 AliDNS 与 DNSPod DoH。
- 增加 DNS 引导映射和防绕过规则。
- 同步配置审计、规则锁和回归测试。
