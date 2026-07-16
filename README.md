# Surge iOS 严格闭锁配置

这是一个面向 Surge iOS 的个人配置模板。当前维护基线是：**国内与 Apple 的既有直连属于明确选择；所有境外、未知、通用 DNS、IPv6、UDP/STUN 不得在节点、规则或远程服务失效时意外回落到直连；APNs 保留代理优先、代理不可用时直连的特殊设计。**

> [!IMPORTANT]
> 公开模板不包含任何真实代理节点，不能直接当作完整可用配置。未加入节点时，境外和未知流量会按设计失败关闭；普通域名的 DoH 也无法建立，因此依赖普通 DNS 解析的国内或 Apple 域名可能同样不可用。局域网、IP 字面量目标，以及使用专用直连 DoH 的 APNs 路径，可能仍按各自规则工作。

## 当前状态

最后审计日期：**2026-07-17**

| 项目 | 当前值 |
| --- | --- |
| 目标平台 | Surge iOS |
| 最低建议版本 | 5.14.6 或更新版本 |
| Smart 策略要求 | 需要 Surge iOS 功能订阅解锁 |
| 出站模式 | Rule |
| 公开模板真实代理节点 | 0 |
| 策略组 | 33 |
| 主配置有效规则 | 323 |
| 运行时远程规则集 | 22 |
| 允许包含直连的策略组 | `Domestic`、`Apple`、`Apple Push` |
| 本地规则快照 | 32 个文件、132599 条有效项 |
| 独立带宽测速功能/策略组 | 不包含 |
| 必要健康/延迟检测 | 保留，使用 Surge iOS 兼容的 HTTP 探测端点 |
| 运行时节点订阅 | 不包含 |
| MITM、脚本、URL Rewrite | 不包含 |
| Wi-Fi/热点共享、HTTP API、Web 面板 | 未开放 |

以上数字由仓库内静态检查器生成。修改规则或策略后应重新运行检查，不应把表中数字永久视为安全证明。

## 1. 威胁模型

### 1.1 需要阻止的失效行为

本配置重点防止以下流量因为节点故障、订阅失效、规则下载失败、DNS 故障或协议不受支持而转为 `DIRECT`：

- 境外服务和未分类目标。
- 通用 DoH、DoH3、DoQ、DoT、应用内 HTTPDNS 及硬编码 DNS。
- IPv4 未知地址和 IPv6 未知地址。
- STUN，以及最终应由代理承载的 UDP。
- 代理路径上的 QUIC。
- 远程规则未命中、加载失败或缓存不可用后的最终流量。
- 未审核节点订阅、外部代理程序或可变内置规则集带来的隐式扩权。

### 1.2 明确允许的直连边界

以下直连属于配置设计的一部分，不应被误报为“意外泄漏”：

- `Domestic` 中经过审核并内联的国内目标。
- `Apple` 中经过审核并内联的 Apple 目标。
- `Apple Push` 在代理路径不可用时选择 `APNs Direct`。
- 明确内联的局域网、回环、链路本地和 ULA 地址。
- 路由器管理域名、`.local`、`.lan` 和简单主机名。
- Apple 网络连通性页面 `captive.apple.com`。
- APNs 专用解析器 `223.6.6.6` 的精确 DoH 例外。

`Domestic` 和 `Apple` 是可手动选择的策略组。用户将它们保持为 `DIRECT` 代表主动接受目标服务看到真实公网 IP；切换为 `Proxy` 则可以缩小直连范围。

### 1.3 不作出的保证

本配置不等于匿名工具，也不能单独证明以下对象可信：

- 代理提供者、代理节点运营者及其日志策略。
- DNS 服务商、运营商、目标网站或 CDN。
- 设备上另外安装的模块、脚本、证书、描述文件、其他 VPN 或网络扩展。
- 平台未交给 Surge 接管的系统保留流量。
- 新出现且伪装成普通 HTTPS 的应用内加密 DNS。
- 规则来源的版权、许可证完整性或目标域名长期准确性。

