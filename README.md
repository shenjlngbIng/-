# Surge iOS Privacy + Push R12

这是面向 Surge iOS 的公开、可审计、失败关闭型远程规则集配置。当前包以 `ChinaDomain 顺序修正版` 为底稿，保留已审计的 `Rules/*.list` 内容，并把这些文件改为由同一仓库 Raw 地址在运行时加载。这样可以更新规则文件而不必重新生成主配置，同时仍由仓库锁文件、SHA-256 和审计脚本约束来源与内容。

## 先看结论

- 主配置文件是根目录的 `Surge.conf`。
- 订阅转换由手机中单独安装的官方 Sub-Store 模块完成。
- 主配置不包含 `Sub-Store Core`、`Sub-Store Simple` 或 Vendor/Sub-Store 文件；也不依赖任意第三方运行时规则源。
- 运行时使用 27 个仓库自有 `RULE-SET`，地址统一为 `https://raw.githubusercontent.com/shenjlngbIng/-/main/Rules/`。
- `Rules/*.list` 是规则源文件，`Rules/r10.lock.json` 是远程规则集清单，记录每个文件的 URL、策略、条目数和 SHA-256。
- `AllServer` 使用 `fallback`，每 60 秒检查节点，单个节点超时 300 秒，启动前先评估可用性。
- `Proxy` 默认优先使用 `AllServer`，然后才是地区组。
- 加密 DNS 使用 `DIRECT` 出站并绕过代理规则，避免代理服务器域名被加密 DNS 请求反向解析而形成循环。
- 公开配置不使用 `system` 或运营商 DNS；加密 DNS 使用阿里 DNS 的 HTTPS 与 TLS 双通道，并为其保留多地址引导映射。
- 真实订阅链接、节点、密码、Token、MITM 私钥和证书不进入公开仓库。
- `Fail-Closed` 显示红色是预期行为，它是故障关闭哨兵，不是真实代理节点。
- 参考 Aegis 和主流 Surge 配置的模块化、DNS 接管、UDP 失败关闭和显式拒绝思路；Aegis 的 Scam/Quarantine 等高误报威胁情报源不直接启用。

## 适用环境

| 项目 | 要求 |
|---|---|
| 客户端 | Surge iOS 5.14.6 或更高版本 |
| 模式 | 规则模式 |
| 推送 | `include-all-networks = true`、`include-apns = true` |
| 蜂窝服务 | `include-cellular-services = true`，减少运营商蜂窝服务的 DNS 绕过 |
| 订阅转换 | Surge 中单独启用官方 Sub-Store 模块 |
| 仓库维护 | Python 3.10 或更高版本，仅用于审计和发布检查 |

## 配置文件中的关键设置

公开仓库只保留不可路由的占位符：

```ini
[Proxy Group]
Proxy = select, AllServer, HongKong, TaiWan, Japan, Singapore, America, no-alert=0, hidden=0, include-all-proxies=0
AllServer = fallback, Fail-Closed, policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL, update-interval=3600, interval=60, timeout=300, evaluate-before-use=true, no-alert=0, hidden=0, include-all-proxies=true
```

这几个参数的作用如下：

| 参数 | 作用 |
|---|---|
| `fallback` | 节点不可用时自动尝试后续节点 |
| `Fail-Closed` | 没有可用节点时不允许静默直连 |
| `update-interval=3600` | 每小时刷新一次订阅策略 |
| `interval=60` | 每 60 秒重新检查回落节点 |
| `timeout=300` | 单个节点的健康检测超时 |
| `evaluate-before-use=true` | 使用前先评估节点状态 |
| `include-all-proxies=true` | 接收订阅输出中的全部代理节点 |

## 手机端首次配置

### 1. 安装并启用官方模块

在 Surge 中单独安装并启用官方 Sub-Store 模块：

```text
https://raw.githubusercontent.com/sub-store-org/Sub-Store/master/config/Surge.sgmodule
```

只保留一套订阅转换模块。不要再把 Core、Simple 脚本复制到主配置，也不要把 `Surge.sgmodule` 地址填入 `AllServer`。

