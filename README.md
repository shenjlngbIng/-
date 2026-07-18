# Surge iOS 严格闭锁配置

这是一个面向 Surge iOS 的个人配置模板。安全基线是：**国内、非推送 Apple、精确局域网发现和两个已记录的启动控制面例外属于明确选择；APNs、境外、未知及未命中这些白名单的 DNS、IPv4/IPv6、QUIC、UDP/STUN，在节点、订阅、规则或解析失效时不得意外回落到直连。**

为处理中国内地网络下 Telegram 等境外应用的通知异常，APNs 由 Surge VIF 接管并固定进入 `Proxy`。它没有独立直连、专用 DNS 或 fallback；代理不可用时推送按设计失败，不会泄漏到真实出口。

> [!IMPORTANT]
> 公开模板不包含真实代理节点或真实订阅 URL；`AllServer` 只保留必须由使用者替换的 `policy-path` 文字占位值。零静态节点首次启动时，Sub-Store 链接必须明确追加 `proxy=DIRECT`；这只授权 Sub-Store 获取上游订阅，不是普通流量的直连兜底。若不接受这条控制面例外，应先在私有 `[Proxy]` 加入一个已审核启动节点，并让 Sub-Store 使用该节点。

## 当前审计状态

最后审计日期：**2026-07-18**

| 项目 | 当前值 |
| --- | --- |
| 目标平台 | Surge iOS |
| 最低建议版本 | 5.14.6 或更新版本 |
| 出站模式 | Rule |
| 策略组 | 31 |
| 主配置有效规则 | 326 |
| 内嵌规则集 | 22 个、10796 条有效项 |
| 外部规则 URL | 0 |
| 可到达直连的策略组 | `Domestic`、`Apple` |
| 运行时节点订阅 | 仅保留无效文字占位值；无真实 URL |
| 主配置 MITM、脚本、Rewrite | 不包含 |
| Wi-Fi/热点共享、HTTP API、Web 面板 | 未开放 |

仓库规则目录共有 32 个 `.list` 文件、135256 条有效项，其中只有 22 个被主配置加载；另有 `upstreams.lock.json` 固定服务规则来源。

## 配置来源

开发分支地址：

```text
https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf
```

`main` 是可变开发源，不是生产信任根。正式部署应在审计通过并提交后使用完整提交号：

```text
https://raw.githubusercontent.com/shenjlngbIng/-/<40位审计提交>/Surge.conf
```

配置内的 URL 注释不会自动启用托管更新；实际资源来源仍由 Surge 导入界面管理。

## 1. 威胁模型与直连边界

### 1.1 必须失败关闭

- 境外服务和未分类目标。
- Apple Push Notification service（APNs）。
- 除精确 `223.5.5.5` DoH 启动请求外的 Surge DoH、DoH3、DoQ，以及已知公共 DNS、DoT 和 HTTPDNS。
- 未知 IPv4 与 IPv6 目标。
- 未先命中已审核服务、国内或局域网规则的 STUN、QUIC 和其余 UDP。
- 代理不支持 UDP、节点连接失败或节点集合为空。
- 规则未命中、DNS 匹配失败或外部节点订阅失效。
- 外部节点订阅试图注入 `direct`、外部程序、明文代理或域名端点。

### 1.2 明确允许

- `Domestic` 中逐条内联的国内目标。
- `Apple` 中逐条内联的非 APNs Apple 目标；APNs 域名与官方网段被更早的规则固定送往 `Proxy`。
- RFC1918、回环、链路本地、IPv6 ULA 和 `.local`，作为非互联网局域网例外。
- mDNS 的 `224.0.0.251/32`、`ff02::fb/128` 与 SSDP 的 `239.255.255.250/32`、`ff02::c/128`；更宽的 IPv4/IPv6 多播仍拒绝。
- `sub.store = 127.0.0.1` 与精确的 `DOMAIN,sub.store,DIRECT` 成对锁定，只允许请求到本机回环地址，防止域名被交给远端代理解析。
- 零节点冷启动时，Sub-Store 上游订阅获取可使用链接中显式声明的 `proxy=DIRECT`。它会向订阅提供者暴露真实出口 IP，但不会把 `DIRECT` 放入任何境外业务策略组。
- `dns-server = 223.5.5.5` 仅作为传统 DNS 连通性探测；`AND,((PROTOCOL,DOH),(DOMAIN,223.5.5.5)),DIRECT` 只允许配置指定的 IP DoH 完成冷启动。其他 DoH 紧随其后进入 `Proxy`，不存在通用加密 DNS 直连。

