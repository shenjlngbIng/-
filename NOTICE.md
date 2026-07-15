# NOTICE

本文件记录本仓库的维护者信息、第三方项目、规则来源、许可边界、商标及免责声明。它用于保留归属并帮助后续维护者审查来源，不替代任何 `LICENSE`、上游许可证、服务条款或法律意见。

最后核对日期：**2026-07-15**

## 1. 本项目

- 项目：Surge 公开配置
- 维护者及署名：**.ᐣ**
- Telegram 用户：[@shenjlngbIng](https://t.me/shenjlngbIng)
- GitHub：<https://github.com/shenjlngbIng/->
- 主配置：`Surge.conf`
- 文档：`README.md`、`NOTICE.md`

本项目对公开 Surge 配置进行了重新组织、兼容性调整、规则顺序修正、Telegram 与 Apple Push 处理、DNS 与 IPv6 设置、泄漏防护和注释整理。

公开版本不应包含任何私人节点订阅、Token、用户名、密码、私钥、控制器密钥或带签名参数的临时 URL。使用者必须在本地私有副本中填写自己的节点订阅。

## 2. 当前许可状态

本仓库当前未声明统一的开源许可证，且本 `NOTICE.md` 本身不构成许可证授予。

在仓库所有者另行添加明确的 `LICENSE` 之前：

- 不应推定本项目原创部分已经以 MIT、Apache-2.0、GPL、AGPL、CC0 或其他许可证开放。
- GitHub 仓库公开可见不等于自动允许复制、修改、再许可或商业分发。
- 第三方内容始终受其原作者的许可证、版权声明和使用条款约束。
- 对未明确声明许可证的上游内容，不应假定存在超出法律默认范围的授权。

如果未来添加项目级 `LICENSE`，仍不得用该许可证覆盖第三方内容原有的许可证或归属要求。建议在发布新许可证前逐个确认 `Rules/` 中每个文件的准确来源和兼容性。

## 3. 主要参考项目

### 3.1 Coldvvater/Mononoke

- 项目：<https://github.com/Coldvvater/Mononoke>
- 本项目用途：主配置结构、策略设计和部分规则思路参考；`ChinaDomain.list` 的直接上游。
- 当前固定引用：

```text
https://cdn.jsdelivr.net/gh/Coldvvater/Mononoke@e8bee09b64c2f6baaa3056ed8de61c74cec56a98/Surge/Rules/ChinaDomain.list
```

在 2026-07-15 的公开仓库根目录核对中未确认到统一许可证文件。引用或再分发相关内容时，应保留作者和仓库链接，并以原仓库最新声明为准；不得因为本项目进行了修改而移除上游权利。

### 3.2 Rabbit-Spec/Surge

- 项目：<https://github.com/Rabbit-Spec/Surge>
- 本项目用途：Surge 配置、策略组、模块和规则组织方式参考。

在 2026-07-15 的公开仓库根目录核对中未确认到统一许可证文件。该仓库 README 中的免责声明、使用限制和第三方归属属于其自身声明，本项目不代替或重新解释这些条款。

### 3.3 As-Lucky/Lucky

- 项目：<https://github.com/As-Lucky/Lucky>
- 本项目用途：Surge 配置与规则组织方式参考。

在 2026-07-15 的公开仓库根目录核对中未确认到统一许可证文件。相关内容的使用范围以原仓库和原作者声明为准。

### 3.4 SukkaW/Surge 与 ruleset.skk.moe

- 源项目：<https://github.com/SukkaW/Surge>
- 生成规则仓库：<https://github.com/SukkaLab/ruleset.skk.moe>
- 规则服务：<https://ruleset.skk.moe/>
- 已公开的许可证：AGPL-3.0；个别数据文件可能另有单独许可证，以原项目说明为准。
- 本项目关联：`Ads_SukkaW_Extra.list` 的文件头明确说明其由 `Ads_SukkaW.list` 处理而来，并保留适用于 Surge `RULE-SET` 的非域名规则。

若继续公开分发或修改该衍生规则，应核对并履行 AGPL-3.0 的源码提供、许可证保留、修改说明及相应再分发义务。不能仅通过改名、移动目录或转换格式消除上游许可证要求。

AGPL-3.0 全文：<https://www.gnu.org/licenses/agpl-3.0.html>

## 4. 本仓库自托管规则

主配置中的大部分远程规则通过本仓库固定提交提供：

```text
https://cdn.jsdelivr.net/gh/shenjlngbIng/-@9b1432d57c9ea26ef24ea037481189743f1d73f6/Rules/...
```

固定提交的目的仅是控制供应链变化和保证可复现性，不改变规则内容的作者、版权或许可证。即使文件从本仓库 URL 下载，也不表示该文件全部由本仓库维护者原创。

当前配置涉及的规则类别包括：

- 广告、跟踪和拒绝规则。
- AI、开发、搜索和生产力服务。
- 社交、通信和内容社区。
- 流媒体、音乐、视频和游戏平台。
- Apple、Google、Microsoft 等系统或平台服务。
- 国内域名、中国区域服务及地理位置兜底。

由于规则集合可能经过合并、删减、格式转换或去重，后续维护者应在 `Rules/` 中为每个文件补充以下最小元数据：

1. 原始项目与原始文件 URL。
2. 原始提交、标签或获取日期。
3. 原始许可证和版权声明。
4. 本仓库所做的修改。
5. 是否包含来自多个来源的合并数据。

如果无法确认某个文件的来源或授权，不应继续扩大分发范围，也不应把它标记为本项目原创。

## 5. 官方数据与技术资料

配置和规则可能参考下列官方数据或技术资料：

### Surge

- 官方手册：<https://manual.nssurge.com/>
- General 选项：<https://manual.nssurge.com/others/misc-options.html>
- DoH：<https://manual.nssurge.com/dns/doh.html>
- Host List：<https://manual.nssurge.com/others/host-list.html>
- Rule Set：<https://manual.nssurge.com/rule/ruleset.html>
- Smart 策略：<https://kb.nssurge.com/surge-knowledge-base/zh/guidelines/smart-group>
- Fallback 策略：<https://manual.nssurge.com/policy-group/fallback.html>
- 通用策略参数：<https://manual.nssurge.com/policy/parameters.html>

这些文档用于说明 Surge 语法和行为，不表示 Surge Networks Inc. 对本项目进行审核、合作或背书。

### Apple Push Notification service

- Apple 网络端口说明：<https://support.apple.com/en-us/102266>
- Apple 企业网络使用说明：<https://support.apple.com/en-us/101555>

配置对 `*.push.apple.com`、相关 APNs 域名及部分 IPv4/IPv6 网段进行独立分流。Apple 资料、域名、网段和服务本身的权利属于 Apple 及相应权利人。

### Telegram

- Telegram 官方 CIDR 资源：<https://core.telegram.org/resources/cidr.txt>

主配置包含 Telegram 域名和 IPv4/IPv6 网段，用于网络分流。Telegram 名称、标识、服务和官方数据的权利属于 Telegram 及相应权利人。

### 其他服务

规则中出现的域名、产品名和公司名仅用于描述网络匹配对象。域名规则不构成对相关服务内容的复制，也不表示本项目获得其商标、接口、内容或服务授权。

## 6. 内容分发与网络服务

本项目使用 GitHub 和 jsDelivr 托管或分发公开文件：

- GitHub：<https://github.com/>
- jsDelivr：<https://www.jsdelivr.com/>

GitHub 和 jsDelivr 仅作为代码托管或内容分发服务出现。它们各自的名称、标识、服务和条款归相应权利人所有。使用 CDN 不会改变被分发文件的许可证，也不代表 CDN 对内容进行安全审计。

## 7. Surge 与相关商标

Surge 是 Surge Networks Inc. 的产品。本项目是独立的用户配置项目，与 Surge Networks Inc. 不存在隶属、代理、合作、认证或背书关系。

Apple、iOS、APNs、iCloud、App Store、Telegram、GitHub、Google、Microsoft、OpenAI、ChatGPT、Anthropic、Claude、Gemini、Netflix、Disney、Spotify、Steam、Epic 及其他名称和标识可能是其各自权利人的商标或注册商标。

本项目仅在兼容性说明、策略组命名和网络分流语境中进行指称性使用。任何商标的出现不表示权利人赞助或认可本项目。

## 8. 隐私与安全说明

本项目不会因为使用 Surge 或代理而自动提供匿名性。根据用户选择和配置状态：

- 国内直连服务会看到用户真实公网 IP。
- Apple Push 在代理全部失效后可能直连，从而向 Apple 暴露真实公网 IP。
- 普通 DoH 经代理时，解析服务商看到代理出口 IP；APNs 专用直连 DoH 会看到真实出口 IP。两者均能处理相应查询内容，但传输链路由 TLS 保护。
- 代理服务商能够观察连接元数据，目标服务通常看到代理出口 IP。
- GitHub、jsDelivr 和连通性测试服务能够看到规则下载或探测请求的出口 IP。
- 第三方模块、脚本、MITM、其他 VPN 和系统网络扩展可能覆盖或绕过主配置行为。

本公开配置不包含 MITM、脚本、URL Rewrite、公开控制器、私人订阅 Token 或私钥。但这只描述仓库内的主配置，不能证明用户设备上另外安装的模块、证书、描述文件或代理节点安全。

## 9. 无担保声明

在适用法律允许的最大范围内，本项目按“现状”提供，不对以下事项作明示或默示保证：

- 配置始终可导入、规则始终准确或第三方 URL 始终可访问。
- 代理节点、运营商、Apple Push、Telegram 或其他服务始终可用。
- 所有流量均被接管、所有 DNS/IP 泄漏均被阻止。
- 广告规则不存在误杀，或国内外服务的域名永远不发生变化。
- 配置适合任何特定用途、地区、设备或合规要求。
- 第三方内容完全不存在版权、许可、商标或数据来源争议。

使用者应自行审查配置、节点提供者、第三方规则、当地法律和服务条款，并自行承担使用、修改、发布或再分发所产生的风险。

## 10. 合规与移除请求

如果你是相关内容的权利人，认为本仓库遗漏署名、违反许可证、错误描述来源或应当移除某项内容，请通过以下方式联系维护者，并尽可能提供：

- 涉及的文件和具体行或规则。
- 原始来源 URL 和权利证明。
- 适用许可证或版权声明。
- 希望采取的更正、补充署名或移除方式。

联系方式：[@shenjlngbIng](https://t.me/shenjlngbIng)

维护者应在核实后补充来源、修正声明、恢复许可证信息或移除存在问题的内容。

## 11. 保留 NOTICE

复制或再分发本仓库文件时，请保留本 `NOTICE.md`、文件头署名以及所有上游版权和许可证声明。保留 NOTICE 不能代替履行许可证义务，也不能为未经授权的内容自动产生授权。
