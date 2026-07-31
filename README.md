Surge iOS Stable Fail-Closed R10.5

一套面向 Surge iOS 5.14.6 及以上版本 的公开、可审计、失败关闭型配置方案。

本项目强调确定性、安全边界和运行时可控性。仓库中的公开文件不包含任何真实代理节点、订阅地址、访问令牌、账户密码、设备证书或其他私密凭据，可用于公开审阅、规则维护和配置审计。

本仓库提供的是配置框架、规则快照和审计工具。使用前，仍需将配置中的订阅占位地址替换为你自己的有效地址。

⸻

项目目标

本项目主要解决以下问题：

* 为 Surge iOS 提供一份可直接导入的稳定配置基线。
* 对未知流量采用失败关闭策略，避免异常流量在规则失效时直接放行。
* 将运行规则固化到主配置中，降低设备运行时对远程规则源的依赖。
* 对 Telegram、APNs、DNS 和默认流量出口进行明确控制。
* 通过自动化脚本检查配置结构、规则数量和锁文件状态。
* 保持公开仓库中不出现任何用户私密信息。

该配置适合希望对 Surge 流量路径进行精细控制，并且愿意在每次修改后执行审计流程的用户。

⸻

当前基线

当前版本基线为 R10.5。

项目	当前设置
主配置文件	Surge.conf
Surge 版本要求	Surge iOS 5.14.6+
有效规则数量	5546
DNS	AliDNS DoH + DNSPod DoH
DNS 容灾	国内明文 DNS
未知流量处理	FINAL,Final,dns-failed
Telegram	始终进入代理策略
APNs	已捕获的精确规则直连
规则来源	仓库内 Rules/ 本地快照
运行时远程规则	不使用 RULE-SET
配置审计	Python 自动化脚本
规则锁定	Rules/r10.lock.json

⸻

核心设计

1. 失败关闭

配置使用以下最终规则：

FINAL,Final,dns-failed

其设计目的不是简单地为未匹配流量选择一个默认出口，而是将未知流量统一交给 Final 策略，并启用 dns-failed 行为。

这意味着：

* 已知流量按照前置规则执行。
* 未被现有规则覆盖的流量不会被无条件直连。
* DNS 解析失败的连接不会轻易绕过既定策略。
* 新出现的域名、应用流量或异常请求需要经过明确策略判断。

失败关闭并不代表绝对安全，但相比默认直连，更适合强调流量边界和配置确定性的使用场景。

⸻

2. 运行时不依赖 RULE-SET

仓库维护规则快照，但设备运行时不直接加载远程 RULE-SET。

规则通过以下脚本嵌入主配置：

python tools/embed_runtime_rules.py

这样做的主要原因包括：

* 避免远程规则源临时不可用导致配置行为变化。
* 避免上游规则未经审核自动进入设备。
* 避免规则更新后实际运行内容与仓库审计结果不一致。
* 让 Surge.conf 成为设备最终运行内容的明确载体。
* 便于通过规则数量和锁文件检测意外变更。

Rules/ 目录仍作为规则维护源和可审计快照存在，但不是设备运行期间的动态依赖。

⸻

3. Telegram 强制代理

Telegram 相关流量始终进入代理策略。

这一设计用于避免 Telegram 流量因为：

* DNS 结果变化；
* IP 地址变化；
* 域名规则缺失；
* 默认规则命中；
* 网络环境切换；

而意外进入直连路径。

修改 Telegram 规则前，应确认域名、IP 和策略引用均未破坏其强制代理约束。

⸻

4. APNs 精确直连

Apple Push Notification service 相关流量通过已捕获的精确规则直连。

采用精确规则而不是大范围 Apple 域名直连，可以减少以下风险：

* 将无关 Apple 服务一并放行；
* 过宽域名后缀影响其他策略；
* 因 Apple 服务范围变化导致规则边界扩大。

调整 APNs 规则时，应优先添加经过实际观察和验证的精确目标，避免使用过于宽泛的匹配条件。

⸻

