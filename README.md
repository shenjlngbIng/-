# Surge 可用性增强配置

个人 Surge 配置模板，基于 Coldvvater 的公开配置与 `Coldvvater/Mononoke`
规则整理。当前版本重点降低节点失效、DNS 故障、IPv6 网络、iOS 后台推送及
ChatGPT Voice 引起的“无网络”概率，同时保留防止流量静默直连的限制。

> **重要：**仓库中的 `Surge.conf` 是公开模板。导入前必须把
> `你的订阅地址` 替换为自己的 Surge 格式节点订阅 URL；未替换时没有可用代理
> 节点，ChatGPT、Claude、Gemini 等代理服务无法联网。不要把带令牌的私人订阅
> 地址提交到公开仓库。

## 兼容性

| 平台 | 最低建议版本 | 原因 |
| --- | --- | --- |
| Surge iOS | 5.14.6 | 配置使用全局 `block-quic` |
| Surge Mac | 5.10.3 | 配置使用全局 `block-quic` |

低于上述版本时应先升级 Surge，避免参数无法识别。Smart Group 本身要求的版本
更低，但不能代表整份配置的最低版本。

## 使用方法

1. 备份当前正在使用的配置和策略组选择。
2. 下载 `Surge.conf`，在本地精确查找 `你的订阅地址`。
3. 将其替换为 Surge 格式的节点订阅 URL；订阅不兼容时可先由 Sub-Store 转换。
4. 导入配置，打开 `AllServer`，确认能看到实际节点而不是 0 个节点。
5. 确认 `Proxy` 选中 `Auto`。旧配置升级时 Surge 可能保留原选择，需要手动切换一次。
6. 分别运行 DIRECT 与代理连通性测试；修改 APNs 接管设置后，可开关一次飞行模式重建推送连接。

主配置 Raw 地址：

```text
https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf
```

直接使用 Raw 地址不会自动填入私人订阅。若把它作为远程配置使用，仍需通过安全的
私有副本提供真实订阅地址。

## 默认分流

| 流量 | 默认策略链 | 说明 |
| --- | --- | --- |
| ChatGPT Web/App/API | `ChatGPT → Proxy → Auto` | OpenAI 核心域名和当前 Voice IP 由专用规则覆盖 |
| ChatGPT Voice | `UDP/3478 → ChatGPT → Proxy → Auto` | 位于通用 STUN 规则之前，所选节点仍须支持 UDP 转发 |
| Claude Web/API | `Claude → Proxy → Auto` | Claude Code 使用到的 GitHub/Google 资源可能进入对应服务组，但默认仍回到 `Proxy` |
| Gemini | `Gemini → Proxy → Auto` | Google 登录、公共 CDN 等共享域名可能进入 `Google → Proxy` |
| Apple、系统服务 | `DIRECT` | 减少登录、下载和系统校验随代理切换中断的概率 |
| APNs、Telegram iOS 后台通知 | `Apple Push → Fallback → 节点` | `include-apns=true`；代理全部失效时由 `Apple Push` 回退到 `DIRECT` |
| 其他境外流量 | `Final → Proxy → Auto` | `Final` 不提供 `DIRECT` 选项 |
| 明确国内服务 | `Domestic → Proxy` | 可手动切到 `DIRECT`，但会暴露真实出口 |
| 广告规则 | `AdBlock → REJECT-NO-DROP` | 怀疑误杀时可临时切到 `Proxy` 排查 |

为了避免 AI 服务的主域名与登录/CDN 使用不同出口，日常建议让 `ChatGPT`、
`Claude`、`Gemini`、`Google` 和 `GitHub` 保持默认的 `Proxy`。手动把单个 AI
服务切到某个地区组时，辅助域名可能仍经其他服务组出站。

## 可用性设计

- `Proxy` 新安装默认使用 `Auto` Smart Group，自动从 `AllServer` 的订阅节点中选择。
- `Fallback` 按订阅顺序使用首个可用节点；`Auto` 异常时可在 `Proxy` 中切换到它。
- 节点订阅每 24 小时刷新，并过滤流量、到期时间、公告等常见非节点条目。
- 地区缩写要求字母边界，避免 `US` 误匹配 Australia/Russia、`TW` 误匹配 Network；
  同时保留“港01”“美西”“台北”等常见节点命名。
- 连通性测试超时为 8 秒，减少移动网络或高延迟节点被过早判死。
- IPv6 仅在当前网络具有有效 IPv6 时接管，兼顾双栈和 IPv6-only 网络。
- Apple 普通系统规则默认直连；APNs 由 Surge 接管并优先使用 `Fallback` 中的可用代理，
  用于解决部分网络下 Telegram 等海外 App 只在前台同步、后台没有推送的问题。
- `Apple Push` 自身是回退组：代理可用时走代理，全部代理失效时走 `DIRECT`，避免国内
  App 通知也随代理故障一起中断。
- APNs 的 `akadns.net` 规则只匹配 Apple Push 专用后缀，避免误伤其他厂商域名；TCP/5223、
  `push.apple.com`、Apple EdgeKey 及官方 IPv4/IPv6 网段仍由专用规则覆盖。
- 代理 QUIC 默认阻断并回落到 HTTPS/TCP，以降低不稳定 UDP 转发造成的失败。
- 节点不支持 UDP 时使用 `REJECT`，不自动改为 `DIRECT`，防止真实出口泄漏。

