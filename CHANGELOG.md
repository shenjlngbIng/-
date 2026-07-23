# Changelog

## 2026-07-23 · R10.1

- 将地区组中的 `Gemini`、`GPT`、`ChatGPT`、`Claude`、`OpenAI` 视为能力标签，不再排除这些节点；名称明确包含“专用/解锁”的节点仍只保留在 `AllServer`。
- 使用真机截图中的香港、台湾、日本、新加坡和美国节点名称新增地区组回归检查，防止可用节点再次因命名标签落入 `Fail-Closed`。
- 默认关闭 `include-all-networks` 与 `include-cellular-services`，保留 `include-apns`，避免全网络接管触发请求风暴、AirDrop/Xcode 兼容问题和 iOS Network Extension 内存终止。
- 保留 `Fail-Closed`、无 `DIRECT` 代理兜底、APNs 强制代理、DNS/UDP/QUIC 闭环及 R10 固定规则快照。
- 删除 6 个未被 `r10.lock.json` 固定、未进入 `Surge.conf` 且没有运行时引用的历史规则快照；`Rules/` 现与 26 个锁定源文件严格一致。
- 同步更新 README、NOTICE、迁移说明、审计器、20 项安全变异回归测试和两套 GitHub Actions 工作流。

## 2026-07-20 · R10

- 按“国内与非推送 Apple 为明确白名单，其余境外、未知、DNS、IPv4/IPv6、UDP/STUN 不得意外直连”的模型重建配置。
- 删除可随 Surge 版本变化的 `RULE-SET,SYSTEM,Apple`，APNs 原有 4 条域名、5 条 IPv4、4 条 IPv6 代理规则和 Raw TCP 设置保持不变且继续先行。
- 删除动态 `policy-path`、Sub-Store 直连启动例外及全部外部规则 URL；公开文件只接受私有副本中的已审计静态节点。
- 将 22 个代理/拒绝源文件压平内嵌为 4483 条普通 iOS 规则，按原顺序删除 154 条不可达重复条件；不再运行时下载或刷新规则资源。
- 内嵌并清洗 4 个直连源：删除 WeChat/国内宽泛 `USER-AGENT`、腾讯 `IP-ASN`、13 条 DNS 服务域名和不明确的 Direct 项，最终保留 Apple 166 条、Domestic 882 条。
- 将服务专用代理规则保留在前，随后把 `STUN → QUIC → UDP` 守卫移到所有互联网直连白名单之前；代理不支持 UDP 时固定 `REJECT`。
- 取消 Surge 加密 DNS，保留两个明确国内传统 DNS 控制面且不含 `system`；常见应用 DoH 走代理，53/853/8853 关闭。
- 开启互联网可路由蜂窝系统服务接管，关闭 ICMP 转发、API、面板、Wi-Fi/热点共享；明确运营商私网流量仍是平台边界。
- 新增 `Rules/r10.lock.json`，固定 26 个运行时源的提交、SHA-256、数量、角色和策略。
- 将 README、NOTICE、生成器、审计器、回归测试、ZIP 暂存器和两套 GitHub Actions 工作流同步到 R10。

## 2026-07-19 · R7

- 发布移动端平衡闭锁版：继续保留 `include-all-networks=true`、`include-apns=true` 与全部 APNs 强制 `Proxy` 规则，不增加 APNs 直连或 fallback。
- 将 `ipv6-vif` 从 `always` 改为 `auto`，并关闭局域网与运营商系统业务的额外接管；README 明确记录接管面缩小及其审计边界。
- 将自动测速组从 6 个减少为仅 `Auto` 1 个；缓存周期从 600 秒延长至 1800 秒，容差从 50 ms 放宽至 150 ms。
- 将五个地区组改为手动 `select`，把 `AllServer` 调整为 `Proxy` 默认入口，避免导入后默认触发整组测速。
- 从全局 `Auto` 排除 Gemini、GPT、ChatGPT、Claude、OpenAI 及“专用/解锁”类节点，减少专用节点参与通用探测和切换；这些节点仍可手动选择。
- 扩充静态审计与回归用例，锁定唯一自动测速组、移动端网络选项、策略顺序、地区手动模式和专用节点过滤；回归变体重新计算构建摘要，确保每个用例命中自身约束。

## 2026-07-18 · R6

- 将 19 个服务规则快照与 `blackmatrix7/ios_rule_script@c00517ce10760a93728b241923a451dfa617be80` 合并，过滤 iOS 不支持或归属过宽的规则，并把运行时内嵌项从 8115 条更新到 10796 条。
- 将广告补充规则准确重命名为 `Ads_Custom_Extra.list` / `RS_Ads_Custom_Extra`。
- 为配置指定的 `223.5.5.5` DoH 增加精确冷启动例外；其他 DoH、DoH3、DoQ 继续进入 `Proxy`。
- 增加四条精确 mDNS/SSDP 局域网发现例外，更宽的多播地址继续拒绝。
- 将服务分流置于通用 STUN、QUIC、UDP 兜底之前，并固定 YouTube/Google、Game/Microsoft 等重叠规则优先级。
- 新增上游锁文件、可复现更新脚本、生成漂移检查和 push/PR GitHub Actions 审计。
- 公开配置继续拒绝设备专用 Host、真实订阅、节点和凭据；这些信息只能保留在私有副本。