5. DNS 设计

默认使用以下国内 DoH 服务：

* AliDNS DoH
* DNSPod DoH

同时保留国内明文 DNS 作为容灾路径。

该设计兼顾：

* 日常解析过程的加密传输；
* 国内网络环境下的解析延迟；
* DoH 服务临时不可用时的基础解析能力；
* 配置在移动网络和 Wi-Fi 网络之间切换时的可用性。

需要注意，明文 DNS 仅作为容灾手段存在。实际隐私性、抗污染能力和可用性仍取决于所在网络环境。

⸻

仓库结构

仓库中的核心文件预计如下：

.
├── Surge.conf
├── Rules/
│   ├── ...
│   └── r10.lock.json
├── tools/
│   ├── audit_config.py
│   ├── audit_rules.py
│   ├── embed_runtime_rules.py
│   └── test_audit_config.py
└── README.md

Surge.conf

设备最终导入和运行的 Surge 主配置。

其中包含：

* DNS 设置；
* 代理策略组；
* 订阅占位配置；
* 域名与 IP 规则；
* Telegram 策略；
* APNs 精确规则；
* 最终失败关闭规则。

Rules/

经过维护和审计的本地规则快照。

设备运行时不会远程加载这些文件。规则修改后，需要通过嵌入脚本重新生成或更新 Surge.conf 中的运行规则。

Rules/r10.lock.json

规则基线锁文件，用于记录和校验当前版本的规则状态。

该文件应与当前规则快照和嵌入结果保持一致。除非规则发生有意修改，否则不应手动更新锁文件来绕过审计错误。

tools/audit_config.py

检查 Surge 主配置的关键约束，例如：

* 必要配置项是否存在；
* 默认规则是否符合预期；
* 敏感占位项是否正确；
* 禁止项是否被意外引入；
* 关键策略是否仍然存在。

tools/audit_rules.py

检查规则快照及其统计状态，例如：

* 规则文件是否完整；
* 规则数量是否符合基线；
* 锁文件是否匹配；
* 是否存在非预期变更。

tools/test_audit_config.py

执行审计工具自身的测试，避免审计脚本修改后产生静默失效。

tools/embed_runtime_rules.py

将 Rules/ 中维护的规则内容嵌入 Surge.conf，生成设备实际使用的运行规则。

⸻

快速使用

1. 获取 Raw 配置地址

https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf

可以在 Surge 中通过 URL 下载或导入该配置。

⸻

2. 替换订阅占位地址

导入配置后，找到 AllServer 中的占位 policy-path，将其替换为你自己的 Sub-Store 订阅转换地址。

示意：

AllServer = external, policy-path=你的订阅转换地址

请勿将以下内容提交到公开仓库：

* 真实订阅 URL；
* Sub-Store 私有接口；
* Token；
* 用户名和密码；
* 节点信息；
* 设备证书；
* 私有域名；
* 可识别个人身份的配置。

建议在本地维护包含真实订阅信息的私有副本，不要直接修改并推送公开版本。

⸻

3. 保持规则模式

导入配置后，Surge 应保持在规则模式下运行。

不要在未评估影响的情况下切换为：

* 全局直连；
* 全局代理；
* 其他会绕过规则链的运行模式。

本项目的失败关闭、Telegram 强制代理和 APNs 精确直连设计，均依赖规则模式正确执行。

⸻

4. 不加载未经审计的 Module

不要直接加载来源不明或未经审阅的 Surge Module。

Module 可能修改：

* DNS；
* Host；
* URL Rewrite；
* MITM；
* Script；
* Header；
* Rule；
* 策略组行为。

即使 Module 看起来只提供去广告或解锁功能，也可能改变本配置的失败关闭边界。

如确需使用 Module，应先检查其完整内容，并确认其不会：

* 插入宽泛直连规则；
* 覆盖 DNS 设置；
* 修改最终规则；
* 改写 Telegram 流量；
* 扩大 MITM 范围；
* 引入远程脚本依赖；
* 包含未经固定版本的远程资源。

