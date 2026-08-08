# Surge iOS Privacy + Push R12

这是一套面向 Surge iOS 的公开、可审计、失败关闭型配置。主配置、规则快照、锁文件、校验脚本和 GitHub Actions 都放在同一个仓库中，便于导入、复核、更新和回滚。

本仓库只发布通用配置。公开文件不包含真实订阅地址、节点、用户名、密码、Token、Cookie、私钥、证书或设备标识。个人订阅只应保存在 Surge 本地或个人私有存储中。

## 先看这里

### 配置 URL

在 Surge 中导入下面的 Raw 配置地址。

```text
https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf
```

这个地址只提供 Surge.conf，不会提供任何个人节点。配置已经预留唯一订阅填写项，导入后只需要替换一处占位符，不需要手动复制节点或重新编写策略组。

## 适用环境与影响边界

| 项目 | 要求 |
|---|---|
| Surge | iOS 5.14.6 或更高版本 |
| 运行模式 | 规则模式 |
| 维护环境 | Python 3.10 或更高版本，建议 3.12 或 3.13 |
| 订阅格式 | Surge 节点格式，来源可以是 Sub-Store 或其他转换工具 |

当前模板只把订阅入口集中到 AllServer 的一行，并内置 Sub-Store `sub.store` 链接所需的最小请求重写。重写脚本固定到官方提交并通过 jsDelivr 获取，避免运行时依赖 GitHub Release 跳转。除订阅来源外，分流规则、策略组、DNS、Telegram、APNs 和 5551 条嵌入规则保持不变。

占位符未替换前没有可用节点，这是模板的预期状态。替换成真实的 Surge 输出链接并重新载入后，AllServer 会自动拉取节点，地区组和服务组会继续沿用现有规则。

### 订阅只有一个填写位置

| 内容 | 位置 | 是否需要修改 |
|---|---|---|
| 订阅 URL | [Proxy Group] 的 AllServer 行 | 只替换 YOUR_SUBSTORE_SURGE_URL |
| 节点、地区组、服务组 | Surge.conf 现有代码 | 不修改 |
| 模块 | 主配置的 `[MITM]` 与 `[Script]` | 已内置，不需要另建策略组或重复安装 |

公开文件只保留 YOUR_SUBSTORE_SURGE_URL 占位符，不保存真实订阅。Surge 的 policy-path 支持读取策略列表或完整 Surge 配置；AllServer 同时保留 include-all-proxies=true，方便你以后手动导入节点时继续兼容。`sub.store/download/...` 这类 Sub-Store 链接由主配置内置、固定版本的重写脚本处理。

## 快速开始

### 第一步，导入主配置

1. 复制上面的 Raw URL。
2. 在 Surge 的配置管理中选择从 URL 下载或导入。
3. 下载完成后载入 Surge.conf。
4. 打开配置审查，确认 [General]、[Proxy]、[Proxy Group] 和 [Rule] 都存在。