## 2. 策略闭环

### 2.1 核心策略

| 策略 | 类型 | 可到达直连 | 作用 |
| --- | --- | --- | --- |
| `Final` | `select` | 否 | 所有未知流量进入 `Proxy` |
| `Proxy` | `select` | 否 | 代理总入口，只能选自动、全部节点或地区组 |
| `Auto` | `url-test` | 否 | 从 `AllServer` 中按 HTTP 探测延迟选择节点 |
| `AllServer` | `select` | 否 | 只收集本地 `[Proxy]` 内经审核的节点 |
| `HongKong` 等地区组 | `url-test` | 否 | 按节点名称筛选并测试地区节点 |
| 各境外服务组 | `select` | 否 | AI、开发、流媒体、社交和游戏平台分流 |
| `Domestic` | `select` | 是 | 明确国内目标，默认可直连，也可手动改为代理 |
| `Apple` | `select` | 是 | 明确 Apple 目标，默认可直连，也可手动改为代理 |
| `APNs Proxy` | `smart` | 否 | APNs 的代理优先路径 |
| `Apple Push` | `fallback` | 是 | `APNs Proxy` 失败后才使用 `APNs Direct` |
| `AdBlock` | `select` | 否 | 默认使用拒绝策略，也可手动改为代理 |
| `Fail-Closed` | 本地不可达代理 | 否 | 没有真实节点时制造确定失败，不提供直连出口 |

`Proxy`、`Auto`、地区组和境外服务组均没有 `DIRECT` 成员。`AllServer` 排除 `Fail-Closed`、`APNs Direct` 和常见订阅信息节点，避免伪节点进入正常代理选择。

### 2.2 规则顺序

Surge 按从上到下的顺序匹配规则。当前主配置依次处理：

1. 多播、广播和未指定地址拒绝。
2. ChatGPT Voice 官方地址，确保其 UDP 在通用 STUN 规则前进入代理策略。
3. APNs 专用 DoH 精确直连例外。
4. 其余 DoH、DoH3、DoQ 强制进入 `Proxy`。
5. 常见 DoT、公共 DNS、已知 DoH 和 HTTPDNS 入口拒绝。
6. 所有可识别 STUN 强制进入 `Proxy`。
7. 局域网、回环、链路本地和 ULA 直连。
8. APNs 域名及 IPv4/IPv6 网段进入 `Apple Push`。
9. Apple、广告、国内和境外服务的精确分流。
10. `FINAL,Final,dns-failed` 收口所有未知和解析失败流量。

重要顺序由 `tools/audit_config.py` 固化检查。若把 STUN、加密 DNS或 `FINAL` 移到宽泛直连规则之后，审计会失败。

### 2.3 为什么不使用宽泛直连来源

本配置不使用 `GEOIP,CN`、`RULE-SET,SYSTEM,DIRECT`、`RULE-SET,LAN,DIRECT` 或运行时远程国内规则授予直连。原因是：

- 地理数据库和内置规则内容会随版本或数据库更新变化。
- 远程直连规则一旦被污染，能够立即扩大真实 IP 暴露范围。
- 远程规则加载失败时，故障行为更难判断。
- 将直连边界内联后，代码审查可以看到每一条获准直连的规则。

局域网和已审核的国内、Apple、APNs 规则因此直接写在 `Surge.conf` 中；远程规则只能进入代理或拒绝策略。

## 3. DNS 与 DoH

### 3.1 普通解析路径

普通域名使用：

```ini
encrypted-dns-server = https://223.5.5.5/dns-query
encrypted-dns-follow-outbound-mode = true
encrypted-dns-skip-cert-verification = false
```

解析器使用 IP 字面量端点，不需要先用明文 DNS 解析 DoH 主机名；证书校验保持开启。规则区又将 `PROTOCOL,DOH`、`PROTOCOL,DOH3` 和 `PROTOCOL,DOQ` 送入 `Proxy`，因此普通 DoH 不会因代理失效而转为直连。