## DNS 行为

- 传统 DNS：系统 DNS、`223.5.5.5`、`119.29.29.29`。
- 加密 DNS：阿里、腾讯、Cloudflare、Google 四个 DoH 端点。
- `encrypted-dns-follow-outbound-mode=false`，因此 DoH 自身使用 DIRECT 建连，避免
  代理订阅和 DNS 互相依赖形成启动死锁。
- 启用 DoH 后，传统 DNS 主要用于网络检测和解析 DoH 服务器自身，并不是普通查询
  失败后的完整明文 DNS 兜底。
- DoH 校验证书，但解析服务仍能看到查询内容及当前公网 IP。

## “无网络”排查

### ChatGPT、Claude、Gemini 同时不可用

三者默认共用 `Proxy → Auto`。同时失败通常不是三套规则一起失效，而是公共链路问题：

1. 检查 `AllServer` 是否有节点；0 个节点通常表示订阅地址、订阅格式或订阅更新失败。
2. 检查 `Proxy` 是否仍选中 `Auto`，再尝试切换为 `Fallback`。
3. 对具体节点执行代理测试；仅显示节点名称不代表节点当前可连接。
4. 查看 Surge 请求日志，确认实际链路是否为服务组、`Proxy`、`Auto`、具体节点。
5. 若所有域名都无法解析，再检查四个 DoH 端点在当前网络是否可达。

### 只有 ChatGPT Voice 不可用

Voice 优先使用 UDP/3478。网页聊天正常而语音失败时，优先更换支持 UDP Relay 的
节点；配置不会在 UDP 不可用时静默直连。OpenAI 客户端可能回落到 TCP/443，但
质量和建立连接速度可能下降。

### App 打开后局部页面提示无网络

将 `AdBlock` 临时切到 `Proxy` 后重试。若恢复，说明是广告规则误杀，不应通过修改
全局 `FINAL` 或关闭整个代理解决；应在对应规则文件中做最小范围修正。

### Apple Push 延迟，或 AirDrop/投屏异常

- 推送异常：确认 `include-apns=true`，并检查 `Apple Push` 当前是否选中了可用的
  `Fallback` 代理。更新配置后开关一次飞行模式或重启设备，让 iOS 重建 APNs 长连接。
  测试时只把 Telegram 放到后台，不要从多任务界面强制划掉。
- AirDrop、投屏、Xcode 调试异常：`include-all-networks` 可能产生系统兼容性副作用。
  排查时应同时关闭 `include-all-networks` 与依赖它的 `include-apns`，验证后再恢复。

## 安全与隐私取舍

- 配置不启用 MITM、脚本或 URL Rewrite。
- Web Dashboard、Wi-Fi 代理共享和热点代理共享默认关闭。
- DoH 校验证书；外部节点订阅也强制 `skip-cert-verify=false`。
- `include-all-networks=true` 用于降低 App 绑定物理接口绕过 VIF 的可能性，但可能影响
  AirDrop、投屏及部分调试功能；`include-apns=true` 让 APNs 也进入 Surge 路由。
- Apple 普通系统流量默认 DIRECT；APNs 优先走代理、代理全部失效时回退 DIRECT。
- `udp-policy-not-supported-behaviour=REJECT` 是有意的防泄漏选择，不建议为了语音或
  游戏方便直接改成 `DIRECT`。

## 规则维护

`Surge.conf` 中的远程规则固定到提交
`9b1432d57c9ea26ef24ea037481189743f1d73f6`，避免上游规则变化在未审计时直接影响
现网。更新规则时应同时完成以下工作：

1. 获取并检查新的规则文件。
2. 检查重复条目、CIDR 格式、未知规则类型和策略引用。
3. 验证 ChatGPT、Claude、Gemini 及 Apple 规则不会被更靠前的宽泛规则遮蔽。
4. 更新 `Surge.conf` 中所有规则 URL 的提交哈希。
5. 确认所有远程 URL 可访问后再发布。

为降低误杀造成的“无网络”，超大的 `Ads_SukkaW_Domain.list` 当前仅保留快照，
不在主配置中启用；主配置只加载 `Ads_SukkaW_Extra.list` 与 `Reject.list`。

## 目录

- `Surge.conf`：主配置模板。
- `Rules/`：主配置引用的规则文件及上游广告规则快照。
- `NOTICE.md`：上游来源和归属说明。

## 参考

- [Surge Policy Group 文档](https://manual.nssurge.com/policy-group/group.html)
- [Surge Fallback Group 文档](https://manual.nssurge.com/policy-group/fallback.html)
- [Surge General 参数文档](https://manual.nssurge.com/others/misc-options.html)
- [OpenAI：ChatGPT 网络与 Voice 要求](https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps)
- [Anthropic：Claude Code 网络配置](https://code.claude.com/docs/en/corporate-proxy)
- [NodeSeek：iOS 海外应用推送处理方法](https://www.nodeseek.com/post-709310-1)
- [Coldvvater 配置来源](https://gist.github.com/Coldvvater/8093bc6be4340b5324b4a343493becfe)
- [Coldvvater/Mononoke](https://github.com/Coldvvater/Mononoke)
