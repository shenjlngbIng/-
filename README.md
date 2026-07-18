# Surge iOS 严格闭锁配置

这是一个面向 Surge iOS 的个人配置模板。安全基线是：**国内与非推送 Apple 流量的既有直连属于明确选择；APNs、境外、未知、业务 DNS、IPv4/IPv6、QUIC、UDP/STUN 在节点、订阅、规则或解析失效时不得意外回落到直连。**

为处理中国内地网络下 Telegram 等境外应用的通知异常，APNs 由 Surge VIF 接管并固定进入 `Proxy`。它没有独立直连、专用 DNS 或 fallback；代理不可用时推送按设计失败，不会泄漏到真实出口。

> [!IMPORTANT]
> 公开模板不包含真实代理节点或真实订阅 URL；`AllServer` 只保留一段必须由使用者替换的 `policy-path` 文字占位值。未替换时外部策略更新会失败；没有可用代理时，境外、未知和普通加密 DNS 会按设计失败，而不是改用 `DIRECT`。

## 当前审计状态

最后审计日期：**2026-07-18**

| 项目 | 当前值 |
| --- | --- |
| 目标平台 | Surge iOS |
| 最低建议版本 | 5.14.6 或更新版本 |
| 出站模式 | Rule |
| 策略组 | 31 |
| 主配置有效规则 | 320 |
| 运行时远程规则集 | 22 |
| 固定规则快照 | 22 个文件、8115 条有效项 |
| 可到达直连的策略组 | `Domestic`、`Apple` |
| 运行时节点订阅 | 仅保留无效文字占位值；无真实 URL |
| 主配置 MITM、脚本、Rewrite | 不包含 |
| Wi-Fi/热点共享、HTTP API、Web 面板 | 未开放 |

仓库规则目录共有 32 个文件、132575 条有效项，其中只有 22 个被主配置加载。

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
- Surge 自身的 DoH、DoH3、DoQ，以及已知公共 DNS、DoT 和 HTTPDNS。
- 未知 IPv4 与 IPv6 目标。
- 所有可识别 STUN、QUIC 和其余 UDP。
- 代理不支持 UDP、节点连接失败或节点集合为空。
- 远程规则下载失败、规则未命中或 DNS 匹配失败。
- 外部节点订阅试图注入 `direct`、外部程序、明文代理或域名端点。

### 1.2 明确允许

- `Domestic` 中逐条内联的国内目标。
- `Apple` 中逐条内联的非 APNs Apple 目标；APNs 域名与官方网段被更早的规则固定送往 `Proxy`。
- RFC1918、回环、链路本地、IPv6 ULA 和 `.local`，作为非互联网局域网例外。
- `sub.store = 127.0.0.1` 与精确的 `DOMAIN,sub.store,DIRECT` 成对锁定，只允许请求到本机回环地址，防止域名被交给远端代理解析。
- `dns-server = 223.5.5.5` 仅作为 Surge 传统 DNS 连通性探测；业务解析使用加密 DNS。它是已记录的探测元数据例外，不是加密 DNS 失败后的业务回退。

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
- `AllServer` 通过 `include-all-proxies=1` 纳入本地 `[Proxy]`，并保留 `policy-path=此处填入Sub-Store转换后的订阅链接` 作为醒目的文字占位值；未替换时不会得到订阅节点。
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

1. Surge 自身的 DoH、DoH3、DoQ 全部进入 `Proxy`。
2. 被 VIF 看到但没有被 DNS 劫持器处理的 53 端口请求直接拒绝。
3. 853、8853、常见公共 DNS 域名/IP及固定 HTTPDNS 快照被拒绝。
4. 未识别为 DNS 的普通 HTTPS 最终进入 `Proxy`，不会因未知而直连。

`[Host]` 不再为代理节点域名指定传统 DNS，也不包含 APNs 专用解析器。代理节点必须使用 IP 字面量服务器端点，避免 DoH 通过代理时产生递归依赖。

不使用 MITM 时无法识别所有伪装成普通 HTTPS 的应用内 DoH；这类请求依靠“未知最终代理”收口，而不是内容识别。

## 4. IPv4、IPv6、UDP、QUIC 与 STUN

- `ipv6=true`、`ipv6-vif=always` 强制建立 IPv6 VIF；`compatibility-mode=3` 明确使用 VIF-only，不依赖版本对自动模式的解释。
- IPv4/IPv6 多播和未指定地址先行拒绝。
- 所有 IP/ASN 规则使用 `no-resolve`，避免规则匹配触发额外本地 DNS。
- `PROTOCOL,STUN,Proxy`、`PROTOCOL,QUIC,Proxy`、`PROTOCOL,UDP,Proxy` 位于所有直连规则之前。
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

局域网直连只保留私有、回环、链路本地、ULA、`.local`、`localhost`，以及已由 `[Host]` 固定到回环地址的 `sub.store`。CGNAT 地址和公开路由器域名不再自动直连。

## 7. 节点与 Sub-Store

### 7.1 严格部署流程

公开模板刻意不写入真实订阅 URL。若要使用 `policy-path` 连接 Sub-Store 转换结果，应只在私有副本中：