`dns-server = 223.5.5.5` 按 Surge 的配置语义用于连通性检查，不是普通加密 DNS 失败后的明文解析回退。它仍可能产生直连探测元数据，隐私影响见 `NOTICE.md`。

### 3.2 APNs 独立解析路径

`[Host]` 只为 APNs 相关域名和 Apple 健康检测域名指定：

```ini
server:https://223.6.6.6/dns-query
```

规则仅允许目标为 `223.6.6.6:443` 且协议被 Surge 识别为 DoH 的连接直连。随后的通用 DoH 规则仍进入 `Proxy`，而直接访问该 IP 的普通 HTTPS、UDP 或其他端口会被后续规则拒绝，不会因为地址相同而获得宽泛直连权限。

这条例外是 APNs 失效时仍能完成域名解析和直连回退的必要组成部分。删除它会破坏特殊 APNs 设计。

### 3.3 应用绕过防护

当前配置采用以下措施：

- `hijack-dns = *:53` 接管应用发往任意服务器的 53 端口 DNS。
- TCP/UDP 853 和 8853 被拒绝，覆盖常见 DoT/DoQ 端口。
- 常见公共 DNS 域名和 IPv4/IPv6 地址被拒绝。
- blackmatrix7 的 `BlockHttpDNS` 固定快照已内联，拒绝常见应用 HTTPDNS 域名和地址。
- 未识别的新 DoH 若表现为普通 HTTPS，无法仅靠端口无误识别；它仍会按服务规则或 `FINAL` 进入代理，而不是未知直连。

不使用 MITM 的前提下，无法完整识别所有应用自定义的加密 DNS。配置选择“未知最终代理”，而不是声称能够看见所有 DNS 内容。

### 3.4 无节点时的 DNS 行为

公开模板没有真实节点，因此普通 DoH 会进入 `Proxy` 后失败。结果是：

- 需要普通 DNS 解析的境外、国内和 Apple 域名都可能失败。
- 这不是 DNS 泄漏，而是失败关闭的预期结果。
- 局域网 IP、IP 字面量目标和已经有缓存的地址可能表现不同。
- APNs 使用独立的直连 DoH，仍有机会按专用路径工作。

添加至少一个可用且已审核的真实代理节点后，普通 DoH 才具备完整工作条件。

## 4. IPv4、IPv6、UDP、QUIC 与 STUN

### 4.1 IPv4 与 IPv6

- `ipv6 = true` 和 `ipv6-vif = auto` 保持 IPv6 接管，不通过关闭 IPv6 掩盖泄漏。
- IPv4/IPv6 多播及未指定地址先行拒绝。
- 回环、链路本地和 ULA 是明确局域网直连例外。
- APNs 的 IPv6 网段进入 `Apple Push`，不会落入通用直连。
- 其他 IPv6 目标与 IPv4 一样继续匹配服务规则，最终由 `Final -> Proxy` 收口。

如果代理节点或服务商不支持 IPv6，失败应留在代理路径中解决，不应通过新增 IPv6 直连兜底规避。

### 4.2 UDP 与 STUN

- `PROTOCOL,STUN,Proxy` 位于所有宽泛直连规则之前。
- `udp-policy-not-supported-behaviour = REJECT` 确保所选代理不支持 UDP 时直接拒绝。
- 未知 UDP 由 `FINAL` 进入 `Proxy`。
- 国内或 Apple 目标上的 UDP 可能因其目的地址已明确归入直连策略而直连，这属于既有直连选择，不是协议失败回落。

WebRTC 是否泄漏还取决于应用实现、系统行为和真机网络环境，必须通过真机测试验证，不能仅凭配置文本下结论。

### 4.3 QUIC

`block-quic = all-proxy` 禁止代理策略上的 QUIC，避免应用因为代理 UDP/QUIC 不兼容而出现不可控路径。国内、Apple 或 APNs 已明确选择直连时仍可能使用 QUIC，这是直连策略的正常结果。

