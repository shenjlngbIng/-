# 上游来源说明

本仓库的 `Surge.conf` 基于以下配置整理：

- 原始配置作者：Coldvvater
- 原始配置：https://gist.github.com/Coldvvater/8093bc6be4340b5324b4a343493becfe
- 原始规则仓库：https://github.com/Coldvvater/Mononoke

`Rules/` 中的文件复制自 `Coldvvater/Mononoke` 的 `Surge/Rules/` 目录。
迁移时使用的上游提交为：

```text
9721a8b66c723f5c2434a5ca7304b2ad5896ad9f
```

本迁移保留原作者归属。仓库所有者表示已就使用事宜与原作者沟通；原始内容的
权利归其各自权利人所有。

为提高 Surge 对超大广告列表的匹配效率，`Ads_SukkaW.list` 会自动派生出
`Ads_SukkaW_Domain.list` 和 `Ads_SukkaW_Extra.list`。派生文件不改变规则归属。