如果通过 ZIP 使用，请导入压缩包根目录中的 Surge.conf，不要导入 Rules/*.list、README.md 或工作流文件。

### 第二步，准备 Surge 格式订阅

在 Sub-Store 或其他订阅转换工具中选择 Surge 输出格式，结果应当是 Surge 节点行，例如下面的形式。

```ini
香港节点 = ss, example.com, 443, encrypt-method=aes-128-gcm, password=REDACTED
```

这里只是格式示例，不能把示例地址或密码直接使用。

以下三个内容需要区分。

| 内容 | 作用 | 能否当作节点订阅填入 |
|---|---|---|
| Sub-Store 的 Surge 输出链接 | 让 Surge 获取 Surge 格式节点 | 可以；`sub.store/download/...` 由主配置内置重写处理 |
| Sub-Store 模块 URL | 单独安装或更新模块 | 不要填入 AllServer；本配置已内置最小重写 |
| Sub-Store 网页预览地址 | 在浏览器查看文本或网页 | 不建议，预览内容不一定是可解析的订阅 |

### 第三步，只修改一处订阅 URL

在 Surge 的配置编辑器中搜索 YOUR_SUBSTORE_SURGE_URL。只修改生效的 AllServer 行，把占位符替换为 Sub-Store 生成的 Surge 输出链接。你当前使用的 `sub.store/download/...?...target=Surge` 属于输出链接，可以填在这里；不要把官方 `Surge.sgmodule` 模块地址填入 AllServer，也不要把 URL 粘贴到 [Proxy]、[Rule]、[General] 或模块列表。

导入前，代码应当保留下面这一行结构。

```ini
AllServer = fallback, Fail-Closed, policy-path=YOUR_SUBSTORE_SURGE_URL, update-interval=3600, interval=60, timeout=300, evaluate-before-use=true, no-alert=0, hidden=0, include-all-proxies=true
```

替换后示例结构如下，示例地址仅用于说明格式。

```ini
AllServer = fallback, Fail-Closed, policy-path=https://example.invalid/surge-output, update-interval=3600, interval=60, timeout=300, evaluate-before-use=true, no-alert=0, hidden=0, include-all-proxies=true
```

保存并重新载入配置后，打开 AllServer。成功时 AllServer 会显示订阅节点，HongKong、TaiWan、Japan、Singapore 和 America 会按节点名称筛选。不要删除 Fail-Closed，它是节点全部失效时的失败关闭保底项。

## 订阅到底填写在哪里

### 公开配置的正确位置

公开版在这里保留唯一可填写的订阅占位符。打开 Surge.conf，搜索下面的标记。

```text
# Subscription
```

它位于 [Proxy Group] 的地区组之后、[Rule] 之前。当前模板实际生效的结构如下。

```ini
[Proxy Group]
AllServer = fallback, Fail-Closed, policy-path=YOUR_SUBSTORE_SURGE_URL, update-interval=3600, interval=60, timeout=300, evaluate-before-use=true, no-alert=0, hidden=0, include-all-proxies=true

[MITM]
hostname = %APPEND% sub.store

[Script]
Sub-Store Core=type=http-request,pattern=^https?:\/\/sub\.store\/((download)|api\/(preview|sync|(utils\/node-info))),script-path=https://cdn.jsdelivr.net/gh/sub-store-org/Sub-Store@b43580e93e3ca2171d62ab17d1806afdc5fadd01/sub-store-1.min.js,requires-body=true,timeout=900
Sub-Store Simple=type=http-request,pattern=^https?:\/\/sub\.store,script-path=https://cdn.jsdelivr.net/gh/sub-store-org/Sub-Store@b43580e93e3ca2171d62ab17d1806afdc5fadd01/sub-store-0.min.js,requires-body=true,timeout=900
```

不要修改 AllServer 以外的代码，也不要删除上面的 `[MITM]`、`[Script]` 段。不要把订阅链接粘贴进 [Proxy]、[Rule]、[General]、策略组选择项或模块列表。请按以下规则填写。

1. 只替换 YOUR_SUBSTORE_SURGE_URL，不要保留这个占位符。
2. 使用 Sub-Store 生成的 Surge 输出链接，不要使用模块 URL 或网页预览 URL。
3. 先确认该链接返回的是 Surge 节点文本，而不是 HTML、登录页或错误信息。
4. 真实 URL 只保存在 Surge 本地，不要提交公开仓库、截图、Issue 或 ZIP。
5. 如果要恢复模板，只需把真实 URL 替换回 YOUR_SUBSTORE_SURGE_URL。

占位符是唯一需要填写的地方。原样保留占位符时不会拉取到节点，这是为了避免公开配置泄露订阅，不会影响其他规则代码。

### Sub-Store 模块与主配置的关系

模块和订阅是两条不同的链路。当前 R12.5 已把 Sub-Store 的最小重写逻辑直接写入主配置的 `[MITM]` 与 `[Script]`，并把脚本固定放在 `Vendor/Sub-Store/`。因此你只需填写 AllServer 的唯一占位符，不需要单独安装 Sub-Store 模块，也不需要为它新建策略组。

如果 Surge 中已经手动安装过官方 Sub-Store 模块，请停用其中一个，避免同一请求被重复重写。保留主配置内置版本即可。主配置只内置下载、预览和同步接口所需的重写，不包含定时同步任务。

仓库内脚本固定于 Sub-Store `2.36.31`，来源、上游提交和许可证见 [`Vendor/Sub-Store/README.md`](Vendor/Sub-Store/README.md)。运行时通过固定提交的 jsDelivr 地址获取，不再请求 `github.com/sub-store-org/Sub-Store/releases/latest/download/...` 或依赖本仓库 Raw 脚本。若 jsDelivr 本身也出现网络中断，那是当前网络无法取得远程脚本，不能靠测速或分流规则伪造脚本内容。

官方 Sub-Store 说明和模块入口如下。

- [Sub-Store 配置说明](https://github.com/sub-store-org/Sub-Store/blob/master/config/README.md)
- [Sub-Store Surge 模块](https://raw.githubusercontent.com/sub-store-org/Sub-Store/master/config/Surge.sgmodule)

## 策略组工作方式

主配置采用一层节点汇总、二层地区筛选、三层服务选择的结构如下。

```text
[Proxy] 手工节点（可选）
    ↓ include-all-proxies=true
AllServer ← policy-path=订阅 URL
    ↓ include-other-group=AllServer + 地区正则
HongKong / TaiWan / Japan / Singapore / America
    ↓ 服务规则引用
ChatGPT / Telegram / Apple / Streaming 等
    ↓ 未匹配流量
Final → Proxy
```

### 核心策略组

| 策略组 | 当前行为 | 用途 |
|---|---|---|
| Fail-Closed | 本地不可用占位策略 | 节点不可用时避免静默直连 |
| AllServer | fallback，拉取 policy-path 并汇总 [Proxy] 节点 | 统一节点池 |
| Proxy | 手动选择默认出口 | 日常代理出口 |
| Final | 仅引用 Proxy | 未匹配流量的最终出口 |
| Domestic | DIRECT 优先，也可选 Proxy | 国内站点和国内 IP |
| EncryptedDNS | Proxy 优先，DIRECT 仅用于加密回落 | Surge 加密 DNS 请求 |
| ApplePush | Proxy 优先，DIRECT 故障回落 | APNs 推送 |
| AdBlock | REJECT 或 REJECT-DROP | 广告拦截 |

### 地区组和测速

HongKong、TaiWan、Japan、Singapore、America 都是 url-test 组。它们从 AllServer 中按节点名称筛选，并用测速结果选择可用节点。

当前测速参数如下。

| 参数 | 值 | 含义 |
|---|---|---|
| interval | 1800 | 约 30 分钟重新测速 |
| tolerance | 150 | 延迟差在容忍范围内时不频繁切换 |
| test-timeout | 8 | 单次测试超时秒数 |
| evaluate-before-use | true | 使用前先评估可用性 |

测速本身不会产生订阅链接，也不会把节点写回订阅。它只负责从已经进入策略组的节点中选可用项。出现“一片红”时先看 AllServer 是否有节点，再看节点主机是否能连通，最后才检查测速参数。

地区正则会排除名称中含“专用”“解锁”等字样的节点，并识别常见中文、英文、旗帜和地区缩写。节点名称完全不含地区信息时，可能只出现在 AllServer，不会出现在地区组。

### 软件内模块是否要单独建策略组

不需要。模块是配置扩展或任务，策略组是网络出口，两者职责不同。

| 内容 | 是否需要单独策略组 | 正确处理 |
|---|---|---|
| Sub-Store 重写 | 不需要单独策略组 | 已内置在主配置 `[MITM]` 与 `[Script]`，节点仍由 AllServer 的 policy-path 拉取 |
| Telegram 模块或脚本 | 通常不需要 | Telegram 流量使用现有 Telegram 组 |
| APNs 相关设置 | 不需要新增模块 | 使用现有 ApplePush 组和 include-apns=true |
| DNS 防绕过规则 | 不需要新增模块 | 使用现有 EncryptedDNS 组和规则顺序 |
| 手工导入节点 | 不需要 | 仅作为备用方式，AllServer 已自动拉取订阅 |

如果某个第三方模块明确要求一个专用出口，应先看模块文档，再给它配置一个普通策略组引用 Proxy 或地区组。不要因为安装了模块就复制一套节点组。

## 分流规则

规则从上到下匹配，顺序不可随意调整。当前顺序的设计重点如下。

1. 局域网发现、多播和本机地址先处理，避免局域网服务被代理。
2. sub.store 直连，避免订阅服务被错误送入代理链路；请求重写在主配置的 `[Script]` 中完成。
3. APNs 域名与网段进入 ApplePush。
4. DoH、DoH3、DoQ、DoT 和 DNS 协议进入 EncryptedDNS；常见明文 DNS 端口被拒绝。
5. Apple、国内服务、国际服务、Telegram、流媒体和游戏按具体规则处理。
6. 国内 IP 由 GEOIP,CN,Domestic 兜底。
7. UDP、STUN、QUIC 按当前配置进入代理策略。
8. 最后由 FINAL,Final,dns-failed 处理所有未匹配流量。

规则快照已经嵌入 Surge.conf，运行时不依赖远程 RULE-SET。这样上游规则临时变更时，设备不会在不知情的情况下改变分流行为。更新规则必须通过仓库脚本、锁文件和审计流程完成。

### 国内与国外分流

国内规则命中后进入 Domestic，默认直连；国内 IP 作为后置兜底。国际服务按服务组分流，常见组包括 ChatGPT、Claude、Gemini、GitHub、YouTube、NETFLIX、Disney+、HBO、PrimeVideo、Emby、TikTok、Bahamut、Spotify、Telegram、X、Google、Microsoft 和 Games。

服务组只是“选择出口”的入口，真正的节点仍来自 Proxy、地区组或 AllServer。因此订阅导入成功但某个服务组全红时，不要先添加模块，先检查该服务组引用的地区是否有节点。

## Telegram 推送与连接

Telegram 规则覆盖常见域名、ASN、IPv4 和 IPv6 网段，并统一指向 Telegram。该策略组没有 DIRECT 选项，避免 Telegram 在国内网络中被错误直连。

Telegram 的消息通知还依赖 APNs。请同时确认下面几项。

- Telegram 组中有可用节点。
- ApplePush 组可用，或至少能在代理故障时回落 DIRECT。
- [General] 中 include-all-networks=true 与 include-apns=true 没有被模块覆盖。
- 系统设置没有关闭 Surge 的网络扩展、Telegram 通知或后台刷新。

如果 Telegram 能打开但后台通知延迟，先固定一个稳定节点测试，再查看 ApplePush 的连接记录。不要把 APNs 规则统一改成 DIRECT，也不要把 Telegram 规则改到 Domestic。

## APNs 推送

配置使用下面两项。

```ini
include-all-networks = true
include-apns = true
```

ApplePush 是独立的 fallback 组，顺序为 Proxy、DIRECT。这意味着 APNs 在代理可用时优先走代理，代理故障时仍有直连回落路径，避免代理故障直接导致整机推送中断。

APNs 规则快照位于 Rules/APNs.list，并已嵌入主配置。当前覆盖 Apple 推送域名、IPv4 网段和 IPv6 网段，共 12 条快照规则。修改规则后必须重新嵌入并更新锁文件，不能只编辑 Rules/APNs.list 而不更新 Surge.conf。

include-local-networks=false 保持局域网流量不被 Surge 接管。使用 AirDrop、局域网调试或 Xcode 时，应留意网络扩展范围带来的系统副作用。

## DNS 设计

### 当前设置

```ini
dns-server = 223.5.5.5, 114.114.114.114
encrypted-dns-server = https://dns.alidns.com/dns-query, https://doh.pub/dns-query
encrypted-dns-follow-outbound-mode = false
hijack-dns = *:53
allow-dns-svcb = false
```

dns-server 是启动和引导阶段的普通 DNS 列表，encrypted-dns-server 是主用的国内可达加密 DNS 端点。encrypted-dns-follow-outbound-mode=false 表示 Surge 自身访问加密 DNS 时直连，不跟随当前代理出口，避免代理节点的域名解析再次依赖同一个代理，形成 DNS 循环。这里不使用海外 1.1.1.1/9.9.9.9 直连，避免中国移动等网络下出现请求超时。

这并不等于所有应用流量都改为直连。它只约束 Surge 自己建立加密 DNS 连接的出口方式，普通应用请求仍按 [Rule] 和策略组分流。

### DNS 防绕过

- hijack-dns 设置为 * 的 53 端口，接管常见明文 DNS 请求。
- PROTOCOL,DNS、DOH、DOH3、DOQ 和 DOT 进入受控策略。
- 53、853、8853 等未经规则允许的端口被拒绝。
- 常见公共 DNS 域名被指向 Proxy，避免应用绕过主解析路径。

如果日志提示“加密 DNS 请求被代理策略匹配，可能导致循环”，优先检查代理节点的主机名是否为域名、当前 DNS 规则是否被模块覆盖，以及 encrypted-dns-follow-outbound-mode 是否被改回 true。订阅域名不应在 [Host] 中映射到 127.0.0.1，DOMAIN,sub.store,DIRECT 用于让远程订阅按当前网络直连访问。

## 常见故障排查

### 导入订阅后策略组一片红

按下面顺序检查。

1. 先搜索 YOUR_SUBSTORE_SURGE_URL。如果还存在，说明你还没有填写唯一订阅位置，出现无节点或红色属于预期状态。
2. 确认生效的 AllServer 行中已经替换成真实 Surge 输出 URL，并且保留 policy-path=、update-interval=3600 和 include-all-proxies=true。
3. 确认 URL 返回的是 Surge 节点文本，不是 HTML、登录页、JSON 错误信息或网页预览。
4. 如果 AllServer 报 404，确认 `[MITM]` 中有 `hostname = %APPEND% sub.store`，且 `[Script]` 中同时有 `Sub-Store Core` 和 `Sub-Store Simple`；不要把模块 URL 填进 AllServer。
5. 暂时停用其他第三方模块和外部资源，重新载入配置，排除它们的 `NSURLErrorDomain:-1005` 连接中断影响。
6. 先在 AllServer 中测试一个具体节点，再看地区组测速结果。
7. 如果 `Sub-Store Core` 或 `Sub-Store Simple` 报 TLS 错误，确认脚本地址是固定提交的 `cdn.jsdelivr.net/gh/sub-store-org/Sub-Store@...`，不是旧的 `github.com/.../releases/latest/download/...`；仍无法访问 jsDelivr 时，先恢复该域名的网络访问后再更新主配置。

测速不是订阅转换器。测速只会标记节点可用性，不能修复错误的订阅格式、失效密码或不可达的节点主机。

### Sub-Store 链接打开正常，但 Surge 读取失败

浏览器能打开链接不代表 Surge 收到的是正确订阅。`sub.store` 是 Sub-Store 模块重写使用的域名，不是普通公共下载站；主配置必须保留内置重写段。官方项目也明确说明，未经过模块重写时直接访问 `sub.store` 可能返回错误或产生数据泄露风险。

- 不能是 HTML 网页、登录页、JSON 错误信息或验证码页面。
- 输出格式必须选择 Surge。
- 链接不能被 URL 编码截断，也不能漏掉必要的查询参数。
- 如果 AllServer 显示 404，先确认主配置已经载入 `[MITM]` 和 `[Script]`，再只更新 AllServer。不要反复改测速参数，测速发生在订阅成功进入策略组之后。
- 如果其他 GitHub/Gist 资源显示 `NSURLErrorDomain:-1005`，先停用这些不属于本仓库主配置的第三方资源；它们是网络连接中断，不会把 404 修好。

对于公共仓库，不要把真实链接写入 Surge.conf、README、Issue、日志、截图或 ZIP。需要自动拉取时使用个人本地副本。

### 出现 sub.store 或代理主机 DNS 循环

这类提示通常表示代理节点主机名和加密 DNS 请求被同一代理策略同时匹配。先停用修改 DNS、Host、重写或策略的模块，重新载入公开配置，再确认下面几项。

- DOMAIN,sub.store,DIRECT 仍在局域网规则之后。
- [Host] 中没有把 sub.store 映射到 127.0.0.1。
- encrypted-dns-follow-outbound-mode=false 没有被覆盖。
- 代理节点主机名可以直接解析，或为个人配置增加明确且安全的 DNS 映射。

不要为了消除提示而把所有 DNS、Telegram 或 APNs 流量固定为直连。

### Telegram 能联网但不推送

先分别测试 Telegram 会话和 APNs。Telegram 使用 Telegram 组，系统通知使用 ApplePush 组。两者不是同一条规则，也不需要增加一个“Telegram 推送模块”。确认系统通知权限、后台刷新和 Surge 网络扩展均已开启，再重载配置并重新建立连接。

### 配置提示占位符或 policy-path 错误

YOUR_SUBSTORE_SURGE_URL 是模板唯一的填写位置。未替换时不要期待出现节点；使用时将它替换为真实的 Surge 输出链接，再保存并重新载入。若已经替换仍报错，先检查 `[MITM]` 与 `[Script]` 的内置重写是否完整，再检查 URL 返回格式、访问权限和节点参数，不要删除 policy-path。

### 修改后节点数量或规则数量对不上

先确认载入的是仓库中的新版 Surge.conf，再执行审计。规则数量由嵌入脚本和锁文件共同决定，不能直接手工删减主配置末尾规则。

## 文件结构

```text
.
├── .github/workflows/
│   ├── audit.yml
│   └── unpack.yml
├── Rules/
│   ├── *.list
│   ├── APNs.list
│   ├── r10.lock.json
│   └── upstreams.lock.json
├── THIRD_PARTY_LICENSES/
├── tools/
│   ├── audit_config.py
│   ├── audit_rules.py
│   ├── embed_runtime_rules.py
│   ├── generate_checksums.py
│   ├── generate_release_manifest.py
│   ├── stage_surge_zip.py
│   ├── test_audit_config.py
│   ├── test_stage_surge_zip.py
│   └── update_service_rules.py
├── Surge.conf
├── README.md
├── CHANGELOG.md
├── NOTICE.md
├── SECURITY.md
├── CONTRIBUTING.md
├── LICENSE
├── RELEASE_MANIFEST.txt
├── SHA256SUMS.txt
└── SHA256SUMS_fixed.txt
```

## 文件用途

| 文件或目录 | 用途 |
|---|---|
| Surge.conf | Surge 最终导入和运行的主配置 |
| Rules/*.list | 本地规则快照，供审计、更新和嵌入使用 |
| Rules/APNs.list | APNs 域名、IPv4 与 IPv6 规则快照 |
| Rules/*.lock.json | 规则源、版本、哈希和嵌入状态锁定信息 |
| tools/audit_config.py | 检查配置结构、策略组和安全不变量 |
| tools/audit_rules.py | 检查规则快照、锁文件和嵌入规则数量 |
| tools/embed_runtime_rules.py | 将规则快照嵌入主配置并更新锁信息 |
| tools/generate_release_manifest.py | 生成发布文件清单和文件哈希 |
| tools/generate_checksums.py | 生成 SHA256SUMS.txt 与固定校验文件 |
| tools/stage_surge_zip.py | 安全解包并限制候选 ZIP 的可导入文件 |
| .github/workflows/audit.yml | 推送、PR 和手动触发的自动审计 |
| .github/workflows/unpack.yml | 手动验证候选 Surge.zip |
| RELEASE_MANIFEST.txt | 发布时应包含的完整文件清单 |
| SHA256SUMS*.txt | 发布文件完整性校验 |
| THIRD_PARTY_LICENSES/ | 第三方规则和材料的许可证记录 |

## 修改顺序

### 只修改 README 或说明文件

只需重新生成发布清单和校验和，命令如下。

```bash
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
```

不需要重新嵌入规则，也不需要修改 Surge.conf、Rules/*.list 或锁文件。

### 修改规则或主配置

1. 修改对应的规则快照或 Surge.conf。
2. 规则内容发生变化时运行 python3 tools/embed_runtime_rules.py。
3. 运行完整审计和回归测试。
4. 重新生成 RELEASE_MANIFEST.txt 和 SHA256SUMS.txt。
5. 检查差异，确认没有真实订阅、节点、Token、密码、Cookie、私钥或证书。

## 本地校验

在仓库根目录执行下面的命令。

```bash
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/test_audit_config.py
python3 tools/test_stage_surge_zip.py
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
sha256sum -c SHA256SUMS.txt
cmp --silent SHA256SUMS.txt SHA256SUMS_fixed.txt
```

正常结果应包括下面几项。

- 配置审计通过，且 R12 rules=5551。
- 规则审计通过，规则源和锁文件一致。
- 变异回归测试通过。
- ZIP 白名单测试通过。
- 所有 SHA-256 校验显示 OK。
- SHA256SUMS.txt 与 SHA256SUMS_fixed.txt 内容一致。

## ZIP 与 GitHub 发布

### 完整 ZIP

完整包应从仓库根目录打包，并包含 RELEASE_MANIFEST.txt 列出的全部公开文件。解压后应能看到 Surge.conf、Rules/、tools/、文档、许可证和校验文件。

发布前至少检查压缩包完整性。

```bash
unzip -t Surge_R12_*.zip
```

压缩包内不得包含 .git/、__pycache__/、.pyc、其他旧压缩包或真实订阅信息。Surge.zip 仅是 GitHub Actions 手动验证用的候选文件，不要把它当作配置订阅地址。

### GitHub 上传范围

README-only 修改通常只会改变下面四个文件。

```text
README.md
RELEASE_MANIFEST.txt
SHA256SUMS.txt
SHA256SUMS_fixed.txt
```

如果主配置和规则没有变化，不需要为了 README 再次修改或重新上传其他运行文件。完整 ZIP 需要重新打包，因为 ZIP 中的 README 和校验文件也应与仓库当前版本一致。

GitHub Actions 会对配置、规则、脚本和校验和做自动检查。提交前不要跳过审计，也不要用手工改哈希的方式掩盖文件差异。

## 安全与隐私

请勿在公开仓库、Issue、Pull Request、日志、截图或提交历史中发布下面的信息。

- 真实订阅地址和 Sub-Store 私有接口。
- 代理节点地址、端口、用户名、密码和传输参数。
- API Token、Bot Token、Cookie、会话信息和设备标识。
- 私钥、CA、客户端证书和配置备份。

如果误公开了订阅或凭据，应先在服务端撤销或更换，再清理公开文件。仅删除当前版本中的文字不能保证旧提交历史已经失效。

本仓库只审计仓库内公开配置。用户自行添加的节点、订阅、模块、MITM、脚本和重写规则不属于公开审计范围，启用前应单独检查来源和权限。

## 许可与贡献

原创脚本、配置结构和文档采用根目录 LICENSE 中的 MIT License。第三方规则、数据和材料继续遵循各自许可证，详情见 THIRD_PARTY_LICENSES/ 和 NOTICE.md。MIT License 不替代或覆盖第三方许可。

提交配置或规则变更时，请同时说明影响范围、验证命令和是否改变了分流行为。涉及私有订阅的问题请脱敏后通过私下渠道说明，不要把订阅内容贴到公开仓库。