该选项要求 Surge iOS 5.14.6 或更新版本。旧版本可能拒绝导入或忽略语义，不属于支持范围。

## 5. APNs 特殊设计

APNs 不是普通 Apple 直连规则，而是单独的两级策略：

1. APNs 域名及明确网段进入 `Apple Push`。
2. `Apple Push` 首选 `APNs Proxy`。
3. `APNs Proxy` 通过 `smart` 从 `AllServer` 选择真实代理节点。
4. `Fail-Closed` 被赋予较低优先级，仅在没有真实节点时充当失败哨兵。
5. 代理路径不可用后，`fallback` 才选择 `APNs Direct`。
6. APNs 域名通过专用直连 DoH 解析，使直连回退不依赖已经失败的普通代理 DoH。

因此 APNs 的目标是“可用性优先但不静默直连”：平时优先代理；只有专用策略明确确认代理不可用后，才使用可见的直连成员。直连时 Apple 和 APNs 解析服务会看到真实出口 IP，这是已接受的隐私代价。

不要进行以下修改：

- 不要把 `APNs Direct` 加入 `Proxy` 或 `AllServer`。
- 不要把 APNs 规则并入普通 `Apple` 组。
- 不要删除 APNs 专用 DoH 的精确逻辑规则。
- 不要把 `Apple Push` 改为包含 `DIRECT` 的普通手选组。
- 不要让远程规则获得 `Apple Push` 或 `DIRECT` 策略。

## 6. 网络接管与控制面

当前网络相关设置包括：

- 接管所有网络、局域网、APNs 和蜂窝服务选项。
- 关闭 Wi-Fi Assist、混合并发和自动挂起。
- 不转发 ICMP。
- 不开放 Wi-Fi 代理共享或热点代理共享。
- 不配置 HTTP API、外部控制器或监听端口。
- 关闭内置 Web 面板。
- 代理及网关限制在局域网语义内，同时共享入口本身保持关闭。

`skip-proxy` 明确列出私网、回环、链路本地、运营商共享地址、`.local` 和 `.lan`。这些目标会绕过代理，是局域网功能的显式例外。尤其 `100.64.0.0/10` 可能由运营商共享地址环境使用，保留它代表接受该地址段直连。

如果设备上通过模块新增监听端口、MITM、脚本、外部代理或跳过路由，必须把模块视作另一份完整配置重新审核。

## 7. 失效时行为

| 场景 | 预期结果 | 是否会新增直连 |
| --- | --- | --- |
| 真实节点正常 | 境外、未知、普通 DoH 和 STUN 经代理 | 否 |
| 所有真实节点故障 | `Fail-Closed` 使代理路径失败 | 否 |
| 公开模板未添加节点 | 境外及未知失败；普通域名解析通常也失败 | 否 |
| 普通 DoH 不可达 | 普通域名解析失败，不回退到普通明文解析 | 否 |
| 单个远程规则下载失败 | Surge 可能使用有效缓存、报告加载错误或无法启用配置；只要配置仍运行，规则本身没有直连授权 | 否 |
| 远程规则内容被错误修改 | 只能影响代理或拒绝策略，不能授予直连 | 否 |
| APNs 代理路径故障 | `Apple Push` 可切换到 `APNs Direct` | 是，仅 APNs 设计范围 |
| APNs 专用 DoH 故障 | APNs 域名解析可能失败 | 否 |
| 所选代理不支持 UDP | UDP 被 `REJECT` | 否 |
| 未知 IPv6 目标 | 最终进入 `Proxy` 或失败 | 否 |
| 用户手动选择 `Domestic=DIRECT` | 国内目标显示真实 IP | 是，明确选择 |
| 用户手动选择 `Apple=DIRECT` | Apple 目标显示真实 IP | 是，明确选择 |

策略闭锁关注的是“不意外扩大直连权限”，并不保证服务始终可用。严格失败关闭的正常表现就是在缺少可信代理或可信解析路径时拒绝连接。

## 8. 添加节点与导入

