# Surge iOS Strict Hybrid R10

这是面向 Surge iOS 的失败关闭配置。威胁模型是：国内与非推送 Apple 的逐条白名单属于明确直连选择；APNs、境外、未知、未获准的 DNS、IPv4/IPv6、UDP、QUIC 与 STUN 不得因为节点、规则、解析或订阅失效而回落到互联网直连。

R10 不包含真实节点、订阅 URL、Token、MITM、脚本或 Rewrite。公开文件没有可用节点时会进入 `Fail-Closed`，这是预期结果。

> [!IMPORTANT]
> Surge 必须保持“规则模式”，设备上不得加载未经审计的 Module。全局直连模式和额外 Module 都能绕过本配置自身的闭环。

## 当前状态

最后审计日期：**2026-07-20**

| 项目 | R10 |
| --- | --- |
| 目标平台 | Surge iOS |
| 最低版本 | 5.14.6+ |
| 配置段 | 5 |
| 策略组 | 30 |
| 有效规则 | 5599 |
| 固定内嵌服务规则 | 4483 条，来自 22 个源文件 |
| 固定内嵌直连规则 | Apple 166 条、Domestic 882 条 |
| 外部规则 URL | 0 |
| 动态 `policy-path` | 0 |
| 可到达 `DIRECT` 的策略组 | 仅 `Apple`、`Domestic` |
| IPv6 | `true`，VIF `auto` |
| 系统接管 | 全网络、APNs、可联网蜂窝系统服务 |
| UDP 失效行为 | `REJECT` |
| API、面板、Wi-Fi/热点共享 | 关闭 |
| SHA-256 | `9277699cf4545f6cc67a072c411c4efb8673e263aaec9e91b4459c237f1206ff` |

## 导入地址

开发分支：

```text
https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf
```

`main` 是可变地址。正式部署应在审计通过并提交后，将 `main` 替换为该次完整 40 位提交号。

## 使用步骤

1. 将 `Surge.conf` 放在仓库根目录。
2. 在 Surge 中选择“规则模式”。
3. 只在设备私有副本的 `[Proxy]` 中加入已经审计的静态节点。
4. 不要把真实节点、密码、订阅 URL 或 Token 提交到公开仓库。
5. 不要在 `AllServer` 加入动态 `policy-path`。名称正则只能过滤名称，不能证明外部策略不是 `direct` 别名。
6. 导入后先确认 `Proxy` 能选到真实节点，再进行联网测试。

公开版本只有：

```ini
[Proxy]
Fail-Closed = http, 127.0.0.1, 1
```

因此直接导入公开文件但没有私有节点时，境外和未知流量会连接失败，不会回落直连。

## 策略闭环

```text
未知 / 未命中 / DNS 失败
          ↓
FINAL,Final,dns-failed
          ↓
Final → Proxy
          ↓
地区组 / AllServer
          ↓
已审计静态节点，或 Fail-Closed
```

- `Final` 只有 `Proxy`。
- `Proxy`、五个地区测速组、`AllServer` 和全部境外服务组均不能到达 `DIRECT`。
- `Domestic`、`Apple` 是仅有的直连可达组，默认分别选择明确的 `DIRECT`。
- `[Proxy]` 中的公开失败哨兵连接 `127.0.0.1:1`，失败时没有直连备用路径。
- 自定义 `direct`/`reject` 别名、`skip-cert-verify=true`、`sni=off` 与动态节点文件会被审计器拒绝。

## DNS 边界

R10 保留两个明确的国内传统 DNS 控制面例外：

```ini
dns-server = 223.5.5.5, 119.29.29.29
hijack-dns = *:53
```

它们不是业务流量的回退策略，且没有 `system` DNS。两个服务器由 Surge 同时查询；相较 R9 删除了第三个上游，减少每次解析的请求扇出。

规则层还执行：

- 常见公共及国内应用 DoH 域名进入 `Proxy`。
- 53、853、8853 端口在未被 DNS 劫持器处理时拒绝。
- 不配置 Surge 加密 DNS，因此删除容易产生错误安全含义的 `PROTOCOL,DOH/DOH3/DOQ`。
- 未知 HTTPS 最终进入 `Proxy`。

不使用 MITM 时，配置无法识别伪装成普通 HTTPS、且部署在已经批准直连域名上的任意应用内 DoH。这是协议可见性的边界，不能用静态域名规则宣称绝对消除。

## IPv4、IPv6、UDP、QUIC 与 STUN

- `include-all-networks=true`，防止应用通过绑定物理接口绕过 VIF。
- `include-apns=true`，APNs 由 Surge VIF 接管。
- `include-cellular-services=true`，接管互联网可路由的 VoLTE、Wi-Fi Calling、IMS、MMS、Visual Voicemail 等系统业务。
- 运营商直接路由到私网的蜂窝业务可能始终位于隧道外，这是 iOS/运营商边界。
- `ipv6=true`、`ipv6-vif=auto`；未知 IPv6 与未知 IPv4 一样最终进入代理。
- 服务专用代理规则先分类，随后 `STUN → QUIC → UDP` 守卫位于所有互联网直连白名单之前。
- 国内或 Apple 的 UDP 也不会因为域名白名单而直连；局域网的精确 mDNS/SSDP 例外除外。
- `udp-policy-not-supported-behaviour=REJECT`，节点不支持 UDP 时直接拒绝。
- `block-quic=all-proxy`，代理策略上的 QUIC 被阻止并由应用自行回落到 TCP，而不是 DIRECT。
- `icmp-forwarding=false`。

