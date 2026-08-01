# Surge iOS Stable Fail-Closed R11 LTS

一套面向 Surge iOS 的公开、可审计、失败关闭型配置。项目将最终运行规则固化在 `Surge.conf` 中，并通过本地规则快照、锁文件、回归测试和 GitHub Actions 保持配置行为可验证。

## 核心特性

- 未匹配流量统一进入 `FINAL,Final,dns-failed`，不默认回落到直连。
- Telegram 域名及核心 IPv4、IPv6 网段强制进入 `Telegram` 代理策略。
- `include-apns = false`，iOS 系统 APNs 长连接不由 Surge VIF 强制接管。
- 保留 APNs 精确直连规则，作为已被捕获连接的兜底路径。
- 使用 AliDNS 与 DNSPod DoH，并设置固定引导地址避免首次解析循环。
- 阻断未经允许的明文 DNS、DoT 与其他常见 DNS 绕过路径。
- 运行时不使用远程 `RULE-SET`，降低上游临时变化对设备行为的影响。
- 公开仓库不保存真实订阅、代理节点、Token、密码或证书。

## 适用环境

- Surge iOS 5.14.6 或更高版本
- 规则模式
- Python 3.10 或更高版本，用于仓库审计
- Sub-Store 或其他可输出 Surge 节点订阅的工具

## 快速开始

### 1. 导入配置

在 Surge 中通过以下 Raw 地址下载配置：

```text
https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf
```

也可以下载仓库后直接导入 `Surge.conf`。

### 2. 配置订阅

公开配置中的 `AllServer` 使用不可路由的占位地址：

```ini
policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL
```

请在自己的私有副本中替换为有效订阅地址。不要把真实订阅地址提交到公开仓库。

### 3. 选择策略

导入后至少检查以下策略组：

| 策略组 | 用途 | 建议 |
|---|---|---|
| `Proxy` | 默认代理出口 | 选择稳定地区组或具体节点 |
| `Telegram` | Telegram 流量 | 保持代理，不要加入 `DIRECT` |
| `Apple` | Apple 常规服务 | 默认 `DIRECT`，按网络环境调整 |
| `Domestic` | 国内流量 | 默认 `DIRECT` |
| `Final` | 未匹配流量 | 保持仅指向 `Proxy` |
| `AdBlock` | 广告规则 | 在 `REJECT` 与 `REJECT-DROP` 中选择 |

## 网络设计

### 失败关闭

最终规则为：

```ini
FINAL,Final,dns-failed
```

`Final` 策略组只提供代理路径。新增服务未被规则覆盖时，会进入受控代理出口，而不是无条件直连。

### Telegram

Telegram 规则覆盖常见域名、ASN、IPv4 和 IPv6 网段。审计器会检查：

- `t.me` 必须进入 `Telegram`。
- 核心 Telegram IPv4 网段必须存在。
- Telegram 相关规则不得指向 `DIRECT`。

切换节点时，优先使用连接稳定、TCP 长连接表现良好的节点。

### APNs

配置使用：

```ini
include-apns = false
```

系统推送通道由 iOS 自行维护，减少代理节点切换或长连接中断造成的通知延迟。配置中的 APNs 精确 `DIRECT` 规则只处理已经进入规则链的连接。

### DNS

默认加密 DNS：

```text
https://dns.alidns.com/dns-query
https://doh.pub/dns-query
```

`[Host]` 中固定了引导 IP。端口 53、853 和 8853 的非授权请求会被阻断，常见第三方加密 DNS 域名按规则进入代理，避免应用绕过配置中的解析路径。

## 仓库结构

```text
.
├── .github/workflows/       GitHub Actions
├── Rules/                   本地规则快照与锁文件
├── THIRD_PARTY_LICENSES/    第三方许可证
├── tools/                   审计、嵌入与安全解包工具
├── Surge.conf               最终运行配置
├── README.md                使用说明
├── CHANGELOG.md             版本记录
├── NOTICE.md                来源和修改声明
├── SECURITY.md              安全规范
├── CONTRIBUTING.md          维护流程
└── SHA256SUMS.txt            文件完整性校验
```

## 本地校验

在仓库根目录执行：

```bash
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/test_audit_config.py
python3 tools/test_stage_surge_zip.py
sha256sum -c SHA256SUMS.txt
```

所有命令通过后再提交配置。

## 规则维护流程

1. 修改 `Rules/*.list` 或 `Surge.conf`。
2. 如规则源发生变化，运行对应更新或嵌入工具。
3. 运行 `python3 tools/embed_runtime_rules.py` 更新锁文件元数据。
4. 执行完整审计和回归测试。
5. 重新生成 `SHA256SUMS.txt`。
6. 检查差异，确认没有真实订阅、Token、密码、证书或私有节点。

## 常见问题

### Telegram 能联网但没有后台通知

确认 `include-apns = false`，重新载入配置并重启 Surge 与 Telegram。不要把 APNs 强制绑定到会自动切换的代理策略组。

### 导入后没有节点

公开配置只包含 `Fail-Closed` 哨兵节点。必须把 `AllServer` 的占位订阅地址替换为自己的有效地址。

### GitHub Actions 报锁文件哈希过期

运行：

```bash
python3 tools/embed_runtime_rules.py
```

随后重新生成 `SHA256SUMS.txt` 并再次执行审计。

### 可以删除 Rules 目录吗

不可以。设备运行时虽然不远程加载这些文件，但仓库审计、规则更新和重新嵌入依赖它们。

## 安全说明

不要向公开仓库提交以下内容：

- 真实订阅 URL 或 Sub-Store 私有接口
- 代理节点地址、端口和凭据
- API Token、Bot Token、密码或 Cookie
- 私钥、CA、客户端证书或设备标识

发现安全问题时，请按照 `SECURITY.md` 处理，不要在公开 Issue 中披露敏感信息。

## 第三方来源与许可证

第三方规则版权归各自作者或项目所有。来源说明和许可证副本位于 `NOTICE.md` 与 `THIRD_PARTY_LICENSES/`。本仓库对上游规则进行筛选、固化和本地调整，不改变原项目的许可证要求。

## 仓库许可证

本仓库自行编写的配置框架、脚本与文档采用 MIT License。第三方规则快照仍适用其原始许可证，详见 `NOTICE.md` 与 `THIRD_PARTY_LICENSES/`。