已删除以下宽泛直连边界：

- `DOMAIN-SUFFIX,cn`。
- `100.64.0.0/10`。
- `.lan`。
- `p.to`、`miwifi.com`、`tplogin.cn`、`router.asus.com`。
- 所有 APNs 专用直连、专用 DoH 和 fallback；APNs 只保留代理路径。

## 2. 策略闭环

核心路径为：

```text
未命中 / DNS 失败
        ↓
FINAL,Final,dns-failed
        ↓
Final → Proxy
        ↓
Auto / AllServer / 地区组
        ↓
已审核静态代理，或 Fail-Closed
```

- `Final` 只有 `Proxy` 一个成员。
- `Proxy`、`Auto`、地区组和所有境外服务组都不能到达 `DIRECT`。
- `AllServer` 通过 `include-all-proxies=1` 纳入本地 `[Proxy]`，并保留 `policy-path=此处填入Sub-Store转换后的订阅链接` 作为醒目的文字占位值；`update-interval=0` 避免失败时持续自动请求，节点订阅由使用者手动更新。
- `Fail-Closed = http, 127.0.0.1, 1` 是确定不可达的失败哨兵。
- `Domestic` 与 `Apple` 是仅有的可手动选择直连策略组；APNs 规则不使用 `Apple`，因此不能随它切换到直连。
- 自定义 `direct` 代理别名被审计器禁止。

## 3. DNS 与 DoH

普通解析使用：

```ini
dns-server = 223.5.5.5
encrypted-dns-server = https://223.5.5.5/dns-query
encrypted-dns-follow-outbound-mode = true
encrypted-dns-skip-cert-verification = false
hijack-dns = *:53
```

防护顺序：

1. 只有同时匹配 `PROTOCOL,DOH` 与 `DOMAIN,223.5.5.5` 的配置内置 DoH 请求直连冷启动。
2. 其他 Surge DoH、DoH3、DoQ 紧邻命中 `Proxy`。
3. 被 VIF 看到但没有被 DNS 劫持器处理的 53 端口请求直接拒绝。
4. 853、8853、常见公共 DNS 域名/IP及固定 HTTPDNS 快照被拒绝。
5. 未识别为 DNS 的普通 HTTPS 最终进入 `Proxy`，不会因未知而直连。

`[Host]` 不再为代理节点域名指定传统 DNS，也不包含 APNs 专用解析器。代理节点必须使用 IP 字面量服务器端点，避免 DoH 通过代理时产生递归依赖。

不使用 MITM 时无法识别所有伪装成普通 HTTPS 的应用内 DoH；这类请求依靠“未知最终代理”收口，而不是内容识别。

## 4. IPv4、IPv6、UDP、QUIC 与 STUN

- `ipv6=true`、`ipv6-vif=always` 强制建立 IPv6 VIF；`compatibility-mode=3` 明确使用 VIF-only，不依赖版本对自动模式的解释。
- 四条精确 mDNS/SSDP 发现地址先行直连，更宽的 IPv4/IPv6 多播和未指定地址随后拒绝。
- 所有 IP/ASN 规则使用 `no-resolve`，避免规则匹配触发额外本地 DNS。
- 服务规则、明确局域网及国内白名单先完成分类；随后连续的 `STUN → QUIC → UDP` 规则兜住所有未分类协议流量，并紧邻 `FINAL`。
- `udp-policy-not-supported-behaviour=REJECT`，代理不支持 UDP 时拒绝，不改用直连。
- `block-quic=all-proxy` 阻断代理策略上的 QUIC，促使应用改用代理 TCP；不会产生 QUIC 直连回退。
- `icmp-forwarding=false`，不把 ICMP直接转发到物理网络。