⸻

本地审计

运行环境需要安装 Python 3。

在仓库根目录执行：

python tools/audit_config.py
python tools/audit_rules.py
python tools/test_audit_config.py

也可以在类 Unix 环境中使用：

python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/test_audit_config.py

全部命令通过后，才应认为当前配置满足仓库定义的基础约束。

⸻

配置修改流程

任何影响规则、策略、DNS 或默认出口的修改，都建议遵循以下流程。

第一步：修改规则源或配置

根据需要修改：

* Rules/ 中的规则快照；
* Surge.conf 中非自动嵌入部分；
* 审计脚本；
* 相关测试。

不要同时修改多个无关部分，否则会增加审计和回滚难度。

⸻

第二步：重新嵌入运行规则

如果规则发生有意修改，执行：

python tools/embed_runtime_rules.py

该步骤会将规则源重新写入设备运行配置。

未执行该步骤时，可能出现以下不一致：

* Rules/ 已更新；
* Surge.conf 仍包含旧规则；
* 审计结果与设备实际行为不一致。

⸻

第三步：执行完整审计

python tools/audit_config.py
python tools/audit_rules.py
python tools/test_audit_config.py

不要只执行其中一个脚本。

配置审计、规则审计和测试分别覆盖不同风险，不能互相替代。

⸻

第四步：检查差异

提交前检查 Git 差异：

git diff -- Surge.conf Rules/ tools/

重点确认：

* 规则数量变化是否符合预期；
* FINAL,Final,dns-failed 是否仍然存在；
* Telegram 是否仍然强制进入代理策略；
* APNs 是否仍然使用精确直连规则；
* 是否意外新增 RULE-SET；
* 是否意外加入真实订阅信息；
* 是否出现 Token、密码或证书内容；
* DNS 设置是否发生非预期变化。

⸻

第五步：提交锁文件

规则发生有意修改并通过全部审计后，提交更新后的：

Rules/r10.lock.json

锁文件应与规则变更一同提交。

不建议单独提交锁文件，也不应仅通过更新锁文件来压制审计失败。

⸻

推荐维护顺序

推荐使用以下完整命令序列：

python tools/embed_runtime_rules.py
python tools/audit_config.py
python tools/audit_rules.py
python tools/test_audit_config.py
git diff --check
git diff -- Surge.conf Rules/ tools/

如使用 Python 3 命令：

python3 tools/embed_runtime_rules.py
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/test_audit_config.py
git diff --check
git diff -- Surge.conf Rules/ tools/

⸻

安全边界

本仓库主动避免存储以下内容：

* 真实代理服务器；
* 节点域名和 IP；
* 代理端口；
* 订阅 URL；
* Sub-Store Token；
* API Token；
* 用户名和密码；
* 私钥；
* CA 证书；
* 客户端证书；
* 设备唯一标识；
* 私有网络地址；
* 可用于识别个人或设备的信息。

提交前可以额外执行关键词检查：

git grep -nEi 'token|password|passwd|secret|authorization|private.key|BEGIN CERTIFICATE'

该命令不能替代人工审阅，但可用于发现部分明显泄漏。

⸻

常见问题

为什么不直接使用远程 RULE-SET？

远程规则使用方便，但会引入运行时外部依赖。

远程内容可能因为以下原因发生变化：

* 上游仓库更新；
* 文件被覆盖；
* CDN 缓存变化；
* 链接失效；
* 维护者账户异常；
* 内容未经本仓库审核。

本项目选择将已审核规则嵌入主配置，以提高运行行为的确定性。

⸻

为什么未知流量不默认直连？

默认直连会让所有未识别流量绕过代理和规则约束。

在应用更新、域名变化或规则遗漏时，这种行为可能导致：

* 流量泄漏；
* 策略绕过；
* 地区限制异常；
* 隐私边界失效；
* 调试困难。

因此，本项目将未知流量交给明确的 Final 策略处理。

⸻

为什么还保留明文 DNS？

明文 DNS 仅作为容灾选项。

