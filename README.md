# Surge

个人 Surge 配置，基于 Coldvvater 的公开配置与 `Coldvvater/Mononoke` 规则整理，
并保留上游来源说明。

## 已做的优化

- 新增 `Auto` Smart Group，全局自动选择更合适的节点。
- 节点订阅每 24 小时刷新一次，并过滤流量、到期时间等非节点信息。
- DNS 同时使用当前网络 DNS 与公共 DNS；DoH 作为可选项保留。
- 使用当前 Surge 版本推荐的自动接管模式，默认关闭 Web 控制面板。
- 补全常见局域网、回环和保留地址的跳过范围。
- 将超大的广告域名规则转换为 `DOMAIN-SET`，减少匹配开销。

Smart Group 需要 Surge iOS 5.11.0 / Surge Mac 5.7.0 或更新版本。

## 使用方法

1. 下载 `Surge.conf`。
2. 在本地将 `YOUR_SUBSCRIPTION_URL` 替换成自己的机场订阅地址。
3. 导入 Surge。

不要把包含令牌的私人订阅地址提交到公开仓库。仓库中的模板应始终保留
`YOUR_SUBSCRIPTION_URL`。

主配置 Raw 地址：

```text
https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf
```

## 规则维护

`Rules/` 保存的是经过完整性检查的上游规则快照。需要更新时，应重新获取上游
规则，并再次生成 `Ads_SukkaW_Domain.list` 与 `Ads_SukkaW_Extra.list`。

## 目录

- `Surge.conf`：主配置模板。
- `Rules/`：配置引用的规则文件及上游广告规则快照。
- `NOTICE.md`：上游来源和归属说明。