### 8.1 准备条件

- 安装受支持版本的 Surge iOS。
- 确认已解锁 Surge iOS 功能订阅；`APNs Proxy` 使用的 Smart 策略需要该功能。
- 在本地私有副本中操作，不要把节点凭据、订阅 URL、密码、私钥或临时签名链接提交到公开仓库。
- 至少准备一个可信、可用且协议受支持的代理节点。

### 8.2 节点要求

在 `[Proxy]` 中添加节点时遵守以下约束：

1. 节点服务器字段使用 IPv4 或 IPv6 字面量，避免代理尚未建立时解析节点域名形成引导 DNS 直连。
2. TLS 类协议仍应设置正确的 SNI/服务器名称。
3. 保持证书验证开启，不得使用 `skip-cert-verify=true`。
4. 不添加未加密的普通 HTTP 或 SOCKS5 远程代理。
5. 核对节点是否支持 UDP；不支持时接受 UDP 被拒绝，而不是增加直连兜底。
6. 节点名称不要伪装成订阅流量、到期通知或其他信息项。

严格检查器允许模板内唯一的普通 HTTP 项是指向 `127.0.0.1:1` 的 `Fail-Closed`，它是不可达哨兵，不是远程代理。

### 8.3 订阅处理

主配置刻意不使用运行时 `policy-path`。如使用 Sub-Store 或其他订阅转换工具：

1. 在私有环境导出节点。
2. 审核协议、IP 端点、端口、SNI、证书校验、UDP 能力和异常信息节点。
3. 将通过审核的节点静态写入本地 `[Proxy]`。
4. 再运行静态检查并导入。

不要把带令牌的订阅地址写回公开配置，也不要恢复可在运行时任意改变节点集合的 `policy-path`。

### 8.4 导入步骤

1. 下载完整仓库或经过审计的发布包。
2. 在私有副本的 `[Proxy]` 中加入真实节点。
3. 运行配置和规则检查。
4. 在 Surge iOS 中导入 `Surge.conf`。
5. 使用 Rule 出站模式。
6. 检查 `Proxy` 不能选择 `DIRECT` 或 `APNs Direct`。
7. 检查 `Domestic`、`Apple` 和 `Apple Push` 的选择符合自己的真实 IP 暴露偏好。
8. 确认设备没有额外模块、MITM、脚本或网络扩展覆盖主配置。

主配置 Raw 地址：

```text
https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf
```

直接使用 `main` 分支地址方便更新，但它不是不可变供应链来源。正式部署应保存已审核副本并记录对应提交。

## 9. 内置健康与延迟检测

本配置不会主动发起带宽测速，也不包含独立带宽测速策略组或大流量下载任务，但保留策略组正常工作所需的轻量健康/延迟检测。个别上游服务规则可能包含同一服务商用于诊断的域名；规则匹配本身不会主动运行测试。

| 用途 | 地址 | 行为 |
| --- | --- | --- |
| 互联网连通性 | `http://www.apple.com/library/test/success.html` | 通过明确允许直连的 Apple 目标检查基础网络可达性 |
| 代理节点检测 | `http://www.gstatic.com/generate_204` | 仅经被测代理检查可用性和延迟 |
| APNs 直连检测 | Apple HTTP 成功页 | 判断 APNs 直连候选是否可用 |

Surge iOS 的连通性与策略测试使用 HTTP 探测端点，并以 HTTP 请求进行可用性/延迟判断；这不是带宽测速。明文探测可能被链路观察或伪造，因此其结果只用于健康状态和代理候选排序：Apple 探测属于既有明确直连，Google 探测只经被测代理发送；相关策略组不存在通往 `DIRECT` 的意外回退路径。`url-test` 和地区组设置 `interval=600`、`evaluate-before-use=true`，结果过期并在需要使用时重新评估。

隐私上，Apple 或 Google 可能看到对应探测请求的出口 IP、时间和基础连接元数据。详情见 `NOTICE.md`。

## 10. 静态检查

在仓库根目录运行：

