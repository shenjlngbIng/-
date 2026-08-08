# Surge iOS Privacy + Push R12

一套面向 Surge iOS 的公开、可审计、失败关闭型配置。项目将设备实际运行规则固化在 `Surge.conf` 中，并通过本地规则快照、锁文件、回归测试、校验和与 GitHub Actions 保持配置行为可验证。

## 核心特性

- 未匹配流量统一进入 `FINAL,Final,dns-failed`，不默认回落到直连。
- Telegram 域名、ASN、IPv4 与 IPv6 网段强制进入 `Telegram` 代理策略。
- APNs 使用独立 `ApplePush` Fallback，代理可用时走代理，故障时回落直连。
- `include-all-networks = true` 与 `include-apns = true`，覆盖 Wi-Fi 和移动数据下的系统推送。
- 使用 Cloudflare 与 Quad9 IP 端点 DoH；正常情况下加密 DNS 走 `EncryptedDNS`，故障时仅回落到加密 DoH 直连。
- 阻断未经允许的明文 DNS、DoT 和常见 DNS 绕过路径。
- 运行时不使用远程 `RULE-SET`，降低上游临时变化对设备行为的影响；APNs 快照保存在 `Rules/APNs.list`。
- 公开仓库不保存真实订阅、代理节点、Token、密码或证书。
- 配置、规则源、脚本、工作流和发布文件均可通过 SHA-256 校验。

## 适用环境

| 项目 | 要求 |
|---|---|
| Surge | iOS 5.14.6 或更高版本 |
| 运行模式 | 规则模式 |
| Python | 3.10 或更高版本，建议 3.12/3.13 |
| 订阅 | Sub-Store 或其他可输出 Surge 节点订阅的工具 |

## 快速开始

### 导入配置

在 Surge 中通过 Raw 地址下载：

```text
https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf
```

也可以下载仓库后直接导入根目录中的 `Surge.conf`。

### 配置订阅

公开配置中的 `AllServer` 使用不可路由的占位地址：

```ini
policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL
```

请仅在自己的私有副本中替换为有效订阅地址。不要把真实订阅地址提交到公开仓库。

### 检查策略组

| 策略组 | 用途 | 建议 |
|---|---|---|
| `Proxy` | 默认代理出口 | 选择稳定地区组或具体节点 |
| `Telegram` | Telegram 流量 | 保持代理，不要加入 `DIRECT` |
| `ApplePush` | iOS APNs 推送 | `Proxy` 优先，`DIRECT` 故障回落 |
| `EncryptedDNS` | Surge 加密 DNS | `Proxy` 优先，`DIRECT` 仅加密回落 |
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
- `Telegram` 策略组不得包含直连路径。

切换节点时，优先使用 TCP 长连接稳定、出口变化较少的节点。

### APNs

配置使用：

```ini
include-all-networks = true
include-apns = true
```

APNs 单独进入 `ApplePush` Fallback，优先使用 `Proxy`，代理不可用时回落 `DIRECT`，避免代理故障时整机收不到通知。APNs 规则快照位于 `Rules/APNs.list`，同时已嵌入 `Surge.conf`。

修改配置后重新载入 Surge；移动数据推送依赖 `include-apns = true`。若仍无通知，可开关一次飞行模式，让系统重建 APNs 长连接。

不需要额外脚本或模块。未采用全量 Apple 代理、`akadns.net` 泛域名或 `apple.com.edgekey.net` 关键词，避免改变普通 Apple 及国内服务分流。
`include-local-networks = false` 保持局域网不被接管；若使用 AirDrop 或 Xcode，需留意 `include-all-networks` 扩大接管范围的系统副作用。

### DNS

默认加密 DNS：

```text
https://1.1.1.1/dns-query
https://9.9.9.9/dns-query
```

`encrypted-dns-follow-outbound-mode = true` 使加密 DNS 按 `EncryptedDNS` 组出站，代理优先、加密 DoH 直连回落。端口 53、853 和 8853 的非授权请求会被阻断，避免应用绕过配置中的解析路径。