## 5. Apple 与 APNs

APNs 使用独立的规则边界，但不创建可回落直连的策略组：

- `include-all-networks=true` 与 `include-apns=true` 确保 Surge VIF 接管 Wi-Fi 和蜂窝网络上的 APNs 流量。
- `*.push.apple.com`、APNs 的 Akamai CNAME 特征和 Apple 官方公布的 5 个 IPv4、4 个 IPv6 网段全部固定绑定 `Proxy`。
- 帖子中的 `DOMAIN-SUFFIX,akadns.net` 会覆盖大量无关 Akamai 服务，本配置收窄为 `DOMAIN-KEYWORD,push-apple.com.akadns.net`；官方网段仍完整保留。
- APNs 在 TCP 5223 建立持久连接，必要时回落 TCP 443。443 上的推送主机保持 raw TCP，避免协议嗅探干扰；这不改变策略选择。
- 没有 `APNs Direct`、`APNs Proxy`、`Apple Push`、APNs 专用 DNS 或直连 fallback。真实代理不可用时推送失败，这是严格闭锁的预期行为。
- 普通 Apple 流量仍由 `Apple` 决定；即使 `Apple` 选择 `DIRECT`，更早命中的 APNs 规则仍只走代理。
- `RULE-SET,SYSTEM,Apple` 补充 Surge 内置的 Apple 系统请求；它位于全部 APNs 强制代理规则之后，因此不会把推送重新导向 `Apple`。

导入或更新后应开关一次飞行模式，强制断开并重新建立 APNs 长连接。之后分别在 Wi-Fi 与蜂窝网络锁屏测试 Telegram 通知，并在 Surge 请求记录中确认 APNs 目标命中 `Proxy`。社区方案只能改善网络路径，不能保证 Telegram/Apple 服务端、系统通知权限或专注模式造成的问题。

## 6. 局域网与控制面

主配置未设置 `http-api`、`external-controller-access`、HTTP/SOCKS 监听地址或 VIF 排除路由，并明确设置：

```ini
allow-wifi-access = false
allow-hotspot-access = false
http-api-web-dashboard = false
proxy-restricted-to-lan = true
gateway-restricted-to-lan = true
```

局域网直连只保留私有、回环、链路本地、ULA、`.local`、`localhost`、四条精确 mDNS/SSDP 地址，以及已由 `[Host]` 固定到回环地址的 `sub.store`。CGNAT、其余多播地址和公开路由器域名不再自动直连。

## 7. 节点与 Sub-Store

### 7.1 首次部署：二选一启动方式

公开模板刻意不写入真实订阅 URL。动态订阅不可能“先通过尚未取得的代理节点去取得这些节点”，因此首次部署必须明确选择一种启动方式：

- 零静态节点：在 Sub-Store 转换链接末尾追加 `proxy=DIRECT`。原链接没有 `?` 时追加 `?proxy=DIRECT`；已有查询参数时追加 `&proxy=DIRECT`。
- 无控制面直连：先在私有 `[Proxy]` 加入一个 IP 端点、证书参数已审核的启动节点，再把链接参数写为 `proxy=<启动节点或策略名>`；参数值需要 URL 编码。

例如：

```text
https://sub.store/download/订阅名/Surge?proxy=DIRECT
https://sub.store/download/订阅名?target=Surge&proxy=DIRECT
```

随后只在设备私有副本中：

1. 在私有环境读取原订阅。
2. 使用类型过滤排除 `Direct`、明文 HTTP/SOCKS、外部程序和不受支持协议。
3. 把代理服务器域名解析为 IP；TLS 类节点必须继续保留正确 SNI/证书参数。
4. 检查端口、密码字段、证书校验、UDP 能力和异常信息节点。
5. 把 `AllServer` 中的中文占位值完整替换为已带启动参数的 Sub-Store Surge 链接；不要改动该行其他成员和过滤条件。
6. 确认订阅失效或返回异常内容时，策略仍只会进入可用代理或 `Fail-Closed`，不会出现 `DIRECT` 成员。
7. 重新检查配置并在目标设备导入；公开模板审计器会有意拒绝真实 URL，以防凭据误提交。