本包没有主配置内的 `[Script]` 段，主配置中的订阅地址只负责接收节点；模块负责把订阅转换为 Surge 格式。

### 2. 导入主配置

可以直接导入根目录的 `Surge.conf`，也可以使用仓库 Raw 地址：

```text
https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf
```

公开文件导入后，`AllServer` 暂时不会有真实节点，因为其中是占位地址。这是为了避免公开仓库泄露个人订阅。

### 3. 在私有副本中填写订阅

只在自己的私有副本中修改 `Proxy Group` 下的 `AllServer`，只替换 `policy-path=` 后面的地址。地址必须是 Sub-Store 生成的完整 Surge 输出链接，并且通常包含 `target=Surge`。

不要填写以下地址：

| 地址 | 是否可填入 `policy-path` | 原因 |
|---|---|---|
| Sub-Store 生成的 Surge 输出链接 | 可以 | 返回 Surge 节点格式 |
| Sub-Store 网页预览地址 | 不可以 | 只用于查看，不是策略输出 |
| `Surge.sgmodule` 地址 | 不可以 | 这是模块地址 |
| GitHub Raw 主配置地址 | 不可以 | 这是配置文件地址 |
| 含 Token 的私有订阅地址 | 只能私下使用 | 不得提交公开仓库 |

截图或界面中显示的 `-copy8759` 只是某条订阅的名称标识，不是固定后缀。不要手动添加或删除它，直接从 Sub-Store 复制这条订阅生成的完整 Surge 输出链接即可。

### 4. 重新载入并更新

保存私有配置后按以下顺序操作：

1. 重新载入主配置。
2. 打开 Surge 的“外部资源”。
3. 只更新 `AllServer`。
4. 等待策略组完成第一次节点评估。

不要为了更新 `AllServer` 同时更新所有 GitHub、Gist 或其他第三方外部资源。那些资源超时不会决定代理节点是否可用。

## 节点全红时怎么判断

### 正常情况

`Fail-Closed` 红色是正常的。它指向本地无效端口，只用于在没有可用节点时阻止流量泄漏。

### 订阅已经成功

如果 `AllServer` 中已经出现真实节点名称，说明 Sub-Store 输出和订阅导入已经成功。此时问题不在 ChinaDomain 规则，也不在订阅转换脚本。

### 真实节点全部红色

恢复旧版回落参数后，如果所有真实节点仍然红色，通常是以下原因之一：

- 机场节点已过期、停机或达到流量限制。
- 节点密码、端口或加密方式已经变化。
- Shadowsocks 的混淆参数与服务端不匹配。
- 当前网络无法连接节点服务器。
- `proxy-test-url` 在当前网络下无法完成检测。

配置只能改善检测和回落逻辑，不能修复服务商已经失效的节点。此时应点击一个真实节点查看具体错误，不要把完整订阅链接、节点密码或 MITM 证书发到公开位置。

## 分流设计

规则按照从上到下的第一条命中原则执行：

```text
局域网与组播
→ DNS 防绕过与端口阻断
→ APNs 远程规则集
→ Apple、国内服务和广告
→ AI、流媒体、Telegram 与国际服务
→ ChinaDomain 远程规则集
→ GEOIP,CN
→ STUN、QUIC、UDP
→ FINAL
```

最终规则为：

```ini
FINAL,Final,dns-failed
```

`Final` 策略组同时提供 `Proxy` 和 `REJECT`。正常流量选择 `Proxy`；没有可用代理时可以明确选择 `REJECT`，避免误以为故障流量已经安全直连。未匹配流量最终进入 `Final`，并携带 `dns-failed`，不会因为远程规则集暂时失败而静默放行。

本版使用运行时远程 `RULE-SET`，但所有运行时 URL 都指向本仓库的 `Rules/*.list`，不是任意第三方 URL。这样保留了原先的人工删减、规则顺序和策略映射，也允许规则文件独立更新。远程规则集不可用时，仍由后面的 `GEOIP,CN`、协议规则和最终失败关闭策略继续决定行为。