## 仓库结构

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
│   ├── generate_release_manifest.py
│   ├── generate_checksums.py
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
└── SHA256SUMS.txt
```

## 文件用途

| 文件或目录 | 用途 |
|---|---|
| `Surge.conf` | Surge 最终导入和运行的主配置 |
| `Rules/` | 本地规则快照、上游锁与配置锁 |
| `tools/audit_config.py` | 检查配置结构、关键策略和安全不变量 |
| `tools/audit_rules.py` | 检查规则快照、锁文件与规则数量 |
| `tools/embed_runtime_rules.py` | 更新主配置对应的锁文件元数据 |
| `tools/generate_release_manifest.py` | 生成发布文件清单与哈希 |
| `tools/generate_checksums.py` | 重新生成 `SHA256SUMS.txt` |
| `tools/stage_surge_zip.py` | 安全解包并限制候选 ZIP 可导入文件 |
| `.github/workflows/audit.yml` | 推送和 PR 的自动审计 |
| `.github/workflows/unpack.yml` | 手动验证候选 `Surge.zip` |

## 本地校验

在仓库根目录执行：

```bash
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/test_audit_config.py
python3 tools/test_stage_surge_zip.py
python3 tools/generate_release_manifest.py
sha256sum -c SHA256SUMS.txt
```

需要更新发布清单和校验和时执行：

```bash
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
```

所有命令通过后再提交配置。

## 规则维护流程

1. 修改 `Rules/*.list` 或 `Surge.conf`。
2. 规则源发生变化时，运行对应更新或嵌入工具。
3. 运行 `python3 tools/embed_runtime_rules.py` 更新锁文件元数据。
4. 执行完整审计和回归测试。
5. 运行 `python3 tools/generate_checksums.py`。
6. 再次运行 `sha256sum -c SHA256SUMS.txt`。
7. 检查差异，确认没有真实订阅、Token、密码、证书或私有节点。

## GitHub Actions

### Audit Surge R12

在 `main` 分支推送、Pull Request 和手动触发时运行，使用 Python 3.12 与 3.13 检查：

- Python 工具可编译性
- Surge 配置不变量
- 规则源和锁文件
- 破坏性变更回归测试
- ZIP 安全暂存逻辑
- 全部 SHA-256 校验和

### Validate Surge R12 ZIP

手动触发前，将候选文件命名为 `Surge.zip` 放在仓库根目录。工作流只解包白名单文件，并对暂存配置和规则进行审计。`Surge.zip` 属于临时文件，不应长期提交。

## 常见问题

### Telegram 能联网但没有后台通知

确认 `include-all-networks = true`、`include-apns = true`，并检查 `ApplePush` 是否有可用代理。重新载入配置并重启 Surge 与 Telegram；不要把 APNs 规则改成固定 `DIRECT`。

### 导入后没有节点

公开配置只包含 `Fail-Closed` 哨兵节点。必须把 `AllServer` 的占位订阅地址替换为自己的有效地址。

### GitHub Actions 报锁文件哈希过期

运行：

```bash
python3 tools/embed_runtime_rules.py
python3 tools/generate_checksums.py
```

随后重新执行完整审计。

### SHA256SUMS 校验失败

说明被校验文件已发生变化。先确认变化是有意的，再运行 `python3 tools/generate_checksums.py`，不要手工修改单个哈希值来绕过检查。

### 可以删除 Rules 目录吗

不可以。设备运行时虽然不远程加载这些文件，但仓库审计、规则更新和重新嵌入依赖它们。

### 可以上传 __pycache__ 或 pyc 文件吗

不可以。这些是本地 Python 缓存，已由 `.gitignore` 排除。发现后应删除。

## 故障排查

| 现象 | 优先检查 |
|---|---|
| Surge 导入报语法错误 | 文件是否完整、UTF-8、LF 换行，最终规则是否存在 |
| Telegram 无法连接 | `Telegram` 策略是否选中有效节点，核心网段是否命中 |
| Telegram 无后台推送 | `include-all-networks` 与 `include-apns` 是否为 `true`，`ApplePush` 是否有可用代理 |
| 所有代理服务不可用 | `AllServer` 是否仍为占位地址，订阅是否有效 |
| CI 报重复规则 | 检查 `Surge.conf` 中是否重复嵌入规则 |
| CI 报规则数量不一致 | 检查 `Rules/*.list` 与 `Rules/r10.lock.json` |
| CI 报校验和失败 | 重新生成并审查 `SHA256SUMS.txt` |

## 安全说明

不要向公开仓库提交：

- 真实订阅 URL 或 Sub-Store 私有接口
- 代理节点地址、端口和凭据
- API Token、Bot Token、密码或 Cookie
- 私钥、CA、客户端证书或设备标识

发现安全问题时，请按照 `SECURITY.md` 处理，不要在公开 Issue 中披露敏感信息。

## 版本与提交

建议使用语义清晰的提交信息：

```text
feat: add service routing
fix: correct Telegram routing
ci: improve audit workflow
docs: update usage guide
refactor: simplify profile comments
```

稳定版本建议创建 GitHub Release，并附上 `Surge.conf`、版本说明和 SHA-256。

## 许可证与第三方来源

本仓库原创脚本、配置结构和文档采用 `LICENSE` 中的 MIT License。第三方规则和材料仍遵循各自许可证，来源与许可证副本位于 `NOTICE.md` 和 `THIRD_PARTY_LICENSES/`。