不要把订阅 URL、Token 或其他凭据写入公开仓库。文字占位值本身不是可用链接，未替换时 Surge 显示外部策略更新失败属于预期结果。

`proxy=DIRECT` 只解决“没有节点时如何取得节点”的闭环。若仍返回 500，错误来自 Sub-Store 生成过程或它的上游订阅，例如源订阅过期、上游拒绝请求、格式不受 Surge 支持或脚本处理失败；此时必须查看 Sub-Store 日志中的内层错误，主配置无法把真实的上游错误变成可用节点。

### 7.2 已安装模块的边界

`sub.store = 127.0.0.1` 与精确本机直连规则共同防止模块失效时请求落到不受控公共域名，但不能固定已安装模块的脚本代码。使用链接里的 `proxy=` 参数需要安装支持 `http-client-policy` ability 的官方 Sub-Store Surge 模块；如果安装的是 Noability 版本，指定策略可能不会生效。继续保留模块时，还必须单独审核模块版本、脚本 URL、定时任务、CORS、MITM 证书和所有订阅操作。

`AllServer` 上方有填写说明，实际文字占位符位于同一策略组行内：

```ini
policy-path=此处填入Sub-Store转换后的订阅链接
```

这里故意不是 URL。需要订阅时，只替换等号后的占位文字，并确保真实链接含有上述启动参数；不要删除其他失败关闭成员或过滤条件。

主配置的静态检查不能证明设备上另外安装的模块、脚本、证书或网络扩展安全。

## 8. 内嵌规则供应链

主配置把经审核的 22 个规则快照内嵌为 `[Ruleset RS_*]`，共 10796 条有效项。Surge iOS 5.7.0 起支持 Inline Ruleset；本配置最低版本 5.14.6 满足要求。

设备运行时不再访问 GitHub、jsDelivr 或任何外部规则 URL，因此截图中的规则 TLS 错误、超时和远程缓存不再属于配置启动链。每个内嵌段都由 `Rules/*.list` 的固定快照生成，审计器同时锁定名称、数量和标准化 SHA-256。

这些规则只能绑定代理或拒绝策略，不能获得 `Domestic`、`Apple` 或内置 `DIRECT`。`RULE-SET,SYSTEM,Apple` 是唯一允许绑定直连可达策略组的规则集，并被强制放在 APNs 代理规则之后。

19 个服务快照固定到 `Rules/upstreams.lock.json` 记录的 blackmatrix7 提交。更新时先审核锁文件、上游差异和排除项，再运行：

```bash
python3 tools/update_service_rules.py --download
python3 tools/embed_runtime_rules.py Surge.conf
```

随后显式更新两套审计哈希并运行全部检查。不能直接在内嵌段中手改后跳过源文件；`python3 tools/embed_runtime_rules.py Surge.conf --check` 会验证生成结果没有漂移。

## 9. 自动审计

本地运行：

```bash
python3 tools/audit_config.py Surge.conf
python3 tools/audit_rules.py Rules --profile Surge.conf
python3 tools/test_audit_config.py
python3 tools/test_stage_surge_zip.py
python3 tools/update_service_rules.py --verify-lock
python3 tools/embed_runtime_rules.py Surge.conf --check
```

当前预期输出：

```text
PASS: Surge.conf | groups=31 rules=326 inline_rulesets=22 inline_entries=10796 external_rules=0 direct_groups=Apple,Domestic
PASS: Rules | files=32 active_entries=135256 target=Surge-iOS runtime_files=22 runtime_entries=10796
PASS: audit_config regression cases=40
PASS: ZIP allowlist regression cases=10
PASS: verified upstream lock services=19
PASS: generated profile is current: Surge.conf
```

`.github/workflows/audit.yml` 会在每次 push、pull request 和手动触发时重复这些检查。现有 ZIP 工作流只负责安全暂存和审计手动候选包。

配置审计器还会拒绝：

