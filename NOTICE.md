# NOTICE、来源、许可证与本地修改

更新日期：2026-07-20

本文件记录 Surge iOS Stable Fail-Closed R10.1 的直接来源、第三方内容、本地筛选和已知元数据缺口。R10.1 继续使用 R10 固定的规则快照与许可边界。本文件不替代任何上游许可证，也不构成法律意见。

## 1. 本项目内容

以下部分属于本项目为当前仓库编写或重写的维护逻辑：

- R10 的策略闭环、规则顺序、DNS/UDP/IPv6/系统接管边界。
- APNs 规则在 Apple/Domestic 白名单之前固定进入代理的组织方式。
- `tools/` 中的配置审计、规则审计、生成和 ZIP 暂存逻辑。
- `.github/workflows/`、README、CHANGELOG 与本 NOTICE 的当前组织和说明。

本项目原创的组织或脚本不改变第三方规则内容原有的权利归属。

## 2. R10 固定快照

R10 不在设备运行时下载规则。`Surge.conf` 将 26 个本地源文件固定内嵌：

- 22 个代理或拒绝源文件，原始 4637 条，按配置原顺序删除 154 条不可达重复条件后内嵌 4483 条。
- 4 个 Apple/国内直连源文件，清洗后内嵌 1048 条。

本地来源基线：

```text
repository: shenjlngbIng/-
commit: 541641b64bf57ba83ccb9df6c59bd15b447ac265
```

`Rules/r10.lock.json` 固定每个运行时源文件的 SHA-256、原始有效项、内嵌项、角色及目标策略。固定提交和哈希只用于可复现性与变更审计，不表示本项目取得或拥有上游内容的版权。

## 3. R10 当前启用文件

### 3.1 广告与代理服务

| 类别 | 文件 | R10 策略 |
| --- | --- | --- |
| 广告补充 | `Ads_Custom_Extra.list` | `AdBlock` |
| AI | `ChatGPT.list`、`Claude.list`、`Gemini.list` | 同名服务组 |
| 视频/音乐 | `YouTube.list`、`Netflix.list`、`Disney.list`、`HBO.list`、`PrimeVideo.list`、`Emby.list`、`TikTok.list`、`Bahamut.list`、`BiliBiliIntl.list`、`Spotify.list`、`ProxyMedia.list` | 对应代理组 |
| 社交 | `Telegram.list`、`Twitter.list` | `Telegram`、`X` |
| 开发/平台 | `Github.list`、`Google.list`、`OneDrive.list`、`Microsoft.list` | 对应代理组 |
| 游戏 | `Game.list` | `Games` |

这些源文件只能生成代理或拒绝规则，不能获得 `Apple`、`Domestic` 或内置 `DIRECT`。

### 3.2 Apple 与国内直连源

| 文件 | 原始项 | R10 内嵌 | 本地修改 |
| --- | ---: | ---: | --- |
| `AppleCN.list` | 166 | 166 | 保留域名规则；APNs 更早固定代理 |
| `WeChat.list` | 33 | 30 | 删除 2 条宽泛 `USER-AGENT`、1 条 `IP-ASN` |
| `Direct.list` | 23 | 5 | 仅保留 4 个腾讯域名和 `goodnotesapp.com.cn` |
| `ChinaDomain.list` | 867 | 847 | 删除 3 条 `USER-AGENT`、13 条 DNS 服务域名和 4 条重复项 |

Google、`api.goodnotescloud.com`、`fileball.app`、`pianyuan.org` 不再由 `Direct.list` 获得直连。

## 4. Coldvvater/Mononoke 与 Gist 配置

- 参考配置：<https://gist.github.com/Coldvvater/8093bc6be4340b5324b4a343493becfe>
- 相关项目：<https://github.com/Coldvvater/Mononoke>
- 当前仓库直接快照关系：`Rules/ChinaDomain.list`
- 已记录历史来源：

```text
https://cdn.jsdelivr.net/gh/Coldvvater/Mononoke@e8bee09b64c2f6baaa3056ed8de61c74cec56a98/Surge/Rules/ChinaDomain.list
```

当前核对未确认该项目根目录的统一许可证。相关内容不能标记为本项目独立原创；公开复制或再分发前应重新核对上游声明并取得必要授权。

R10 对 `ChinaDomain.list` 进行安全筛选后内嵌，不在设备上请求该 URL。

## 5. SukkaW/Surge

- 项目：<https://github.com/SukkaW/Surge>
- 规则服务：<https://ruleset.skk.moe/>
- 仓库许可：上游声明的 AGPL-3.0 及具体文件单独声明。
- 本仓库相关文件：`Rules/Ads_Custom_Extra.list`。

`Ads_Custom_Extra.list` 是历史输入与本项目移动端补充整理后的自定义规则集合，不应表述为 SukkaW 官方 `reject_extra` 全量文件。

