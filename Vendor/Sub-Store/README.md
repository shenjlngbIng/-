# Sub-Store runtime scripts

这两个文件固定来自 Sub-Store `2.36.31` 的官方 `release` 分支，用于主配置中的 `sub.store` 请求重写。

- `sub-store-0.min.js`：Simple 重写脚本
- `sub-store-1.min.js`：Core 重写脚本
- 来源：[sub-store-org/Sub-Store](https://github.com/sub-store-org/Sub-Store)
- 上游提交：`b43580e93e3ca2171d62ab17d1806afdc5fadd01`
- 许可证：见 [`THIRD_PARTY_LICENSES/Sub-Store-AGPL-3.0.txt`](../../THIRD_PARTY_LICENSES/Sub-Store-AGPL-3.0.txt)

主配置通过固定提交的 jsDelivr 地址加载脚本；本目录副本用于审计、校验和离线打包，不再依赖 GitHub Release 的跳转地址。