本版不增加 P2P 端口 `DIRECT`，不把所有 UDP 强制改为直连，也不使用宽泛的 `DOMAIN-SUFFIX,cn,DIRECT`。UDP、STUN 和 QUIC 仍按显式策略处理，设备或代理不支持 UDP 时按 `REJECT` 处理。

### ChinaDomain 顺序

`ChinaDomain.list` 远程规则集放在国际服务规则之后、`GEOIP,CN` 之前。这样可以先命中 ChatGPT、YouTube、Netflix、Telegram、GitHub 等专用规则，再将未命中的国内域名交给 `Domestic`。它不会覆盖前面已经命中的国际服务。

不要把 ChinaDomain 移到国际服务规则之前，也不要用一个宽泛的中国域名规则替换现有快照。

### APNs

APNs 使用独立 `ApplePush` Fallback：

```ini
ApplePush = fallback, Proxy, DIRECT, interval=60, timeout=300, no-alert=0, hidden=0
```

代理可用时优先使用代理，代理失败时回落直连。APNs 规则源保存在 `Rules/APNs.list`，主配置通过远程 `RULE-SET` 加载它；更新规则文件后，Surge 会在外部资源更新时重新获取。移动数据推送依赖 `include-apns = true`。

### 加密 DNS

本版不把 `system`、运营商 DNS 或国内明文 DNS 写入公开配置。`dns-server = 223.5.5.5, 223.6.6.6` 仅作为加密 DNS 主机的引导与连通性用途；实际普通域名解析使用 `https://dns.alidns.com/dns-query` 与 `tls://dns.alidns.com`。Surge 在配置加密 DNS 后，普通 DNS 仅用于连通性测试和解析加密 DNS URL 的主机名，其他域名通过加密 DNS 解析。

`encrypted-dns-follow-outbound-mode = false` 让加密 DNS 连接固定使用 `DIRECT` 并绕过代理规则，避免节点服务器使用域名时出现 DNS 代理循环。首选通道是 HTTPS，TLS 作为备用通道；两者都不会跟随普通代理规则。若 223.5.5.5/223.6.6.6 在“网络诊断”中出现响应，那只是加密 DNS 主机的引导/连通性检查，不代表普通域名解析退回明文 DNS。

`[Host]` 中的三个 `dns.alidns.com` 映射是启动阶段的 DNS 引导地址，不是代理节点，也不会替代订阅转换。`include-cellular-services = true` 是参考 Aegis 加入的蜂窝服务接管设置；`include-local-networks = false` 则保留本配置的局域网兼容边界，避免影响 AirDrop、Bonjour 和局域网设备发现。公开配置不加入 `sub.store = 127.0.0.1`，订阅转换仍由单独安装的官方 Sub-Store 模块负责。

有效的 `DOH`、`DOH3`、`DOQ` 协议规则继续保留；无效的 `PROTOCOL,DOT` 和 `PROTOCOL,DNS` 规则不再使用。53、853、8853 端口继续阻断，用于减少明文 DNS、DoT 和常见 DNS 绕过。

## 仓库覆盖与删除清单

上传本包时，应将压缩包内的文件解压后覆盖仓库同名文件。不要把 ZIP 文件本身作为 Surge 配置上传。

本包内没有以下内容。若旧仓库仍然存在，删除它们即可：

```text
Vendor/Sub-Store/
THIRD_PARTY_LICENSES/Sub-Store-AGPL-3.0.txt
```

除上述遗留 Sub-Store Vendor 文件外，不需要为本版本额外删除正式文件。以下文件必须保留：

```text
Surge.conf
README.md
Rules/
tools/
SHA256SUMS.txt
SHA256SUMS_fixed.txt
RELEASE_MANIFEST.txt
.github/workflows/
LICENSE
NOTICE.md
SECURITY.md
CONTRIBUTING.md
CHANGELOG.md
```

真实订阅配置、私有节点文件、MITM `ca-p12`、密码和本地缓存不应上传。`__pycache__` 和 `.pyc` 只是本地缓存，也不属于仓库发布内容。

