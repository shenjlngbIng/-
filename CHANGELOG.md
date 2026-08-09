# 更新日志

## 2026-08-09 R12.12 国内外总分流修正

### 修正

- 将仓库维护规则从 GitHub Raw 切换到 jsDelivr，降低中国网络环境下规则集首次加载失败的概率。
- 按 blackmatrix7/ios_rule_script 固定提交 `ccc2d6b711007324bacb55cdfbbf7e36ad48145a` 增加 Direct、China、China_Domain、Global 和 Global_Domain 五个上游总规则。
- 将 WeChat、Direct、ChinaDomain 和 GEOIP,CN 的策略统一改为 `DIRECT`，避免国内流量因手动策略组选择被误送进代理。
- 从本地 ChinaDomain 补充表中移除与上游 Global 冲突的 Battle.net、Blizzard、Futu5 和 Futunn 条目，避免国内表提前截获国外流量。
- 保留 YouTube、Google、Microsoft 等专用规则在 China/Global 总规则之前，避免专用服务被国内总规则或国外兜底覆盖。
- 删除宽泛的 QUIC、UDP 规则，仅保留 STUN 代理分流，避免不支持 UDP 的节点直接阻断 YouTube 回落到 TCP。
- 移除香港、台湾、日本、新加坡和美国地区组对“专用/解锁”节点的误排除，保留地区关键词筛选。

## 2026-08-09 R12.11 参考来源集中说明

### 文档

- 将配置参考、Sub-Store 资料、实际规则上游和本仓库维护范围集中放到 README 文末。
- 补充 Sub-Store 项目、Surge 模块和输出服务的公开地址。

## 2026-08-09 R12.10 README 用词修正

### 文档

- 删除拟人化章节名，改为“关键取舍”和“具体做法”。
- 将流程章节改为连接处理流程，保留原有图示和导航。

## 2026-08-09 R12.9 README 结构与识别度调整

### 文档

- 增加配置副标题、阅读导航和四项设计取向说明。
- 增加配置处理流程图，说明 DNS 接管、规则分流、失败关闭和最终策略之间的关系。
- 保留部署、来源、审计和故障排查内容不变。

## 2026-08-09 R12.8 参考来源说明补充

### 文档

- README 增加 Rabbit-Spec、As-Lucky、Coldvvater 和 Thoseyearsbrian Aegis 的公开来源链接。
- 明确区分设计参考、运行时规则上游和本仓库自己的整合内容。
- NOTICE.md 同步补充参考项目、许可证边界和公开包不包含的私有材料。

## 2026-08-09 R12.7 README 操作说明补全

### 文档

- 明确公开主配置、私有 policy-path、Sub-Store Surge 输出地址和可选模块地址的区别。
- 补充仓库根目录上传、覆盖、保留、漏传文件和旧版遗留目录处理方法。
- 补充 404、500、请求超时、节点全红、DNS 诊断和旧 Core/Simple 外部资源排查。
- 补充 Wi-Fi、蜂窝数据、APNs、局域网和 allow-wifi-access 的实际区别。
- 补充发布清单、GitHub Actions 和 README 修改后的校验和更新要求。

## 2026-08-09 R12.6 DNS 参考配置融合

### 修正

- 参考 Aegis，将加密 DNS 调整为阿里 DNS 的 HTTPS 与 TLS 双通道，并增加 IPv4/IPv6 引导映射。
- 将 `dns-server` 引导地址改为国内可达的阿里 DNS 地址，避免 1.1.1.1/9.9.9.9 在移动网络诊断中超时。
- 开启 `include-cellular-services = true`，减少蜂窝服务流量绕过 Surge DNS 接管的可能性。

### 取舍

- 保留 `include-local-networks = false`，避免为了 DNS 接管破坏 AirDrop、Bonjour 和局域网设备发现。
- Rabbit-Developer、Rabbit-EN、Lucky 和 Coldvvater 配置中的明文 DNS、`system` DNS 或注释状态加密 DNS 未直接照搬；只吸收其中经验证的规则集和兼容性结构。

## 2026-08-09 R12.5 远程规则集版

### 修正

- 将 27 个已审计的 `Rules/*.list` 改为仓库自有 Raw URL 的运行时 `RULE-SET`，保留原有策略映射和 `ChinaDomain` 顺序。
- 将 APNs 规则改为远程 `RULE-SET`，保留 `ApplePush` 代理优先、直连回落设计。
- `Final` 策略组加入显式 `REJECT` 选择，远程规则集或节点异常时不静默直连。
- 将审计器、规则锁、回归测试、README、发布清单和 SHA-256 校验同步到 schema 5 的 `remote-ruleset` 模式。

### 边界

- 只吸收 Aegis 和主流配置的模块化远程规则、DNS 接管、UDP 失败关闭和显式拒绝思路。
- 不直接启用未经独立复核的 `Scam_Block`、`Quarantine_Block` 或其他外部威胁情报列表，避免高误报进入主规则链路。
- 不加入 `Sub-Store Core`、`Sub-Store Simple`、Vendor 文件、真实订阅、节点、Token、密码或证书私钥。

## 2026-08-09 R12.4 DNS 隐私边界修正

### 修正

- 撤回 `system, 223.5.5.5, 119.29.29.29`，避免把系统或运营商 DNS 纳入公开隐私配置。
- 普通 DNS 恢复为 `1.1.1.1, 9.9.9.9`，仅用于加密 DNS 主机的引导与连通性用途。
- 保留阿里 DNS 与 `doh.pub` 的 HTTPS 加密 DNS，以及两个 DoH 主机的固定映射。
- 同步审计器、锁文件、README、发布清单和 SHA-256 校验值。

### 边界

- 网络诊断中 1.1.1.1/9.9.9.9 超时不应通过加入 `system` 或运营商 DNS 来掩盖。
- 不写入真实订阅地址、节点、证书私钥或重复 Sub-Store 模块。

## 2026-08-09 R12.3 国内 DNS 可达性修正

### 修正

- 将普通 DNS 恢复为 `system, 223.5.5.5, 119.29.29.29`。
- 将加密 DNS 恢复为阿里 DNS 与 `doh.pub`，并保留 `encrypted-dns-follow-outbound-mode = false`。
- 增加两个加密 DNS 主机的固定引导映射，并将对应主机规则设为 `DIRECT`。
- 同步审计器、锁文件、README、发布清单和 SHA-256 校验值。

### 边界

- 不修改或写入真实 Sub-Store 订阅地址；公开配置仍使用占位符。
- 不加入 `Sub-Store Core`、`Sub-Store Simple`、Vendor 文件、节点或证书私钥。

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
- 早期版本曾将 APNs 快照嵌入 `Surge.conf`；当前远程规则模式已移除这种做法，APNs 通过独立规则文件引用。
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