本地处理可能包含格式筛选、拆分、去重和 Surge iOS 适配。AGPL-3.0 文本保存在：

```text
THIRD_PARTY_LICENSES/SukkaW-AGPL-3.0.txt
```

官方许可证：<https://www.gnu.org/licenses/agpl-3.0.html>

## 6. blackmatrix7/ios_rule_script

- 项目：<https://github.com/blackmatrix7/ios_rule_script>
- 上游许可：GNU GPL v2；仍应以具体目录和文件声明为准。
- 本地 19 个服务快照的固定上游提交：`c00517ce10760a93728b241923a451dfa617be80`。
- 直接路径、Git Blob、SHA-256、排除项和合并参数记录于 `Rules/upstreams.lock.json`。

本地更新流程会：

- 保留既有本地规则并与固定上游精确去重。
- 过滤 Surge iOS 不执行的 `PROCESS-NAME`。
- 不导入未经单独审核的新增宽泛 `IP-ASN`。
- 排除不能唯一归属某服务的共享分析、身份、同意管理或公共云规则。
- 为运行时 IP/ASN 规则要求 `no-resolve`。

R10 进一步按原服务优先级删除跨文件的精确重复条件；先出现的专用服务策略保持优先，后续不可达重复项不再写入 `Surge.conf`。

GPL v2 文本保存在：

```text
THIRD_PARTY_LICENSES/blackmatrix7-GPL-2.0.txt
```

官方许可证：<https://www.gnu.org/licenses/old-licenses/gpl-2.0.html>

## 7. Apple 与 Telegram 网络标识

配置和规则中包含公开域名、IP 网段、ASN 或端口。相关服务标识用于网络匹配，不表示本项目拥有相关服务、数据库、商标或接口。

参考资料包括：

- Apple APNs 网络说明：<https://support.apple.com/zh-cn/102266>
- Apple 企业网络服务说明：<https://support.apple.com/zh-cn/101555>
- Telegram 官方 CIDR：<https://core.telegram.org/resources/cidr.txt>

这些资料和当前快照都可能变化。R10 保留的 APNs 规则是本次审计选择，不应视为 Apple 或 Telegram 对通知送达的保证。

## 8. 已移除的未加载快照

R10.1 已移除以下不在 `r10.lock.json`、不进入 `Surge.conf`、也不被运行时引用的历史快照：

- `Ads_SukkaW_Domain.list`
- `Doubao.list`
- `NetEaseMusic.list`
- `ProxyGFW.list`
- `Reject.list`
- `bilibili.list`

删除这些文件不会改变 `Surge.conf` 的 5599 条运行规则。仓库现在只保留 `r10.lock.json` 固定的 26 个规则源文件，减少无效体积和来源元数据缺口。

## 9. 来源元数据缺口

部分 `Rules/*.list` 文件只有名称、更新时间或数量，没有足够证据证明：

- 文件完全由本仓库原创。
- 文件只来自单一上游。
- 文件名等于原作者或原项目。
- 格式转换自动消除原许可证义务。
- 已取得所有再分发授权。

维护者为每个新增或更新文件至少应记录：原始项目、直接文件 URL、提交或获取日期、版权与许可证、本地删改、是否运行时启用及其策略影响。

## 10. 仅供比较与设计参考

以下项目用于理解 Surge 语法、规则组织和社区惯例。除本 NOTICE 已明确声明直接关系的文件外，不据此宣称 R10 复制其内容：

- DivineEngine/Profiles：<https://github.com/DivineEngine/Profiles/tree/master>
- DivineEngine Surge 规则系统：<https://divineengine.net/article/surge-rule-system/>
- GeQ1an/Rules：<https://github.com/GeQ1an/Rules/tree/master>
- NobyDa/ND-AD：<https://github.com/NobyDa/ND-AD>
- Rabbit-Spec/Surge：<https://github.com/Rabbit-Spec/Surge>
- SukkaW/Surge：<https://github.com/SukkaW/Surge>

若未来直接引入这些项目的文件，必须单独记录具体文件、固定版本、许可证和本地修改，不能只引用本节作为授权依据。

## 11. 分发要求

公开分发本仓库或其规则衍生物时：

1. 保留本 NOTICE、上游文件头和 `THIRD_PARTY_LICENSES/`。
2. 不删除第三方作者、来源、许可证或修改说明。
3. 不把聚合、筛选或格式转换后的规则全部标记为本项目原创。
4. 遵守 AGPL-3.0、GPL-2.0 和具体上游文件适用的其他条款。
5. 来源或许可不确定时，停止扩大分发并联系权利人。

本 NOTICE 与有效上游许可证冲突时，以适用法律和有效许可证为准。