## 发布包目录

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
├── tools/
│   ├── audit_config.py
│   ├── audit_rules.py
│   ├── convert_to_remote_rules.py
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
├── RELEASE_MANIFEST.txt
├── SHA256SUMS.txt
├── SHA256SUMS_fixed.txt
└── 许可证、通知与协作文件
```

## 本地维护与验证

在仓库根目录执行：

```bash
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/test_audit_config.py
python3 tools/test_stage_surge_zip.py
python3 tools/embed_runtime_rules.py
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
sha256sum -c SHA256SUMS.txt
cmp --silent SHA256SUMS.txt SHA256SUMS_fixed.txt
```

修改 `Surge.conf` 或 `Rules/*.list` 后必须同步更新 `Rules/r10.lock.json`、`RELEASE_MANIFEST.txt`、`SHA256SUMS.txt` 和 `SHA256SUMS_fixed.txt`。不要手工改校验值，使用仓库中的脚本生成。虽然锁文件名称仍保留 `r10.lock.json` 以兼容旧工作流，但其当前 schema 为 5，模式是 `remote-ruleset`。

## 安全提醒

- 真实订阅 URL 通常包含 Token，等同于账号凭据。
- 节点密码、端口、服务器地址和客户端证书不要提交公开仓库。
- `[MITM]` 中的 `ca-p12` 与 `ca-passphrase` 属于私钥材料，不要放入公开配置。
- 如果私钥或订阅链接已经发送到聊天、Issue、日志或仓库，应立即更换订阅 Token，并重新生成 Surge MITM 证书。
- 遇到 `sub.store` 证书无效时，不要信任异常证书，也不要关闭 TLS 安全校验。

## 远程规则集清单

主配置当前引用 27 个仓库自有规则集，策略映射由 `tools/convert_to_remote_rules.py` 和 `Rules/r10.lock.json` 共同固定：

| 规则文件 | 策略 | 用途 |
|---|---|---|
| `APNs.list` | `ApplePush` | 系统推送 |
| `AppleCN.list` | `Apple` | Apple 国内服务 |
| `WeChat.list`、`Direct.list`、`ChinaDomain.list` | `Domestic` | 国内服务与精选直连 |
| `Ads_Custom_Extra.list` | `AdBlock` | 广告与追踪 |
| `ChatGPT.list`、`Claude.list`、`Gemini.list` | 对应策略组 | AI 服务 |
| `YouTube.list`、`Netflix.list`、`Disney.list`、`HBO.list`、`PrimeVideo.list`、`Emby.list` | 对应策略组 | 视频服务 |
| `TikTok.list`、`Bahamut.list`、`BiliBiliIntl.list`、`Spotify.list`、`ProxyMedia.list` | 对应策略组 | 音视频及区域服务 |
| `Telegram.list` | `Telegram` | Telegram |
| `Github.list`、`Twitter.list`、`Google.list`、`OneDrive.list`、`Microsoft.list`、`Game.list` | 对应策略组 | 国际服务和游戏 |

规则文件必须保留在仓库中。远程化不是删除 `Rules/`，而是把主配置中的大段嵌入文本替换成可审计的远程引用。每次修改规则源后，应重新执行锁文件、清单和校验和生成脚本。

## 为什么不直接启用 Aegis 威胁情报列表

Aegis 的远程规则集结构值得参考，但 `Scam_Block`、`Quarantine_Block`、`Malware_IOC_Block` 等列表属于外部威胁情报。它们规模大、更新快，可能把地区性站点、公共服务或用户需要的网站误判为拒绝目标。当前版本只吸收模块化远程引用、DNS 接管、UDP 失败关闭、显式 `REJECT` 和审计锁定这些可验证的结构，不把未经独立复核的高误报列表加入主链路。

## 版本边界

本版本解决的是远程规则集迁移、配置结构、无效规则、ChinaDomain 顺序、节点测速和失败回落问题。它不会保证任何机场节点永久可用，也不会替换服务商提供的节点协议、密码或服务器。远程规则集的可用性还取决于 GitHub Raw 的网络可达性；主配置因此保留显式的失败关闭边界。
