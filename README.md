# Surge 公开配置

由 **.ᐣ** 维护的 Surge iOS 公开配置，面向中国大陆网络环境，目标是在兼顾日常兼容性的前提下，完成国内外流量分流、常用境外服务独立策略、Telegram 与 Apple Push 通知处理、DNS 加密以及 IPv4/IPv6/UDP 泄漏防护。

> Telegram 用户：[@shenjlngbIng](https://t.me/shenjlngbIng)  
> GitHub：<https://github.com/shenjlngbIng/->  
> 当前配置更新日期：**2026-07-15**  
> 建议版本：**Surge iOS 5.14.6 或更高版本**

## 目录

- [项目特点](#项目特点)
- [文件说明](#文件说明)
- [安装与更新](#安装与更新)
- [首次使用必须完成的设置](#首次使用必须完成的设置)
- [策略组说明](#策略组说明)
- [规则匹配顺序](#规则匹配顺序)
- [Telegram 与 Apple Push](#telegram-与-apple-push)
- [DNS、IPv6 与泄漏防护](#dnsipv6-与泄漏防护)
- [隐私边界与预期暴露](#隐私边界与预期暴露)
- [规则集与供应链控制](#规则集与供应链控制)
- [验证基线](#验证基线)
- [常见问题](#常见问题)
- [更新维护建议](#更新维护建议)
- [免责声明与第三方声明](#免责声明与第三方声明)

## 项目特点

- 国内服务统一归入 `Domestic`，默认直连，不为单个国内应用建立独立策略组。
- 境外 AI、开发、社交、流媒体、游戏平台及系统服务分别进入对应策略组。
- 未命中的流量进入 `Final`，且 `Final` 不包含 `DIRECT`，避免未知境外流量意外直连。
- 使用仅连接本机关闭端口的 `Fail-Closed` 哨兵，防止 Smart 空组按 Surge 默认行为替代为 `DIRECT`。
- Telegram 业务流量与其依赖的 Apple Push 通知链路分开处理。
- APNs 使用内层 Smart 自适应选择代理；外层仅在全部代理不可用时回落 `DIRECT`，保留上一版推送能力。
- 接管 IPv4、IPv6、APNs、可接管的蜂窝系统服务以及应用主动绑定物理网卡的流量。
- DoH 加密 DNS、证书校验、53 端口 DNS 劫持；除 APNs 兜底所需的单一显式例外外，Surge 自身的 DoH/DoH3/DoQ 及 853 端口 DoT/DoQ 强制交给代理。
- 代理不支持 UDP 时拒绝连接，代理流量阻断 QUIC，所有公网 STUN 在国内规则之前进入代理。
- 禁用 ICMP 直接转发，降低增强模式下的真实 IP 暴露面。
- 禁用 Wi-Fi 代理共享、热点代理共享和网页控制面板，并限制代理与网关访问范围。
- 不包含 MITM、脚本和 URL Rewrite，不安装证书，不解密应用 HTTPS 内容。
- 远程规则集固定到具体 Git 提交，避免上游主分支变化后静默改变本地行为。
- 禁用未固定内容的 GeoIP 后台自动更新；数据库失配时未知地址进入 `Final → Proxy`。

## 文件说明

| 文件 | 用途 |
| --- | --- |
| `Surge.conf` | Surge 主配置，公开仓库中不应包含订阅 Token、密码或私钥。 |
| `README.md` | 安装、策略结构、安全边界、推送说明及排错指南。 |
| `NOTICE.md` | 作者信息、上游项目、规则来源、许可和商标说明。 |

## 安装与更新

### 方法一：手动导入，推荐

1. 从仓库下载 `Surge.conf`。
2. 在本地文本编辑器中，将 `policy-path=你的订阅地址` 替换为自己的 Surge 节点订阅 URL。
3. 不要把修改后的私有订阅 URL、Token、用户名或密码上传到公开仓库。
4. 在 iOS 分享菜单中选择 Surge，或在 Surge 的配置列表中从文件导入。
5. 首次启用后检查 `AllServer` 是否已经加载出真实节点。

手动导入可以确保订阅 URL 只保存在设备本地，也不会因为远程公开配置更新而被占位符覆盖。

### 方法二：从 URL 下载

GitHub Raw：

```text
https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf
```

jsDelivr 备用入口：

```text
https://cdn.jsdelivr.net/gh/shenjlngbIng/-@main/Surge.conf
```

注意：

- 部分中国大陆运营商网络访问 GitHub Raw 可能超时；此时改用 jsDelivr 或手动下载。
- jsDelivr 可能存在缓存延迟，不适合验证刚刚上传的分钟级更新。
- URL 下载到的公开配置仍然使用订阅占位符，必须在本地私有副本中填写节点订阅。
- 如果 Surge 提示 `NSURLErrorDomain -1001`，通常表示配置下载请求超时，不代表配置语法错误。

## 首次使用必须完成的设置

### 1. 填写节点订阅

找到 `[Proxy Group]` 中的 `AllServer`：

```ini
AllServer = select, Fail-Closed, ..., policy-path=你的订阅地址, ...
```

仅在本地把 `你的订阅地址` 替换为真实 URL。配置通过 `external-policy-modifier="skip-cert-verify=false"` 强制外部节点保持证书校验。

### 2. 检查默认策略

导入后建议确认：

| 策略组 | 建议初始选择 |
| --- | --- |
| `Proxy` | `Auto` |
| `Domestic` | `DIRECT` |
| `AdBlock` | `REJECT` |
| `Apple` | `DIRECT`；需要代理时再手动切换 |
| `Telegram` | `Proxy` 或稳定的地区节点 |
| `Final` | `Proxy` |

Surge 会记住旧配置中的策略选择。如果更新后行为异常，应先把 `Proxy` 切回 `Auto`、`Domestic` 与 `Apple` 切回 `DIRECT`，再重新测试。

### 3. 更新外部资源

在 Surge 中更新配置和外部资源，确认所有远程规则集成功加载。若只有单个规则集失败，优先判断 CDN 或网络可达性，而不是立即改动规则顺序。

## 策略组说明

### 核心策略

| 策略组 | 作用 | 是否可直连 |
| --- | --- | --- |
| `Fail-Closed` | 指向 `127.0.0.1:1` 的永远失败代理；只用于阻止 Smart 空组替代为 `DIRECT`。 | 否 |
| `AllServer` | 从本地订阅导入全部有效节点；始终包含 `Fail-Closed`。 | 否 |
| `Auto` | 根据节点质量自动选择；`Fail-Closed` 被降低到最低优先级。 | 否 |
| `Proxy` | 全局代理入口，可在 Smart 自动选择、全部节点和地区组之间切换。 | 否 |
| `Final` | 未命中规则的最终出口。 | 否 |
| `Domestic` | 国内服务统一策略，默认 `DIRECT`，必要时可临时切 `Proxy`。 | 是 |
| `APNs Proxy` | 使用 Smart 在全部订阅节点间自适应选择；只含代理和本机失败哨兵，不包含公网直连。 | 否 |
| `APNs Direct` | 仅供 `Apple Push` 最末兜底的直连别名；用 Apple 连通性地址测试可用性。 | 是，仅 APNs 兜底 |
| `Apple Push` | 优先使用 `APNs Proxy`；全部代理不可用时回落 `APNs Direct`，保留通知可达性。 | 是，仅 APNs 兜底 |
| `AdBlock` | 广告和跟踪规则，默认 `REJECT`；误杀时可临时切 `Proxy`。 | 否 |

### 地区策略

`HongKong`、`TaiWan`、`Japan`、`Singapore` 和 `America` 使用节点名称正则筛选，并通过 Smart 策略选择质量较好的节点。地区组不回落到 `DIRECT`；没有匹配节点时只剩 `Fail-Closed`，连接在本机失败。

### 境外服务策略

配置为以下类别建立独立策略组：

- AI：`ChatGPT`、`Claude`、`Gemini`。
- 开发与生产力：`GitHub`、`Microsoft`。
- 社交与通信：`Telegram`、`X`，以及进入通用 `Proxy` 的其他境外服务。
- 流媒体：`YouTube`、`NETFLIX`、`Disney+`、`HBO`、`PrimeVideo`、`Emby`、`Spotify`、`TikTok`、`Bahamut`、`Streaming`。
- 游戏：`Games`。
- 系统服务：`Apple`、`Apple Push`、`Google`。

这些策略组默认继承 `Proxy`，也允许用户针对地区限制或流媒体解锁情况手动选择节点。

### 国内服务策略

国内社交、影音、阅读、电商、支付、云服务及中国区域服务统一进入 `Domestic`。配置不依赖应用名称，而是按域名规则、`.cn`、固定的中国域名集合以及 `GEOIP,CN` 依次兜底。

为避免未固定内容的后台供应链变化，`disable-geoip-db-auto-update=true`。随应用提供的 GeoIP 数据库若变旧，影响是部分中国 IP 被送入 `Final → Proxy`，而不是把未知境外 IP 放行直连。

少量中国区域游戏平台域名放在境外游戏规则之前，这是必要的优先级例外；全球版游戏平台域名仍然进入 `Games`。

## 规则匹配顺序

Surge 采用从上到下、首条命中即停止的规则模型。本配置按以下优先级排列：

1. 本地初始化地址、无效地址和局域网。
2. APNs 域名与专用 IPv4/IPv6 网段。
3. APNs 专用直连 DoH 例外，其余 DoH/DoH3/DoQ/DoT 与所有公网 STUN 强制进入代理。
4. Apple 系统策略、SSH 和特殊顶级域处理。
5. 安全浏览与广告拦截。
6. 必须优先直连的中国区域服务。
7. 境外 AI、开发、社交、流媒体和游戏服务。
8. Apple 系统服务。
9. 国内服务、`.cn`、中国域名集合与 `GEOIP,CN`。
10. 其余流量进入 `FINAL,Final,dns-failed`。

不要随意把 `DOMAIN-SUFFIX,cn,Domestic` 或整个国内规则段移动到最顶部，否则可能覆盖 Apple、广告、安全浏览或需要独立策略的中国区域域名。也不要把 `FINAL` 移出最后一条。

## Telegram 与 Apple Push

Telegram 前台收发消息使用 Telegram 自身服务器；iOS 应用退到后台后的通知主要依赖 Apple Push Notification service（APNs）。因此，“Telegram 能打开并收消息”不等于后台推送链路正常。

本配置保留上一版处理关系：

```text
Telegram 业务域名/IP  → Telegram → Proxy/稳定地区节点
APNs 域名/专用网段    → Apple Push → APNs Proxy → APNs Direct 兜底
```

`include-apns=true` 让 Surge VIF 接管 APNs；Surge 官方要求它与 `include-all-networks=true` 配合。后者还用于接管主动绑定物理网卡、试图绕过 VIF 的应用。`include-local-networks=true` 和 `include-cellular-services=true` 分别接管可接管的局域网及蜂窝系统服务流量；运营商直接路由到专网、完全不经过互联网的流量仍可能被系统排除。

APNs 规则只覆盖上一版使用的 3 个域名后缀、5 个 IPv4 网段和 4 个 IPv6 网段，不使用整个 Apple 地址空间。`APNs Proxy` 使用 Smart 根据实际连接质量在订阅节点间自适应选择，并把 `Fail-Closed` 降到最低优先级；它本身不含内置 `DIRECT` 或其他策略组，因此不会再触发截图中的 Smart 子策略语法错误。`Apple Push` 是只含 `APNs Proxy` 与 `APNs Direct` 的外层 fallback，仅在全部代理不可用时直连。直连别名只被该组引用，不能被其他 Smart、境外或最终策略意外选中。

新版 Surge 的自动策略组复用具体策略的测试结果，不应再配置组级独立 `url=`。因此 Apple 测试地址设置在 `APNs Direct` 的 `test-url` 上；测试器按 Surge 官方机制发送 HTTP HEAD，不携带业务内容。外层使用 600 秒结果有效期并采用默认的非阻塞首次评估，避免首个 APNs 请求等待整组检测。直连回落会让 Apple 看到设备真实出口 IP，但避免代理故障拖死所有应用通知。

为了不让全局 DNS 的失败关闭破坏 APNs 直连兜底，`[Host]` 仅为 APNs 域名和 Apple 检测地址指定 `https://223.6.6.6/dns-query`，并通过一条 `PROTOCOL,DOH + IP-CIDR` 逻辑规则明确直连。其他域名的 DNS 仍强制走代理，不会借此例外回落直连。

修改 `include-apns` 后应开关一次飞行模式或重启设备，并且测试时不要从多任务界面强退 Telegram。Apple 说明设备通常使用 TCP 5223 连接 APNs，失败时可回落 TCP 443；节点能打开 Apple 测试页并不等于一定能长期稳定连接 APNs。

作为中国大陆网络下推送异常的背景资料，可参阅用户提供的 [NodeSeek 页面存档](https://web.archive.org/web/20260715022631/https://www.nodeseek.com/post-709310-1)；该页面不是 Surge、Apple 或 Telegram 官方文档，配置中的协议、端口和网段仍以官方资料为准。

Surge 显示“包含所有网络请求选项已开启”的警告属于已知提示。关闭 `include-all-networks` 可以减少 AirDrop、Xcode 或 USB Dashboard 的兼容问题，但会同时削弱 APNs 接管和应用防绕行能力。

## DNS、IPv6 与泄漏防护

### DNS

- 上游 DoH：AliDNS 与腾讯 DNSPod。
- `encrypted-dns-skip-cert-verification=false`：校验 DoH 服务器证书。
- `hijack-dns=*:53`：接管应用发送到任意传统 53 端口 DNS 的查询。
- `use-local-host-item-for-proxy=false`：代理连接默认交由代理服务器解析目标域名。
- `encrypted-dns-follow-outbound-mode=true`：DoH 连接遵循规则，并由前置规则强制进入 `Proxy`。
- `PROTOCOL,DOH/DOH3/DOQ`：按 Surge 官方说明匹配 Surge 自身发出的加密 DNS 请求。
- `DEST-PORT,853`：把应用常用的 DoT/DoQ 端口交给代理。
- 传统 DNS 只用于连通性检查、解析 DoH URL 及必要的代理引导；不会承载普通应用域名查询。
- 除 APNs/Apple 检测域名的显式直连 DoH 外，代理不可用时其他 DoH 会失败，不自动回落真实 IP 直连。

应用自带的任意 DoH 若伪装成普通 HTTPS/443，系统无法仅凭端口完整识别；本配置中的境外与未知目标仍会由 `FINAL` 送入代理，但无法承诺识别所有私有协议。测试时应暂时停用其他加密 DNS 描述文件和网络扩展。DNS 泄漏页面显示 AliDNS/DNSPod 的解析器名称，并不等同于暴露设备 IP；需要同时确认该 DoH 连接在 Surge 中命中 `Proxy`。

### IPv6

- `ipv6=true`：允许查询和使用 IPv6。
- `ipv6-vif=auto`：当前网络具备有效 IPv6 时，由 Surge VIF 接管 IPv6。
- Telegram 前台业务和 APNs 均包含专用 IPv6 规则；APNs IPv6 与 IPv4 使用相同的代理优先、DIRECT 兜底策略。
- 配置没有排除公网 IPv6 路由，因此不会因为只处理 IPv4 而让公网 IPv6 默认绕过。

### UDP、QUIC、STUN 与 ICMP

- `udp-policy-not-supported-behaviour=REJECT`：节点不支持 UDP 时拒绝，而不是自动直连。
- `block-quic=all-proxy`：对代理策略阻断 QUIC，促使应用回落到可控的 TCP/TLS。
- `PROTOCOL,STUN,Proxy`：位于国内域名/IP 规则之前，所有公网 STUN 流量走代理。
- `icmp-forwarding=false`：不让增强模式中的公网 ICMP 自动从物理接口直发。

这些设置降低常见绕行风险，但不能替代设备端实测。代理节点自身的 UDP 实现、系统扩展、其他 VPN、私人中继及第三方模块都可能改变最终结果。

## 隐私边界与预期暴露

本配置对境外、未知、非 APNs DNS 和 STUN 采用失败关闭，但仍保留明确的国内、Apple 与 APNs 兜底直连。下列暴露属于设计结果，不应误判为规则绕行：

| 场景 | 对方可能看到的信息 | 原因 |
| --- | --- | --- |
| `Domestic = DIRECT` | 设备当前公网 IP、连接时间和常规服务端元数据 | 国内服务默认直连，保证速度和兼容性。 |
| `Apple = DIRECT` | Apple 及 `SYSTEM` 内置规则目标看到真实公网 IP | Apple 组默认直连；需要隐藏时可手动切至 `Proxy`。 |
| `Apple Push` 回落到 `APNs Direct` | Apple 看到真实公网 IP | 仅在全部 APNs 代理不可用时保留通知可达性。 |
| APNs 专用直连 DoH | AliDNS 看到真实出口 IP及 APNs/Apple 检测域名 | 仅用于保证上述 DIRECT 兜底具备解析能力；其他 DNS 不使用此出口。 |
| DoH 经代理 | DoH 提供商看到代理出口 IP及查询域名；代理商看到加密 DNS 连接元数据 | 解析服务必须处理查询，但不再看到设备真实出口。 |
| 传统 DNS 引导 | AliDNS/DNSPod 可能看到 DoH 端点或代理节点的引导查询 | Surge 官方说明配置 DoH 后，传统 DNS 不再承载普通应用域名查询。 |
| `sub.store`、LAN 与 captive portal | 对应本地服务或 Apple 门户看到真实出口/局域网地址 | 初始化、局域网和登录网络所需的明确直连例外。 |
| 运营商系统服务 | 运营商看到订阅身份、连接信息及相关地址 | 可接管部分已纳入 VIF；运营商专网路由仍可能被系统强制排除。 |
| 连通性测试 | 华为和 Cloudflare 看到对应出口 IP | 用于判断 DIRECT 与代理是否可用。 |
| 代理流量 | 代理服务商看到连接元数据；目标站点看到代理出口 IP | 代理转发的固有属性。 |
| 节点订阅更新 | 订阅提供商看到更新请求的出口 IP、时间及订阅凭据 | 只能使用可信的 HTTPS 订阅，且不得把带 Token 的 URL 上传到公开仓库。 |
| 外部规则下载 | GitHub/jsDelivr 看到下载出口 IP和请求时间 | 更新远程规则所必需。 |

在保留国内、Apple、APNs 兜底、局域网和 captive portal 直连的前提下，无法实现“任何第三方都看不到真实 IP”。若需要全局匿名模式，必须另建不含这些 `DIRECT` 路径的配置；直接删掉兼容例外会增加登录认证、局域网及系统服务故障概率。

## 规则集与供应链控制

当前主配置引用 26 个远程规则集：

- 本仓库规则固定到提交 `9b1432d57c9ea26ef24ea037481189743f1d73f6`。
- `ChinaDomain.list` 固定到 `Coldvvater/Mononoke` 提交 `e8bee09b64c2f6baaa3056ed8de61c74cec56a98`。
- 通过 jsDelivr 下载固定提交内容，不直接跟随可变的 `main` 或 `master`。

固定提交可以避免上游在未审计的情况下改变规则，但也意味着新域名不会自动进入旧规则。维护者更新规则时应先检查差异、冲突、重复项和过宽规则，再更新提交哈希。

第三方规则、配置结构及参考项目的归属见 [NOTICE.md](./NOTICE.md)。

## 验证基线

截至 2026-07-15，当前公开配置的静态审计基线为：

| 项目 | 结果 |
| --- | ---: |
| 本地策略定义 | 2（`Fail-Closed`、`APNs Direct`） |
| 策略组 | 33 |
| 主规则 | 215 |
| 固定版本远程规则集 | 26 |
| 远程子规则 | 9,194 |
| 策略/规则静态检查 | 0 错误、0 警告 |
| 远程规则在线检查 | 26/26 HTTP 200 |
| 远程内容与固定版本本地副本一致 | 26/26 |
| 未知策略引用 | 0 |
| 策略组循环引用 | 0 |
| 重复生效主规则 | 0 |
| 可到达 `DIRECT` 的策略组 | 3（仅 `Domestic`、`Apple`、`Apple Push`） |
| 显式 `DIRECT` 主规则 | 4（Sub-Store、LAN、APNs 专用 DoH、captive portal） |
| Smart 空组失败保护 | `Fail-Closed` 已覆盖全部 Smart 组 |
| 远程规则过宽兜底项 | 0 |
| 未声明的“直连优先”跨策略冲突 | 0（9 项中国区域/安全服务例外均已声明） |
| 未固定提交的远程规则 URL | 0 |

当前 `Surge.conf` 内容对应的 SHA-256：

```text
0e12908b084f22f98481b565dc340598b2f723c18ec8449618049c72e52b7b77
```

仓库后续更新配置后，维护者应同步更新日期、审计数字和校验值。文件换行符或空格变化也会改变 SHA-256，并不必然表示内容恶意。

## 常见问题

### Surge 下载配置提示请求超时

这通常是 GitHub Raw、当前网络或 DNS 的可达性问题。可以改用 jsDelivr，或者先在浏览器下载配置后手动导入。只有下载成功后，Surge 才能继续做语法检查。

### 远程规则集加载失败

先检查失败 URL 是否能在浏览器打开，再尝试切换 Wi-Fi/蜂窝网络、更新外部资源或稍后重试。本配置已经固定提交；不要因为临时 CDN 故障把 URL 改回不固定版本的主分支。

### `AllServer` 中的 `Fail-Closed` 显示红色“失败”

这是预期行为。Surge 官方说明 Smart 组在没有子策略时会以 `DIRECT` 替代；`Fail-Closed` 是指向 `127.0.0.1:1` 的本机失败哨兵，用来保证 Smart 永不为空。它不发送公网流量，并通过权重排在真实节点之后。若整个 `AllServer` 只有 `Fail-Closed`，说明订阅地址尚未填写、加载失败或节点名称全部被过滤。

### 节点频繁显示超时

代理超时通常来自订阅节点、服务器线路、端口或当前运营商，不代表分流规则错误。先在 `AllServer` 单独测试节点，再判断策略组。

### 国内服务无网络

1. 确认 `Domestic` 当前选择 `DIRECT`。
2. 查看请求记录中的首条命中规则。
3. 若命中 `AdBlock`，临时把 `AdBlock` 切到 `Proxy` 判断是否误杀。
4. 若完全没有请求记录，检查是否还有其他 VPN、DNS 工具或系统网络限制。
5. 不建议为每个国内应用建立独立组；优先补充域名到统一 `Domestic` 规则。

### 国外应用无网络

确认目标策略组没有选到失效地区节点，`Proxy` 不是空组，并检查 `AllServer` 是否至少存在一个可用节点。`Final`、境外服务组和地区组均不会自动直连。

### Telegram 能打开但后台没有推送

1. 确认 `include-all-networks=true` 与 `include-apns=true` 均已生效。
2. 更新配置后开关一次飞行模式或重启设备，不要强退 Telegram。
3. 在请求记录中确认 Telegram 业务命中 `Telegram`，`courier.push.apple.com` 或对应 APNs IP 命中 `Apple Push`。
4. 分别测试 Wi-Fi 与蜂窝网络；移动数据更依赖 APNs 接管。
5. 若 `APNs Proxy` 的节点无法维持 TCP 5223/443，观察 `Apple Push` 是否回落 `APNs Direct`。回落后仍无通知，问题可能位于运营商、Apple、iOS 电源管理或 Telegram 服务端。

### Surge 提示“包含所有网络请求选项已开启”

这是 `include-all-networks=true` 的已知警告。本配置同时启用 `include-apns=true` 以保留上一版后台推送能力。若 AirDrop、Xcode 或 USB Dashboard 出现问题，可以临时关闭排查，但该时段 APNs 代理和完整防绕行均不能保证。

### Surge 提示短时间处理大量请求或内存占用过高

1. 先重启 Surge 和设备，排除旧连接或模块死循环。
2. 禁用第三方脚本、MITM、重写和高频定时任务后观察。
3. 检查事件列表中是否有某个域名持续重复请求。
4. 通用 `Fallback` 已移除；`APNs Proxy` 使用 Smart，只抽取部分策略复测。外层 `Apple Push` 复用策略测试结果，结果有效期为 600 秒，不再配置每 60 秒组级独立测试，也不会阻塞首个 APNs 请求。
5. 本主配置不包含脚本、MITM 或 URL Rewrite；若出现 JSON 字段缺失、脚本运行错误或通知轰炸，来源通常是另外启用的模块。
6. 不要同时加载多个功能重叠的大型广告规则集。

### 出现第三方脚本字段缺失通知

类似“无某字段”的 JSON 脚本错误属于对应模块与服务端数据结构不兼容，不由主配置规则修复。请在 Surge 模块列表中禁用或更新该模块；删除通知本身不会解决脚本逻辑问题。

### 如何检查 IP 或 DNS 是否绕行

1. 分别记录关闭 Surge、开启 Surge 且使用 `Proxy` 时的公网 IPv4/IPv6。
2. 检查境外目标看到的应是代理出口，国内直连目标看到真实出口属于预期。
3. 在 Surge 请求记录中确认普通 DoH/DoH3/DoQ/853 与 STUN 命中 `Proxy`；只有发往 `223.6.6.6` 的 APNs 专用 DoH 可以命中显式 `DIRECT`。
4. 确认 APNs 域名/IP 命中 `Apple Push`，而非 `Apple`、`Domestic` 或 `Final`。
5. 分别在 Wi-Fi 和蜂窝网络测试，网络切换可能触发不同路由。
6. 暂停其他 VPN、私人中继、加密 DNS 描述文件和网络扩展，避免混淆结果。

## 更新维护建议

每次发布前建议完成以下流程：

1. 保留公开配置中的订阅占位符，扫描 Token、密码、私钥及控制器密钥。
2. 检查 `[General]`、`[Proxy Group]` 和 `[Rule]` 是否存在重复键、未知策略或循环引用。
3. 确认 `FINAL` 是最后一条生效规则。
4. 下载全部远程规则集并检查 HTTP 状态、空文件、非法规则及异常过宽域名。
5. 比较跨规则集冲突，尤其关注广告、国内、流媒体和游戏平台之间的首条命中。
6. 验证 DoH、STUN、Apple Push、Apple 直连、国内直连、主要境外服务与未知域名。
7. 在 Wi-Fi 与蜂窝网络分别进行后台推送、IPv4、IPv6 和 DNS 泄漏测试。
8. 更新配置日期、固定提交、README 审计基线和 SHA-256。
9. 上传后分别验证 GitHub Raw 与 jsDelivr URL。
10. 不把本地订阅 URL 或带签名参数的临时下载地址提交到仓库。

## 免责声明与第三方声明

- 本项目仅提供 Surge 配置与分流规则，不提供代理节点、网络服务或可用性承诺。
- 使用者应遵守所在地法律法规、Apple、Surge、代理服务商及相关网络服务的条款。
- 配置无法消除运营商、DNS 服务商、代理服务商、目标网站和系统平台可观察到的全部元数据。
- 远程规则可能出现遗漏、误杀、服务域名变化或地区差异，使用者应根据请求记录自行判断。
- Surge 是 Surge Networks Inc. 的产品；本项目与 Surge Networks Inc.、Apple、Telegram 及规则涉及的各服务商不存在隶属或背书关系。
- 第三方项目、规则和许可信息见 [NOTICE.md](./NOTICE.md)。`NOTICE.md` 不替代任何上游许可证。

## 联系

- 维护者：**.ᐣ**
- Telegram：[@shenjlngbIng](https://t.me/shenjlngbIng)
- GitHub：<https://github.com/shenjlngbIng/->
