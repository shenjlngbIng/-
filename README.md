# Surge

个人 Surge 配置。主配置基于 Coldvvater 的公开 Gist 整理，规则文件来自
`Coldvvater/Mononoke`，迁移时保留了来源说明。

## 使用方法

1. 下载 `Surge.conf`。
2. 在本地将 `YOUR_SUBSCRIPTION_URL` 替换成自己的机场订阅地址。
3. 导入 Surge。

不要把包含令牌的私人订阅地址提交到公开仓库。

配置发布后可使用下面的 Raw 地址：

```text
https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf
```

## 目录

- `Surge.conf`：主配置。
- `Rules/`：主配置引用的规则文件。
- `NOTICE.md`：上游来源和归属说明。

## 上游更新

规则文件是迁移时的快照，不会自动与上游仓库同步。需要更新时，应先比较上游
规则差异，再更新本仓库并保留归属说明。