```bash
python3 tools/audit_config.py Surge.conf
python3 tools/audit_rules.py Rules
```

当前预期输出：

```text
PASS: Surge.conf | groups=33 rules=323 remote_rules=22 direct_groups=Apple,Apple Push,Domestic
PASS: Rules | files=32 active_entries=132599
```

`audit_config.py` 会检查：

- 仅出现允许的配置区段、选项、策略类型和规则类型。
- 不存在未解析的 `#!include` 或托管配置指令。
- 真实节点必须使用 IP 字面量服务器端点。
- 不允许关闭 TLS 证书校验。
- `Proxy`、境外服务组及远程规则不能到达直连。
- 远程规则 URL 必须固定到 40 位完整提交并属于允许前缀。
- APNs Host、策略、网段、DoH 例外及顺序保持完整。
- 普通 DoH、STUN、UDP 不支持行为和代理 QUIC 设置保持闭锁。
- IPv6、网络接管、局域网和控制面设置没有回归。
- `FINAL` 是最后一条有效规则并进入 `Final`。

`audit_rules.py` 会检查：

- 本地 `.list` 文件是否可读。
- 规则类型和字段数量是否处于允许范围。
- IPv4、IPv6、ASN 和 `no-resolve` 参数是否有效。
- DOMAIN-SET 是否含空白或逗号等格式错误。
- 文件内是否存在完全重复项或超长规则。

这些脚本是项目自己的安全断言，不是 Surge 官方解析器。静态检查通过后仍必须在真机导入并观察请求日志。

## 11. 真机验收清单

建议在 Wi-Fi 和蜂窝网络分别执行以下检查：

- 配置能在目标 Surge iOS 版本无警告导入。
- Rule 模式启用，`FINAL` 命中未知域名时显示 `Final -> Proxy`。
- 所有代理节点关闭后，境外网站失败而不是显示本地公网 IP。
- 普通 DoH 随代理失败，不出现运营商 DNS 自动接管。
- 国内和 Apple 的直连结果符合用户当前策略选择。
- APNs 正常时优先使用代理，代理全部故障后仅 APNs 切换直连。
- IPv4 与 IPv6 测试中，境外出口均为代理地址或直接失败。
- WebRTC/STUN 测试不显示未预期的本地公网地址。
- 所选代理不支持 UDP 时，UDP 请求被拒绝而不是直连。
- 已知公共 DoH、DoT 和 HTTPDNS 入口被拒绝或按配置进入代理。
- 局域网路由器和必要本地设备仍可访问。
- Wi-Fi/热点上的其他设备无法连接本机代理端口、API 或面板。
- 请求日志中没有陌生模块、脚本、改写或额外 DNS 服务器。

测试泄漏时不要只看单一网站；至少交叉检查 IPv4、IPv6、DNS、WebRTC/STUN，并在代理正常、代理全断和规则缓存清除后三种状态下重复。

## 12. 规则与供应链

### 12.1 运行时规则

当前主配置加载 22 个本仓库规则快照。每个 URL 都固定到：

```text
9b1432d57c9ea26ef24ea037481189743f1d73f6
```

这些远程规则只能进入代理或拒绝策略。固定提交能够防止上游同一路径静默改变内容，但不能证明文件本身无误、来源完整或许可证兼容。

### 12.2 直连规则

能进入 `Domestic`、`Apple`、`Apple Push` 或内置 `DIRECT` 的规则均在主配置内联并由检查器建立允许清单。维护时应逐条审查新增直连规则，说明业务理由，并同时更新审计器断言。

### 12.3 本地快照

`Rules/` 中既有当前主配置使用的文件，也有未启用的来源/归档快照。发布包只携带当前主配置实际引用的 22 个规则文件，避免把未使用内容扩大到交付面。

完整来源、许可状态、实际分发与仅供参考的项目区分见 `NOTICE.md`。部分历史规则快照仍缺少逐文件来源元数据；在补齐之前，不应把它们宣称为本项目原创，也不应无条件扩大再分发。

