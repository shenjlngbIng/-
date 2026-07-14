# Surge

个人 Surge 配置，基于 Coldvvater 的公开配置与 `Coldvvater/Mononoke` 规则整理，
并保留上游来源说明。

## 可用性设计

- `Proxy` 新安装默认使用 `Auto` Smart Group；另设 `Fallback`，按订阅顺序切换到首个可用节点。
- 节点订阅每 24 小时刷新一次；地区缩写使用字母边界，避免 `US` 误匹配 Australia/Russia、`TW` 误匹配 Network。
- DNS 使用系统、阿里与腾讯传统解析器引导，并配置阿里、腾讯、Cloudflare、Google DoH 冗余。
- IPv6 随当前网络自动启用，避免 IPv6-only 网络完全不可用。
- Apple 系统流量与 APNs 默认直连；ChatGPT Voice 的 UDP/3478 在通用 STUN 规则前匹配。
- UDP 不受节点支持时仍选择 `REJECT`，避免为了可用性静默改成 `DIRECT` 而泄漏真实出口。
- 默认关闭 Web 控制面板，并补全常见局域网、回环和保留地址的跳过范围。

配置中的 `block-quic` 要求 Surge iOS 5.14.6 / Surge Mac 5.10.3 或更新版本；
低于该版本请先升级 Surge。

## 使用方法

1. 下载 `Surge.conf`。
2. 在本地将 `你的订阅地址` 替换成自己的 Surge 格式订阅 URL（可由 Sub-Store 转换）。
3. 导入 Surge，并确认 `Proxy` 选中 `Auto`。旧配置升级时 Surge 可能保留原选择，需要手动切换一次。

不要把包含令牌的私人订阅地址提交到公开仓库。仓库中的模板应始终保留
`你的订阅地址`；未替换前模板没有可用代理节点，不能直接联网。

主配置 Raw 地址：

```text
https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf
```

## 规则维护

`Rules/` 保存的是经过完整性检查的上游规则快照。需要更新时，应重新获取上游
规则，并再次生成 `Ads_SukkaW_Domain.list` 与 `Ads_SukkaW_Extra.list`。
为降低误杀造成的“无网络”，超大的 `Ads_SukkaW_Domain.list` 当前仅保留快照、
不在主配置中启用；主配置只加载 `Ads_SukkaW_Extra.list` 与 `Reject.list`。

## 目录

- `Surge.conf`：主配置模板。
- `Rules/`：配置引用的规则文件及上游广告规则快照。
- `NOTICE.md`：上游来源和归属说明。