1. 在私有环境读取原订阅。
2. 使用类型过滤排除 `Direct`、明文 HTTP/SOCKS、外部程序和不受支持协议。
3. 把代理服务器域名解析为 IP；TLS 类节点必须继续保留正确 SNI/证书参数。
4. 检查端口、密码字段、证书校验、UDP 能力和异常信息节点。
5. 优先将审核结果静态写入私有副本的 `[Proxy]`；若确需运行时订阅，再把 `AllServer` 中的文字占位值替换为 Sub-Store 转换后的 Surge 订阅 URL。
6. 确认订阅失效或返回异常内容时，策略仍只会进入可用代理或 `Fail-Closed`，不会出现 `DIRECT` 成员。
7. 重新检查配置并在目标设备导入；公开模板审计器会有意拒绝真实 URL，以防凭据误提交。

不要把订阅 URL、Token 或其他凭据写入公开仓库。文字占位值本身不是可用链接，未替换时 Surge 显示外部资源更新失败属于预期结果。

### 7.2 已安装模块的边界

`sub.store = 127.0.0.1` 与精确本机直连规则共同防止模块失效时请求落到不受控公共域名，但不能固定已安装模块的脚本代码。严格部署完成静态导出后，应停用或卸载标准 Sub-Store 模块；如果继续保留，必须单独审核模块版本、脚本 URL、定时任务、CORS、MITM 证书和所有订阅操作。

`AllServer` 上方有填写说明，实际文字占位符位于同一策略组行内：

```ini
policy-path=此处填入Sub-Store转换后的订阅链接
```

这里故意不是 URL。需要订阅时，只替换等号后的占位文字，不要删除其他失败关闭成员或过滤条件。

主配置的静态检查不能证明设备上另外安装的模块、脚本、证书或网络扩展安全。

## 8. 远程规则供应链

运行时加载的 22 个规则文件全部使用 HTTPS，并固定到完整提交：

```text
8099f3036f0f1ebde038abff98cbaec9409cd430
```

这些规则只能绑定代理或拒绝策略，不能获得 `Domestic`、`Apple` 或内置 `DIRECT`。`audit_rules.py` 除了核对语法和数量，还固定检查全部 22 个运行时文件的 SHA-256；内容变化必须先审核并显式更新清单。

固定提交减少路径内容静默变化，但仍依赖 GitHub、jsDelivr、TLS、设备时钟和 Surge 的外部资源缓存。规则获取失败时，未命中流量仍由 `FINAL → Proxy` 收口；真机仍需验证旧缓存和配置激活行为。

## 9. 自动审计

本地运行：

```bash
python3 tools/audit_config.py Surge.conf
python3 tools/audit_rules.py Rules --profile Surge.conf
python3 tools/test_audit_config.py
```

当前预期输出：

```text
PASS: Surge.conf | groups=31 rules=320 remote_rules=22 direct_groups=Apple,Domestic
PASS: Rules | files=32 active_entries=132575 target=Surge-iOS runtime_files=22 runtime_entries=8115
PASS: audit_config regression cases=23
```

`.github/workflows/audit.yml` 会在每次 push、pull request 和手动触发时重复这些检查。现有 ZIP 工作流只负责安全暂存和审计手动候选包。

配置审计器还会拒绝：

- 除 `AllServer` 精确文字占位值外的任何 `policy-path`（包括意外提交的真实 URL）、托管 include 和未解析区段。
- 自定义 `direct`、外部代理程序、未批准协议、明文 HTTP/SOCKS 代理和弱 Shadowsocks 加密。
- 域名形式的代理服务器端点。
- 越界端口、策略组循环和关闭或削弱 TLS 证书验证。
- APNs 直连/fallback 策略、专用 Host、直连 DoH、错误策略绑定，以及过宽的整个 `akadns.net` 匹配。
- 远程直连规则、非固定提交规则 URL。
- 运行时规则快照哈希或已审核直连域名集合发生变化。
- 缺失或顺序错误的 DNS、STUN、QUIC、UDP 和 FINAL 守卫。
- CGNAT、公开路由器域名或顶级公共后缀重新获得直连。

这些脚本不是 Surge 官方解析器。静态检查通过后仍必须在目标 Surge iOS 版本真机导入。

## 10. 真机验收

在 Wi-Fi 与蜂窝、IPv4 与 IPv6 下分别测试：

- 未知域名命中 `Final → Proxy`。
- 全部真实节点关闭时，境外网站失败而不显示本地公网 IP。
- 清除 DNS/规则缓存后，普通 DoH 随代理失败，不出现运营商 DNS 业务回退。
- STUN、QUIC 和其他 UDP 只显示代理出口或失败。
- 代理不支持 UDP 时请求被拒绝。
- 阻断 GitHub/jsDelivr 后，远程规则失败不扩大直连。
- `Domestic` 与 `Apple` 的当前手动选择符合预期；APNs 域名和官方网段无论 `Apple` 如何选择都命中 `Proxy`。
- 局域网必要设备仍可访问，CGNAT和公开路由器域名不再自动直连。
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

完整第三方来源、许可证、规则修改与数据处理说明见 [`NOTICE.md`](NOTICE.md) 和 `THIRD_PARTY_LICENSES/`。

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