### 12.4 更新远程规则的安全流程

1. 在隔离目录下载候选文件。
2. 记录原始项目、文件 URL、提交、许可证和获取日期。
3. 对比新增/删除规则，特别检查是否包含策略字段、逻辑规则、过宽网段或异常长行。
4. 运行 `tools/audit_rules.py`。
5. 只把代理或拒绝类规则接入运行时。
6. 提交快照后，将 `Surge.conf` 和 `tools/audit_config.py` 中的固定提交同步更新。
7. 在真机验证缓存存在与缓存清除两种状态。
8. 更新 `NOTICE.md` 的来源和修改说明。

任何希望进入直连的上游内容都必须改为人工审核后内联，不能直接赋予远程 URL 直连策略。

## 13. ZIP 候选包工作流

`.github/workflows/unpack.yml` 是只读验证工作流：

- 仅手动触发。
- GitHub Actions 权限为 `contents: read`。
- `actions/checkout` 与 `actions/upload-artifact` 固定到完整提交。
- `tools/stage_surge_zip.py` 拒绝路径穿越、链接、重复路径、超量文件、超大解压体积和非允许文件。
- 暂存后重新审计主配置及规则。
- 只上传保留 7 天的候选 artifact。
- 不覆盖工作区源文件，不删除仓库文件，不提交，也不推送。

该流程用于验证候选包，不代表自动发布或自动信任 ZIP 内内容。

## 14. 已知边界

- 没有真实代理节点时，严格闭锁会显著降低可用性，这是模板的预期状态。
- 不使用 MITM 时，无法准确识别所有伪装为普通 HTTPS 的新型应用内 DoH。
- `include-*` 选项尽量扩大接管范围，但不能保证平台所有系统流量都经过 Surge。
- 域名、IP 网段、服务接口和平台行为都会变化，固定快照会逐渐过时。
- 广告规则可能误杀，服务规则也可能遗漏或交叉匹配。
- 健康检测成功只表示测试目标在当时可达，不证明节点隐私、安全或完整业务可用。
- 静态检查只覆盖编码进脚本的断言，无法替代官方语法解析和真机网络观测。
- 公开 Raw 地址和 jsDelivr 仍依赖 GitHub、CDN、TLS、证书链及本地缓存等供应链环节。

## 15. 目录说明

- `Surge.conf`：iOS 主配置模板。
- `Rules/`：本地规则快照；并非全部都由主配置启用。
- `THIRD_PARTY_LICENSES/`：已确认并分发的第三方许可证副本。
- `tools/audit_config.py`：主配置失败关闭与信任边界检查。
- `tools/audit_rules.py`：本地规则语法包络检查。
- `tools/stage_surge_zip.py`：候选 ZIP 安全暂存器。
- `.github/workflows/unpack.yml`：只读候选包验证工作流。
- `NOTICE.md`：来源、许可证、归属、隐私暴露及免责声明。

## 16. 参考资料

- [Surge 官方手册](https://manual.nssurge.com/)
- [Surge DoH](https://manual.nssurge.com/dns/doh.html)
- [Surge General 选项](https://manual.nssurge.com/others/misc-options.html)
- [Surge Rule Set](https://manual.nssurge.com/rule/ruleset.html)
- [Surge 策略组包含规则](https://manual.nssurge.com/policy-group/policy-including.html)
- [Surge 测试型策略组](https://kb.nssurge.com/surge-knowledge-base/zh/technotes/testing-group)
- [Surge Smart 策略](https://kb.nssurge.com/surge-knowledge-base/zh/guidelines/smart-group)
- [DivineEngine：Surge 分流规则说明](https://divineengine.net/article/surge-rule-system/)
- [Apple：APNs 网络端口](https://support.apple.com/zh-cn/102266)
- [Apple：企业网络上的 Apple 服务](https://support.apple.com/zh-cn/101555)

第三方规则和参考配置的完整列表不在本节重复，统一记录于 `NOTICE.md`。
