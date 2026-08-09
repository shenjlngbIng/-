# 更新日志

## 2026-08-09 R12.2 加密 DNS 循环修正

### 修正

- 将 `encrypted-dns-follow-outbound-mode` 从 `true` 改为 `false`。
- 加密 DNS 固定直连并绕过代理规则，避免节点服务器域名被同一代理策略再次解析而形成循环。
- 保留 HTTPS 加密 DNS、有效协议规则快照、节点失败关闭和其他分流逻辑不变。

### 边界

- 不在公开配置中写入节点 IP、真实订阅链接或其他私有信息。
- 不通过 `DOMAIN,gd.bjnet2.com,DIRECT` 等规则掩盖代理服务器自身的 DNS 引导问题。

## 2026-08-09 R12.1 代理回落修正版

### 修正

- `AllServer` 恢复为 `fallback`，增加 60 秒检测、300 秒节点超时和启动前评估。
- 默认 `Proxy` 优先使用 `AllServer`，避免首次载入时直接落到空的地区组。
- 代理健康检测超时恢复为 8 秒，降低移动网络下的误判。
- 移除主配置中的 `sub.store` 本地地址映射，由独立 Sub-Store 模块处理订阅转换。
- 保留现有 ChinaDomain 顺序、规则快照、APNs、加密 DNS 和失败关闭设计。

### 边界

- 不加入 `Sub-Store Core` 或 `Sub-Store Simple` 内嵌脚本。
- 不写入真实订阅链接、节点、密码、Token 或 MITM 证书。
- 不增加运行时远程 `RULE-SET`，不增加 P2P 端口直连。

## 2026-08-08 R12

### 修正

- APNs 改为独立 `ApplePush` Fallback，代理优先、直连故障回落。
- 启用 `include-all-networks` 与 `include-apns`，覆盖移动数据下的系统推送。
- 加入 APNs 本地快照，并同步嵌入 `Surge.conf`，避免运行时依赖远程规则。
- 加密 DNS 改用 Cloudflare 与 Quad9 IP 端点，按 `EncryptedDNS` 代理优先、加密直连回落。
- 保持 Telegram 强制代理及既有国内外分流，不引入全量 Apple 代理规则。

### 校验

- 审计器、锁文件、回归测试和工作流统一升级为 R12。
- 增加发布文件清单，发布包按清单核对文件数量与 SHA-256。

## 2026-08-01 R11 LTS

### 新增

- 新增仓库级 `LICENSE`。
- 新增 `tools/generate_checksums.py`，统一生成发布文件校验和。
- GitHub Actions 增加 Python 3.12 与 3.13 双版本审计。
- README 增加完整目录、工具、工作流、FAQ 和故障排查说明。

### 优化

- 配置注释统一为简短文字标题，不使用装饰性横线。
- 统一审计脚本、锁文件、文档和工作流的 R11 LTS 版本标识。
- `audit_rules.py` 支持验证仓库规则目录和 ZIP 暂存规则目录。
- 完善 `.gitignore`，排除缓存、临时文件、压缩包和本地敏感配置。
- 工作流增加并发控制、超时限制、编译检查和 SHA-256 校验。

### 保持

- Telegram 强制代理。
- 系统 APNs 不由 Surge VIF 接管。
- APNs 精确直连兜底。
- `FINAL,Final,dns-failed` 失败关闭。
- 5546 条有效规则及既有规则顺序。

## 2026-08-01 R10.6

- 修复 Telegram 后台通知与 APNs 路由冲突。
- 补充 Telegram 核心网段。
- 清理旧校验和记录。

## 2026-07-31 R10.5

- 启用 AliDNS 与 DNSPod DoH。
- 增加 DNS 引导映射和防绕过规则。
- 同步配置审计、规则锁和回归测试。