当 DoH 服务不可达、网络环境限制加密 DNS，或者系统处于特殊网络认证阶段时，完全不保留明文 DNS 可能导致所有域名解析失败。

是否保留该容灾路径，应根据自己的威胁模型和网络环境决定。

⸻

可以直接导入后使用吗？

可以导入配置框架，但不能在不修改的情况下获得可用代理节点。

你至少需要：

1. 配置自己的 Sub-Store 订阅转换地址；
2. 检查策略组是否正确加载节点；
3. 确认 Surge 处于规则模式；
4. 不加载未经审计的 Module；
5. 测试 DNS、Telegram、APNs 和未知流量路径。

⸻

可以添加自己的规则吗？

可以，但应遵循以下原则：

* 优先添加精确规则；
* 避免过宽的 DOMAIN-SUFFIX；
* 谨慎添加大范围 IP 段；
* 明确规则顺序；
* 修改后重新嵌入运行规则；
* 执行全部审计；
* 更新锁文件；
* 检查实际设备日志。

⸻

审计通过是否代表配置绝对安全？

不代表。

自动审计只能验证脚本中已经定义的约束，无法覆盖：

* Surge 自身实现缺陷；
* 操作系统网络行为；
* 上游 DNS 服务问题；
* 代理节点运营风险；
* 订阅服务泄漏；
* 用户自行加载的 Module；
* 本地证书和 MITM 设置；
* 未被审计规则覆盖的新型流量。

审计结果应理解为“当前配置符合仓库预设约束”，而不是完整安全证明。

⸻

更新前检查清单

每次发布新版本前，建议确认：

* Surge.conf 可以被 Surge 正常解析。
* 当前有效规则数量与预期一致。
* Rules/r10.lock.json 与规则快照一致。
* 未引入运行时 RULE-SET。
* FINAL,Final,dns-failed 未被修改。
* Telegram 仍然进入代理策略。
* APNs 精确规则仍然直连。
* DNS 主路径和容灾路径符合预期。
* 所有审计脚本执行成功。
* 审计测试执行成功。
* 仓库中不存在真实订阅 URL。
* 仓库中不存在 Token、密码或证书。
* Git 差异中没有无关格式变化。
* 已在实际设备上完成基础连通性测试。

⸻

设备验证建议

完成配置导入后，建议至少测试以下场景：

1. Wi-Fi 网络下的普通网页访问；
2. 蜂窝网络下的普通网页访问；
3. Wi-Fi 与蜂窝网络切换；
4. Telegram 登录、消息和媒体连接；
5. APNs 推送接收；
6. DoH 正常工作时的 DNS 解析；
7. DoH 不可用时的 DNS 容灾；
8. 未被规则覆盖的测试域名；
9. 代理节点全部不可用时的失败行为；
10. Surge 重启和配置重载后的策略状态。

验证时应结合 Surge 请求日志确认实际命中规则，而不是只根据“能否打开网页”判断配置是否正确。

⸻

贡献原则

提交规则或配置修改时，建议说明：

* 修改目的；
* 涉及的流量类型；
* 新增或删除的规则数量；
* 是否影响 DNS；
* 是否影响 Telegram；
* 是否影响 APNs；
* 是否影响最终策略；
* 审计命令输出；
* 实际设备验证结果。

请勿在 Issue、Pull Request、提交记录或日志截图中暴露：

* 订阅地址；
* 节点地址；
* Token；
* 证书；
* 设备标识；
* 私有域名；
* 个人网络信息。

⸻

免责声明

本项目仅提供 Surge 配置结构、规则快照和自动审计工具，不提供代理节点或网络服务。

使用者需要自行确认：

* 所在地区的法律法规；
* Surge 软件许可要求；
* 代理服务的可信度；
* DNS 服务的隐私政策；
* 订阅源的安全性；
* 配置是否适合自身网络环境。

因使用、修改或部署本配置产生的网络中断、数据泄漏、账户风险或其他损失，应由使用者自行评估和承担。