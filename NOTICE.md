# NOTICE

本文件记录本仓库的项目身份、第三方内容、参考项目、许可证边界、网络数据暴露、商标及免责声明。它用于保留归属并帮助后续维护者进行来源审计，不替代任何上游 `LICENSE`、版权声明、服务条款或专业法律意见。

最后核对日期：**2026-07-18**

## 1. 项目身份与范围

- 项目：Surge iOS 严格闭锁配置
- 维护者及署名：**.ᐣ**
- 联系方式：[@shenjlngbIng](https://t.me/shenjlngbIng)
- GitHub：<https://github.com/shenjlngbIng/->
- 主配置：`Surge.conf`
- 主要文档：`README.md`、`NOTICE.md`、`CHANGELOG.md`
- 目标平台：Surge iOS

本项目在公开配置基础上进行了大幅重组与安全加固，包括策略闭环、规则顺序、DNS/DoH、IPv4/IPv6、UDP/QUIC/STUN、APNs 强制代理边界、控制面收缩、节点启动约束、规则快照内嵌、只读候选包验证及静态检查。

公开模板不包含真实代理节点，也不应包含可用的节点订阅 URL、Token、用户名、密码、私钥、控制器密钥、设备标识或带签名参数的临时 URL。`AllServer` 中的中文 `policy-path` 只是不可用的填写占位值；使用者应只在本地私有副本中加入自己的节点或真实链接。

## 2. 当前安全设计摘要

本 NOTICE 不代替 `README.md` 的完整安全说明。与第三方内容和数据处理直接相关的当前边界如下：

- 只有经审核并内联的国内、Apple、非互联网局域网、四条精确 mDNS/SSDP 发现地址，以及记录在配置中的启动控制面目标可以到达直连。
- APNs 不使用直连回退或专用 DNS；已审核域名和官方网段固定进入 `Proxy`，不受 `Apple` 的直连选择影响。
- 除精确 `223.5.5.5` DoH 冷启动外的加密 DNS，以及未先命中已审核服务、国内或局域网规则的 STUN、QUIC 和 UDP，不因故障回落直连。
- 22 个运行时规则集已内嵌到主配置，只能选择代理或拒绝策略，不能扩大直连集合。
- 主配置没有外部规则 URL；GitHub 与 jsDelivr 不再处于设备规则启动链。
- 公开主配置只有不可用的节点订阅文字占位值，不包含真实 URL；未替换时外部策略更新失败。主配置不执行第三方脚本，不启用 MITM 或 URL Rewrite；设备另装模块属于必须单独审核的边界。
- Wi-Fi/热点代理共享、HTTP API、外部控制器和 Web 面板均未开放。
- 配置保留 Surge iOS 兼容的轻量 HTTP 健康/延迟检测，但不主动执行带宽测速，也不包含独立带宽测速策略组。

这些设计降低“故障导致直连”的风险，但不保证所有网络流量被接管，也不构成匿名性或无泄漏保证。

## 3. 本仓库许可状态

### 3.1 没有统一项目许可证

本仓库当前未声明统一的开源许可证，本 `NOTICE.md` 也不构成许可证授予。在仓库所有者另行添加明确的项目级 `LICENSE` 前：

- 不应推定本项目原创部分已经以 MIT、Apache-2.0、GPL、AGPL、Creative Commons 或其他许可证开放。
- 仓库公开可见不等于自动允许复制、修改、再许可、商业使用或再分发。
- 第三方内容始终受原作者许可证、版权声明和使用条款约束。
- 对没有明确许可证的上游内容，不应假定存在超出法律默认范围的授权。
- 文件名、格式转换、去重、合并或固定到本仓库 URL 都不会消除原始权利。

如果未来添加项目级许可证，仍不得用它覆盖第三方内容原有的许可证、署名、通知或源代码提供要求。

### 3.2 已保存的第三方许可证

仓库当前保存：

- `THIRD_PARTY_LICENSES/SukkaW-AGPL-3.0.txt`
- `THIRD_PARTY_LICENSES/blackmatrix7-GPL-2.0.txt`

保存许可证副本只表示项目识别到相关第三方内容及义务，不表示本项目原创部分采用相同许可证，也不表示其他来源不再需要单独核对。

`Surge.conf` 当前把 blackmatrix7 的 GPL v2 规则快照直接内联到主配置，而本项目原创部分尚未声明统一许可证。该组合在公开再分发时可能产生许可证兼容与完整源代码提供问题；是否构成一个受 GPL 覆盖的整体需要结合具体事实和适用法律判断。扩大分发前应取得专业意见，或将第三方快照拆分为边界清晰、保留许可证和来源的独立文件，并确保实际加载方式仍满足安全模型。

### 3.3 合规优先级

对同一文件可能存在多个来源或许可证时，应采用以下维护原则：

1. 先定位原始数据和直接上游，而不是只记录最后一个镜像地址。
2. 保留所有适用版权声明、许可证和修改说明。
3. 不把“规则是事实数据”作为忽略整理、选择、编排或数据库权利的理由。
4. 不确定许可时，停止扩大分发并联系权利人。
5. 本 NOTICE 与上游许可证冲突时，以适用法律和上游有效许可证为准。

## 4. 内容分类

为避免把“参考过”误写为“复制了”，本仓库内容分为四类：

| 类别 | 含义 | 当前例子 |
| --- | --- | --- |
| 本项目原创或重写 | 配置闭环、审计脚本、ZIP 暂存器、文档及维护逻辑 | `Surge.conf` 的当前安全架构、`tools/`、文档 |
| 明确分发或改编的第三方内容 | 已确认存在直接来源或衍生关系 | SukkaW 广告规则、blackmatrix7 HTTPDNS 与服务规则快照、Coldvvater 快照 |
| 来源尚未逐文件补齐的自托管快照 | 本仓库分发，但不能宣称全部原创或单一来源 | 多个 `Rules/*.list` 文件 |
| 仅供比较与设计参考 | 用于审计规则组织或语法思路，不代表当前文件直接复制 | DivineEngine、GeQ1an、NobyDa、Rabbit-Spec、As-Lucky |

分类可能随来源证据补齐而调整。任何调整都应记录直接上游、固定提交、许可证和本项目修改内容。

## 5. 明确分发或改编的第三方内容

### 5.1 Coldvvater/Mononoke

- 项目：<https://github.com/Coldvvater/Mononoke>
- 本项目关系：早期主配置结构和策略设计的重要来源；当前配置已围绕新的威胁模型大幅重写。
- 直接快照：`Rules/ChinaDomain.list`
- 已记录固定来源：

```text
https://cdn.jsdelivr.net/gh/Coldvvater/Mononoke@e8bee09b64c2f6baaa3056ed8de61c74cec56a98/Surge/Rules/ChinaDomain.list
```

`ChinaDomain.list` 当前不被主配置运行时加载，仅作为来源/归档快照保留。原因是宽泛远程国内规则不应直接获得直连权限。

截至本次核对，未在仓库根目录确认统一许可证文件。相关内容不应被标记为本项目独立原创；复制或再分发前应再次检查上游最新声明并取得必要授权。

### 5.2 SukkaW/Surge 与 ruleset.skk.moe

- 源项目：<https://github.com/SukkaW/Surge>
- 规则生成项目：<https://github.com/SukkaLab/ruleset.skk.moe>
- 规则服务：<https://ruleset.skk.moe/>
- 上游许可：除上游特别注明的 `List/ip/china_ip.conf` 外，SukkaW/Surge 仓库声明为 AGPL-3.0；特例文件以其单独声明为准。
- 本项目文件：`Rules/Ads_SukkaW_Domain.list`、`Rules/Ads_Custom_Extra.list`

`Ads_SukkaW_Domain.list` 的文件头保留 SukkaW 来源、生成信息和聚合上游说明。`Ads_Custom_Extra.list` 是从历史广告输入和本项目移动端补充整理出的自定义非域名集合，不是 SukkaW 官方 `reject_extra` 全量规则；它以固定快照内嵌到主配置并绑定 `AdBlock`。

本项目对相关内容进行过格式筛选、拆分、去重或适配 Surge `RULE-SET` 的处理。本轮 Surge iOS 候选快照还删除了 3 条宽泛 `URL-REGEX`：当前配置不启用 MITM，路径级 HTTPS 匹配不能作为可靠边界。继续公开分发或修改时，应核对并履行 AGPL-3.0 的许可证保留、修改说明、对应源代码提供及其他适用义务。

AGPL-3.0 副本：`THIRD_PARTY_LICENSES/SukkaW-AGPL-3.0.txt`

官方许可证页面：<https://www.gnu.org/licenses/agpl-3.0.html>

### 5.3 blackmatrix7/ios_rule_script

- 项目：<https://github.com/blackmatrix7/ios_rule_script>
- 上游许可：GNU GPL v2，仍应以上游具体目录和文件的声明为准。
- 本项目关系：`Surge.conf` 内联了 `BlockHttpDNS.list`，19 个服务规则文件另与 blackmatrix7 的 Surge 产物合并。
- HTTPDNS 固定提交：`cdd1e3a0ae2834d3f79715d05931ac4936e22592`
- 服务规则固定提交：`c00517ce10760a93728b241923a451dfa617be80`
- HTTPDNS 内联有效规则：63 条

原始文件：

```text
https://github.com/blackmatrix7/ios_rule_script/blob/cdd1e3a0ae2834d3f79715d05931ac4936e22592/rule/Surge/BlockHttpDNS/BlockHttpDNS.list
```

本项目将该快照从外部规则改为主配置内联，并为 IP 规则保留或补充适用的 `no-resolve` 参数，以避免运行时远程变化并确保 HTTPDNS 阻断先于直连规则。

19 个服务文件的直接路径、Git blob、SHA-256、排除项和固定提交集中记录在 `Rules/upstreams.lock.json`。生成后的文件头继续保存上游声明的 `NAME`、`AUTHOR` 和 `REPO`；例如 Emby 产物保留其声明的 `justdoiting/emby-rules` 直接来源。本项目把这些固定上游与既有本地规则精确去重，过滤 Surge iOS 不执行的 `PROCESS-NAME`、未单独审核的新增 `IP-ASN`，并排除 24 条会把共享分析、身份、同意管理或公共云平台错误绑定到单一服务策略的规则。合并后的快照仍受上游 GPL v2 及文件内可能列出的更直接来源约束。

复制、修改或再分发相关部分时应保留作者、来源、固定提交和修改说明，并履行 GPL v2 的适用条件。

GPL v2 副本：`THIRD_PARTY_LICENSES/blackmatrix7-GPL-2.0.txt`

官方许可证页面：<https://www.gnu.org/licenses/old-licenses/gpl-2.0.html>

### 5.4 服务官方网络数据

主配置或规则快照包含用于网络匹配的域名、IP 网段、ASN 或端口。这些标识可能来自服务商公开文档、公开 DNS/路由数据或第三方规则整理。

目前有明确官方资料链接的例子包括：

- Apple APNs 网络说明：<https://support.apple.com/zh-cn/102266>
- Apple 企业网络服务说明：<https://support.apple.com/zh-cn/101555>
- Telegram 官方 CIDR：<https://core.telegram.org/resources/cidr.txt>

这些网络标识用于兼容性和路由匹配，不表示本项目拥有相关服务、数据库、商标或接口。配置中的网段是维护时选择的快照，不应被理解为官方资料的完整实时镜像。

## 6. 本仓库自托管规则快照

### 6.1 内嵌方式

主配置当前不通过网络加载规则。经审核的 22 个 `Rules/*.list` 文件由 `tools/embed_runtime_rules.py` 确定性生成 `[Ruleset RS_*]` 段，并直接写入 `Surge.conf`。服务规则上游由 `Rules/upstreams.lock.json` 固定；本仓库早期本地快照基线提交为：

```text
8099f3036f0f1ebde038abff98cbaec9409cd430
```

固定提交只用于记录审计来源和提高可复现性，不改变文件原作者、版权或许可证。内嵌也不代表规则全部由本仓库维护者原创，不能消除上游许可、署名和修改说明义务。

### 6.2 当前启用的 22 个文件

| 类别 | 文件 |
| --- | --- |
| 广告/拒绝 | `Ads_Custom_Extra.list`、`Reject.list` |
| AI | `ChatGPT.list`、`Claude.list`、`Gemini.list` |
| 开发与平台 | `Github.list`、`Google.list`、`Microsoft.list`、`OneDrive.list` |
| 流媒体 | `Bahamut.list`、`BiliBiliIntl.list`、`Disney.list`、`Emby.list`、`HBO.list`、`Netflix.list`、`PrimeVideo.list`、`ProxyMedia.list`、`Spotify.list`、`TikTok.list`、`YouTube.list` |
| 社交 | `Twitter.list` |
| 游戏 | `Game.list` |

这些文件只会选择代理或拒绝策略。设备无需下载它们；未命中的流量最终进入 `Final -> Proxy`，规则内容本身没有授予直连的能力。

### 6.3 Surge iOS 本地修改与能力过滤

当前 22 个内嵌源文件共有 10796 条有效项；完整 `Rules/` 目录共有 32 个 `.list` 文件、135256 条有效项。本轮本地修改包括：

- 从本轮 19 个固定上游文件过滤 17 条 `PROCESS-NAME`。其中包含 macOS 可执行文件名和 Android 包名；Surge iOS 不执行该规则类型。
- 不导入 1 条未经单独审核的新增 `IP-ASN`；既有 2 条本地 ASN 规则继续保留并强制 `no-resolve`。
- 从 `Ads_Custom_Extra.list` 删除 3 条宽泛 `URL-REGEX`。本配置没有 MITM，不把 URL 路径匹配视为可靠的移动端过滤边界。
- 排除 24 条非唯一归属的共享分析、身份、同意管理或公共云平台规则，避免手动切换单一服务地区时劫持无关应用。
- 保留 72 条 `USER-AGENT` 规则，但将其视为尽力匹配。iOS 15 以后，无 MITM 的 HTTPS 请求通常不可见真实 User-Agent；这些规则不能承担防泄漏、最终分流或失败关闭职责。
- 要求活动文件中的 `IP-ASN`、`IP-CIDR` 和 `IP-CIDR6` 全部带 `no-resolve`，避免匹配 IP 规则时意外触发本地 DNS。
- 校验每个带 `# 规则统计:` 头的文件，其声明数量必须与实际有效项一致。

这些属于平台适配和本地删改，不改变上游权利归属，也不把删改后的文件变成本项目独立原创。

本轮已按两阶段流程完成候选规则核对。`tools/update_service_rules.py` 会验证锁文件中的上游 Git blob 与 SHA-256，再执行过滤、去重和排序；`tools/audit_rules.py` 固定检查提交后源文件 SHA-256，`tools/audit_config.py` 另行固定检查每个内嵌段的名称、数量和标准化 SHA-256。`tools/embed_runtime_rules.py --check` 还会拒绝生成结果漂移。后续内容变化必须先审核、重新生成主配置并显式更新两处哈希清单。

### 6.4 当前未启用的 10 个快照

以下文件存在于完整仓库，但当前主配置不加载：

- `Ads_SukkaW_Domain.list`
- `AppleCN.list`
- `ChinaDomain.list`
- `Direct.list`
- `Doubao.list`
- `NetEaseMusic.list`
- `ProxyGFW.list`
- `Telegram.list`
- `WeChat.list`
- `bilibili.list`

“未启用”不等于“无版权或无风险”。它们仍属于仓库分发内容，必须保留和补充来源信息。发布候选包应只携带主配置实际引用的 22 个文件，以减少无关分发面。

### 6.5 来源元数据缺口

除本 NOTICE 已明确识别的文件外，部分 `Rules/*.list` 只含规则名称、更新时间或数量统计，没有完整记录直接上游、固定提交和许可证。因此当前不能可靠断言：

- 每个文件都由本仓库维护者原创。
- 每个文件都只来自单一上游。
- 文件名能够代表原始作者或原始项目。
- 格式转换后的内容自动摆脱原许可证。
- 所有文件均已取得任意用途的再分发授权。

后续维护者应为每个文件补充至少以下字段：

1. 原始项目和直接上游文件 URL。
2. 原始提交、标签或获取日期。
3. 原始版权声明和许可证。
4. 聚合规则涉及的所有已知数据来源。
5. 本仓库进行的筛选、合并、删除、重排、转换和去重。
6. 当前是否启用、绑定策略及安全影响。

来源无法确认或许可证不兼容时，应停止扩大分发、从发布包移除，并视情况从仓库删除或联系权利人。

## 7. 仅供比较与设计参考的项目

本节项目用于理解 Surge 语法、规则顺序、策略组组织、服务分类和社区惯例。除前文另有明确说明外，本仓库**不据此声称当前文件直接复制自这些项目**，也不因为参考链接而自动继承或获得其许可证。

### 7.1 DivineEngine/Profiles 与规则系统文章

- 配置与规则项目：<https://github.com/DivineEngine/Profiles/tree/master>
- 规则系统文章：<https://divineengine.net/article/surge-rule-system/>
- 参考范围：Surge 规则类型、从上到下匹配、`no-resolve`、外部 Rule Set 和分流层次。

当前配置没有直接运行 DivineEngine 的远程规则。若未来引入任何文件，必须单独记录直接文件、固定提交和许可证，不能只引用本节作为授权依据。

### 7.2 GeQ1an/Rules

- 项目：<https://github.com/GeQ1an/Rules/tree/master>
- 参考范围：历史服务分类、规则拆分和多客户端规则组织。

本次核对时，项目 README 显示内容已移除。当前仓库根目录未见许可证文件。历史内容的存在、分叉或镜像不代表可以自由再分发；若发现本仓库文件与其历史内容存在直接关系，应补充可验证来源并重新评估授权。

### 7.3 NobyDa/ND-AD

- 项目：<https://github.com/NobyDa/ND-AD>
- 上游状态：README 标明项目自 2022 年 9 月停止维护。
- 上游仓库许可证：MIT；聚合数据仍需关注其列出的各原始来源。
- 参考范围：广告与隐私规则的分类、聚合来源披露和拒绝策略用法。

当前没有把任何活动文件仅凭名称认定为 ND-AD 的直接衍生物。若后续证据表明某个广告快照来自 ND-AD，应保留其 MIT 许可证和版权声明，并继续追踪其聚合上游。

### 7.4 Rabbit-Spec/Surge

- 项目：<https://github.com/Rabbit-Spec/Surge>
- 参考范围：Surge 配置、策略组、模块与规则的组织方式，以及用本地排除层维护个人差异的思路。

截至本次核对，仓库根目录未见统一许可证文件，README 另有其自身的使用限制和免责声明。本项目只采用“候选更新先做人工差异复核”的维护思路，不复制其模块、脚本、MITM、外部控制面或整份配置；若要直接采用内容，应先确认权利和许可。

### 7.5 As-Lucky/Lucky

- 项目：<https://github.com/As-Lucky/Lucky>
- 参考范围：多客户端配置和规则组织方式。

截至本次核对，仓库根目录未见统一许可证文件。当前配置没有运行其远程规则。任何未来直接使用都需要逐文件确认来源、提交和许可。

### 7.6 参考不等于背书

本项目与上述作者和项目不存在隶属、代理、合作、认证或背书关系。列入本节只表示其公开资料对审计和设计比较有帮助。

本轮对比还采用了 SukkaW 的域名/非 IP/IP 分层审查和平台能力过滤思路，以及 blackmatrix7 的平台专属产物、来源记录与规则计数思路。现有 `# 规则统计:` 由审计器自动核对，来源和本地修改集中记录于本 NOTICE。没有因此接入新的上游运行时地址，也没有引入 Clash、Mihomo、Quantumult X、Mac 专用规则、测速、MITM、Rewrite 或脚本。

## 8. Surge 官方技术资料

配置语法和行为主要依据以下官方资料理解：

- 官方手册：<https://manual.nssurge.com/>
- General 选项：<https://manual.nssurge.com/others/misc-options.html>
- DoH：<https://manual.nssurge.com/dns/doh.html>
- Host List：<https://manual.nssurge.com/others/host-list.html>
- Rule Set：<https://manual.nssurge.com/rule/ruleset.html>
- 策略组包含：<https://manual.nssurge.com/policy-group/policy-including.html>
- 测试型策略组：<https://kb.nssurge.com/surge-knowledge-base/zh/technotes/testing-group>

这些链接用于解释语法与预期行为，不表示 Surge Networks Inc. 对本项目进行审核、合作、认证或背书。项目静态检查器也不是官方解析器。

## 9. 网络服务与供应链

### 9.1 GitHub 与规则分发

本项目使用 GitHub 托管代码；jsDelivr 仅保留在历史来源记录和部分上游链接中：

- GitHub：<https://github.com/>
- jsDelivr：<https://www.jsdelivr.com/>

设备加载主配置后不再向 GitHub 或 jsDelivr 请求 22 个规则文件。源码维护与配置更新仍依赖：

- GitHub 仓库和账户完整性。
- TLS、系统信任库和证书链。
- GitHub 仓库、账户和提交本身是否经过正确审核。
- Surge 对主配置中 Inline Ruleset 的解析行为。

CDN 不改变文件许可证，也不证明内容安全、准确、合法或及时。

### 9.2 内嵌规则的权限限制

当前 22 个内嵌 `RULE-SET` 只能进入代理或拒绝策略。这一设计把供应链风险限制为误代理、误拒绝或漏匹配；未命中目标仍由 `FINAL` 进入代理。它不能防止：

- 恶意规则导致大范围拒绝服务。
- 规则把某些服务错误送往错误的代理地区。
- 规则文件的许可证或来源争议。

### 9.3 Sub-Store 与设备模块

主配置将 `sub.store = 127.0.0.1` 与精确的本机直连规则成对锁定，用于防止 Sub-Store 的模块域名在重写或模块失效时被发送到远端代理或不受本项目控制的公共域名。该本机例外不代表本仓库分发、固定或审核了设备上已经安装的 Sub-Store 模块。

标准 Sub-Store 模块会引入 MITM、远程脚本、可选定时任务和订阅处理能力。公开模板在 `AllServer` 中仅保留 `policy-path=此处填入Sub-Store转换后的订阅链接` 的不可用文字占位值。零静态节点首次启动时，私有真实 URL 必须显式追加 `proxy=DIRECT`；该参数仅授权 Sub-Store 的上游订阅请求直接发出，但会向订阅提供者暴露用户真实出口 IP。若不接受这一控制面例外，应先静态加入经审核启动节点，并把 `proxy=` 指向该节点或策略。指定策略依赖支持 `http-client-policy` ability 的模块版本。真实 URL/Token 不得回传公开仓库。

Sub-Store 官方项目：<https://github.com/sub-store-org/Sub-Store>

### 9.4 GitHub Actions 候选包验证

`.github/workflows/unpack.yml`：

- 仅允许手动触发。
- 权限限制为 `contents: read`。
- 使用完整提交固定 `actions/checkout` 和 `actions/upload-artifact`。
- 将 ZIP 解压到临时目录前检查路径、链接、文件类型、数量和总体积。
- 对暂存后的配置和规则重新运行静态审计。
- 只上传短期 artifact，不提交、不推送、不修改仓库源文件。

工作流执行仍会把候选文件交给 GitHub Actions 运行环境和 artifact 服务处理。候选包不得包含私人节点、凭据或其他秘密。

`.github/workflows/audit.yml` 在 push、pull request 和手动触发时审计当前主配置与规则，并检查内嵌生成结果没有漂移；它使用只读仓库权限和固定提交的 checkout action。该工作流只验证公开静态模板，不接触私人节点。

## 10. 隐私与数据暴露

本仓库主配置没有分析脚本、遥测脚本或通知脚本，但使用网络配置本身必然会向若干参与方暴露元数据。

| 参与方 | 可能看到的内容 | 常见出口身份 |
| --- | --- | --- |
| 国内直连目标 | 用户公网 IP、连接时间、目标请求元数据 | 用户真实出口 |
| Apple 直连目标 | 用户公网 IP、连接时间、服务请求元数据 | 用户真实出口 |
| APNs 目标 | 推送服务器地址、连接时间、流量大小等元数据 | 代理出口 |
| 配置指定的 `223.5.5.5` DoH | DNS 查询、时间和源 IP | 用户真实出口 |
| 其他 DoH 服务 | DNS 查询、时间和代理连接元数据 | 代理出口 |
| 传统 DNS 连通性检查目标 | 探测时间、源 IP 和基础 DNS 元数据 | 用户真实出口或平台实际控制路径 |
| 代理服务商 | 目标地址、时间、流量大小等连接元数据；加密内容可见性取决于协议 | 用户真实入口 |
| 最终网站或应用服务 | 代理流量看到代理出口；直连流量看到真实出口 | 取决于策略 |
| Sub-Store 上游订阅提供者 | 使用 `proxy=DIRECT` 冷启动时可见订阅请求、时间、User-Agent 和真实出口 IP | 用户真实出口 |
| Apple 健康检测目标 | 连通性探测、时间和出口 IP | 基础网络或 Apple 当前策略路径 |
| Google 健康检测目标 | 代理节点探测、时间和代理出口 IP | 被测代理出口 |
| GitHub Actions | 候选包内容、日志和 artifact 元数据 | 托管运行环境 |

### 10.1 DNS 隐私边界

- 业务 DNS 采用 HTTPS 加密传输，但解析服务商仍能看到查询内容。
- 只有同时匹配 `PROTOCOL,DOH` 和 `DOMAIN,223.5.5.5` 的配置内置 DoH 冷启动请求直连；运营商可以观察其目标地址和连接元数据，DoH 服务可以看到查询及真实出口 IP。
- 其他 DoH 被规则强制经代理，因此本地运营商通常看到代理连接而不是普通查询内容；代理和 DoH 服务仍各自看到相应元数据。
- `dns-server = 223.5.5.5` 用于 Surge 连通性检查，不是普通 DoH 失败回退；检查本身仍可能形成直连可观察元数据。
- 53 端口劫持、已知公共 DNS 阻断和 HTTPDNS 快照不能识别所有伪装成普通 HTTPS 的自定义解析协议。

### 10.2 IP 暴露边界

以下情况会按设计显示用户真实公网 IP：

- `Domestic` 选择 `DIRECT`。
- `Apple` 选择 `DIRECT`。
- 配置指定的 `223.5.5.5` DoH 冷启动请求，以及 Sub-Store 显式 `proxy=DIRECT` 请求。
- 局域网、回环、链路本地、ULA、精确 mDNS/SSDP 和 `skip-proxy` 明确目标。
- 平台没有交给 Surge 接管的流量。

境外或未知目标出现真实公网 IP 不属于预期行为，应立即停用配置并检查出站模式、模块、其他网络扩展、规则命中、代理故障行为和系统日志。

### 10.3 健康检测

配置保留 Surge iOS 兼容的 HTTP 连通性和延迟检测。它们不会主动执行带宽测试，但仍会定期或按需向 Apple、Google 等检测目标建立连接，并暴露出口 IP、时间和基础请求元数据。Apple 探测由明确允许的直连路径发出；Google 探测仅经被测代理发出。由于探测本身未加密，本地链路或代理路径上的参与方可能观察、阻断或伪造响应，从而影响可用性判断或节点排序，但不能把境外或未知业务流量改为 `DIRECT`。上游服务规则中出现诊断域名并不表示配置会主动访问或运行相应测试。

### 10.4 日志

主配置将 `loglevel` 设为 `warning`，用于减少常规日志量，但以下位置仍可能保留记录：

- Surge 本地日志和请求记录。
- 代理服务商日志。
- DNS 服务商日志。
- 目标服务、CDN 和托管平台日志。
- 系统诊断、崩溃报告或用户手动导出的日志。

分享日志前应移除节点 IP、端口、账户信息、访问域名、设备标识、时间关联信息和任何凭据。

## 11. 安全边界与非保证事项

在适用法律允许的最大范围内，本项目按“现状”提供，不保证：

- 配置始终可以在未来 Surge iOS 版本导入。
- 所有流量、所有系统服务或所有 IPv6 都被完整接管。
- 所有 DNS、HTTPDNS、DoH、WebRTC、STUN 或 IP 泄漏都能被阻止。
- 代理节点、Apple/APNs、DNS、GitHub、Sub-Store 或健康检测目标始终可用。
- 规则没有误杀、漏匹配、过期地址或服务分类错误。
- 节点提供者不记录、修改、出售或关联用户流量。
- TLS 之外的连接元数据对本地网络、代理或目标不可见。
- 第三方文件完全不存在版权、许可证、商标或数据库权利争议。
- 配置满足任何地区、组织、服务商或用户的法律、监管与合规要求。
- 静态审计脚本覆盖 Surge 的全部语法和运行时行为。

公开模板没有真实代理节点。缺少可信节点时大量连接失败是预期的安全行为，不是可用性承诺。

## 12. 商标与关联声明

Surge 是 Surge Networks Inc. 的产品。本项目是独立用户配置，与 Surge Networks Inc. 不存在隶属、代理、合作、认证或背书关系。

Apple、iOS、APNs、iCloud、App Store、Telegram、GitHub、jsDelivr、Google、Microsoft、OpenAI、ChatGPT、Anthropic、Claude、Gemini、Netflix、Disney、HBO、Spotify、Steam、Epic 及其他名称和标识可能是其各自权利人的商标或注册商标。

这些名称仅用于兼容性说明、策略组命名、来源记录和网络分流。任何出现都不表示相关权利人赞助、认可或审核本项目。

## 13. 使用者责任

使用者应自行：

- 核对代理节点提供者、服务条款和隐私政策。
- 遵守所在地法律、组织政策和网络服务条款。
- 评估国内与非推送 Apple 直连暴露真实 IP 的影响；APNs 固定使用代理，代理失效时不会回落直连。
- 在目标设备和真实网络上验证 IPv4、IPv6、DNS 与 WebRTC/STUN。
- 审核任何额外模块、脚本、证书、描述文件或网络扩展。
- 在发布或再分发前确认第三方许可证和来源。
- 不将私人凭据上传到公开仓库、候选 ZIP 或托管 CI。

使用、修改、发布或再分发本项目所产生的风险由使用者自行评估和承担。

## 14. 合规、更正与移除请求

如果你是相关内容的权利人，认为本仓库遗漏署名、违反许可证、错误描述来源或应移除某项内容，请联系维护者并尽可能提供：

- 涉及的文件和具体规则或片段。
- 原始来源 URL、提交和权利证明。
- 适用许可证、版权或数据库权利声明。
- 希望采取的补充署名、修改、替换或移除方式。

联系方式：[@shenjlngbIng](https://t.me/shenjlngbIng)

维护者应在核实后采取适当措施，包括补充来源、恢复通知、修正描述、替换规则或移除存在问题的内容。

## 15. 再分发时应保留的材料

复制或再分发仓库内容时，至少应保留：

- 本 `NOTICE.md`。
- 适用的项目级 `LICENSE`，如果未来添加。
- `THIRD_PARTY_LICENSES/` 中与所分发内容相关的许可证。
- 文件头中的作者、来源、生成信息和修改说明。
- 固定提交和直接上游 URL。
- 对本地修改的清晰说明。

保留 NOTICE 不能代替履行许可证义务，也不能为未经授权的内容自动产生授权。只分发部分文件时，仍应携带与该部分相关的所有许可证和归属材料。