## Apple、APNs 与 Telegram

R10 保留上一版 APNs 特殊设计：

- 4 条 APNs 域名规则。
- 5 条 Apple 官方 IPv4 网段规则。
- 4 条 Apple 官方 IPv6 网段规则。
- APNs 与 Telegram 长连接主机保持 Raw TCP。
- 全部 APNs 规则位于 Apple/Domestic 直连白名单之前并固定绑定 `Proxy`。

`Telegram.list` 从外部引用改为同一固定快照的本地内嵌，仍绑定 `Telegram` 代理组。本轮只保留和审计上述路由设计，不把它表述为 Telegram 推送问题的完整诊断。

## 直连白名单清洗

R10 内嵌直连敏感规则，不让远程更新获得直连权限：

- `AppleCN.list`：166 条，绑定 `Apple`。
- `WeChat.list`：删除 2 条宽泛 `USER-AGENT` 与 1 条 `IP-ASN`，保留 30 条域名规则。
- `Direct.list`：只保留 4 个明确腾讯域名及 `goodnotesapp.com.cn`，共 5 条。
- `ChinaDomain.list`：删除 3 条 `USER-AGENT`、13 条 DNS 服务域名和 4 条重复项，保留 847 条。

Google、`api.goodnotescloud.com`、`fileball.app` 与 `pianyuan.org` 不再获得国内直连。

## 规则供应链

运行时不存在 `RULE-SET`/`DOMAIN-SET` URL。配置将 22 个代理/拒绝源文件压平为普通 iOS 规则，并按原始顺序删除 154 条永远不会命中的重复条件。四个直连源另按上述规则清洗。

`Rules/r10.lock.json` 固定：

- 本地来源提交 `541641b64bf57ba83ccb9df6c59bd15b447ac265`。
- 26 个运行时源文件的 SHA-256。
- 原始有效项数量、实际内嵌数量、角色与目标策略。

`Rules/upstreams.lock.json` 继续记录 19 个 blackmatrix7 服务快照的直接上游提交、文件路径、Blob、SHA-256 和本地排除项。详细许可与修改说明见 `NOTICE.md` 和 `THIRD_PARTY_LICENSES/`。

## 仓库文件处理

升级 R10 不需要删除任何已跟踪文件：

- `Rules/`：保留，供生成、审计和来源追踪使用。
- `NOTICE.md`、`THIRD_PARTY_LICENSES/`：必须保留。
- `tools/`：已更新为 R10 生成器和审计器。
- `.github/workflows/`：已更新为 R10 检查。
- `tools/__pycache__/`：本地缓存，已由 `.gitignore` 忽略，不要上传。

未被 R10 运行时加载的规则快照仍可保留作来源与比较资料；它们不会因为存在于 `Rules/` 就自动进入 Surge。

## 本地审计

在仓库根目录运行：

```bash
python3 -m json.tool Rules/upstreams.lock.json >/dev/null
python3 -m json.tool Rules/r10.lock.json >/dev/null
python3 -m py_compile tools/*.py
python3 tools/update_service_rules.py --verify-lock
python3 tools/audit_rules.py Rules
python3 tools/embed_runtime_rules.py Surge.conf --check
python3 tools/audit_config.py Surge.conf
python3 tools/test_audit_config.py
python3 tools/test_stage_surge_zip.py
```

预期核心输出：

```text
PASS: verified upstream lock services=19
PASS: Rules | files=32 active_entries=135256 locked_files=26 embedded=5531
PASS: generated profile is current: .../Surge.conf
PASS: Surge-Strict-Hybrid-R10.conf
PASS: baseline + 15 security mutations
PASS: ZIP allowlist regression cases=12
```

`.github/workflows/audit.yml` 会在 push、pull request 和手动触发时执行同一套检查。

## 真机验收

静态审计通过不等于真机网络、通知或温度已经得到证明。至少检查：

1. 全部真实节点关闭时，境外和未知目标失败且不显示本地公网出口。
2. 国内 TCP 命中 `Domestic`，国内 UDP/QUIC/STUN 命中代理守卫。
3. 未知 IPv4、IPv6 和域名命中 `Final → Proxy`。
4. APNs 域名与官方网段无论 `Apple` 当前选择如何都命中 `Proxy`。
5. Wi-Fi 与蜂窝网络分别测试；确认没有额外 Module、脚本、DNS 或策略订阅。
6. 在稳定信号、非充电条件下静置至少 15 分钟记录温度、电量与事件数量。

严格接管全网络与蜂窝系统服务可能比平衡配置增加网络扩展工作量。若关闭 `include-cellular-services` 或 `include-all-networks` 来降低负载，就不再满足本 README 声明的完整接管范围。

## 许可与免责声明

本仓库包含或改编了多个第三方规则来源。保留 `NOTICE.md`、上游文件头和 `THIRD_PARTY_LICENSES/`；规则名称、服务标识和网络数据不代表本项目拥有相关服务或商标。

该配置不构成隐私、匿名、网络可用性或通知送达保证。设备全局出站模式、额外 Module、iOS/运营商排除项、节点实现和服务端行为均可能影响最终结果。