- 除 `AllServer` 精确文字占位值外的任何 `policy-path`（包括意外提交的真实 URL）、托管 include 和未解析区段。
- 自定义 `direct`、外部代理程序、未批准协议、明文 HTTP/SOCKS 代理和弱 Shadowsocks 加密。
- 域名形式的代理服务器端点。
- 越界端口、策略组循环和关闭或削弱 TLS 证书验证。
- APNs 直连/fallback 策略、专用 Host、非精确 DoH 直连、错误策略绑定，以及过宽的整个 `akadns.net` 匹配。
- 任意外部规则 URL、缺失/重复的内嵌规则集或内嵌快照哈希变化。
- SYSTEM 规则越过 APNs、绑定内置 `DIRECT`，或已审核直连域名集合发生变化。
- 缺失或顺序错误的精确 DoH 冷启动、DNS、mDNS/SSDP、服务优先级、STUN、QUIC、UDP 和 FINAL 守卫。
- CGNAT、公开路由器域名或顶级公共后缀重新获得直连。

这些脚本不是 Surge 官方解析器。静态检查通过后仍必须在目标 Surge iOS 版本真机导入。

## 10. 真机验收

在 Wi-Fi 与蜂窝、IPv4 与 IPv6 下分别测试：

- 未知域名命中 `Final → Proxy`。
- 全部真实节点关闭时，境外网站失败而不显示本地公网 IP。
- 清除 DNS/规则缓存后，指定 `223.5.5.5` DoH 可以冷启动；其他 DoH 随代理失败，不出现运营商 DNS 业务回退。
- 未命中明确服务、国内或局域网白名单的 STUN、QUIC 和其他 UDP 只显示代理出口或失败。
- 代理不支持 UDP 时请求被拒绝。
- 在阻断 GitHub/jsDelivr 的环境重新载入配置，22 个内嵌规则集仍可用且外部资源页不再列出它们。
- `Domestic` 与 `Apple` 的当前手动选择符合预期；APNs 域名和官方网段无论 `Apple` 如何选择都命中 `Proxy`。
- 局域网必要设备以及 mDNS/SSDP 发现仍可用，CGNAT、其余多播和公开路由器域名不再自动直连。
- 其他设备无法连接本机代理、API 或面板。
- 请求日志中没有未审核模块、脚本、额外 DNS 或外部策略订阅。

最好通过路由器日志或旁路抓包核对：除国内、Apple、明确局域网以及建立代理隧道所需的节点 IP/端口外，不应出现其他物理出口连接。

## 11. 已知平台边界

- `include-all-networks` 能扩大接管范围，但不能证明 iOS 所有系统保留流量都进入第三方网络扩展。
- 代理客户端必然需要直接连接代理节点本身；节点 IP/端口属于隧道基础设施，必须静态审核和允许。
- 不使用 MITM 时无法准确分类所有新型应用内加密 DNS。
- 固定域名、IP 和 ASN 快照会老化，需要按同一审计流程更新。
- 配置无法约束设备上其他 VPN、描述文件、私有中继或网络扩展。

## 12. 来源与许可

完整第三方来源、许可证、规则修改与数据处理说明见 [`NOTICE.md`](NOTICE.md) 和 `THIRD_PARTY_LICENSES/`；版本变化见 [`CHANGELOG.md`](CHANGELOG.md)。

本仓库没有统一项目许可证。公开可见不等于自动获得复制、修改、商业使用或再分发授权。

## 参考资料

- [Surge 官方手册](https://manual.nssurge.com/)
- [Surge 加密 DNS](https://manual.nssurge.com/dns/doh.html)
- [Surge 策略包含](https://manual.nssurge.com/policy-group/policy-including.html)
- [Surge 规则集](https://manual.nssurge.com/rule/ruleset.html)
- [Surge General 选项](https://manual.nssurge.com/others/misc-options.html)
- [Apple APNs 网络要求](https://support.apple.com/zh-cn/102266)
- [NodeSeek APNs 推送讨论存档](https://web.archive.org/web/20260715022631/https://www.nodeseek.com/post-709310-1)
- [Sub-Store 官方仓库](https://github.com/sub-store-org/Sub-Store)
