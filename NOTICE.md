# 来源与本地修改

更新日期：2026-08-08

本仓库发布 Surge iOS Privacy + Push R12 配置及维护工具。`Surge.conf` 中的第三方规则版权归各自作者或项目所有，相关许可证副本位于 `THIRD_PARTY_LICENSES/`。

本仓库的原创维护内容包括：

- Surge 配置结构与策略组设计
- 失败关闭策略和规则顺序
- DNS 防绕过规则
- Telegram 与 APNs 路由方案
- 配置和规则审计脚本
- ZIP 安全暂存工具
- GitHub Actions 工作流
- 使用、安全和贡献文档
- 订阅导入兼容和策略组接入说明

主配置随仓库固定发布 Sub-Store `2.36.31` 的两份重写脚本，仅用于按官方接口处理 `sub.store` 请求；脚本版权和许可证归 Sub-Store 项目所有，来源、上游提交与许可证副本见 `Vendor/Sub-Store/README.md` 和 `THIRD_PARTY_LICENSES/Sub-Store-AGPL-3.0.txt`。主配置不再依赖 GitHub Release 的运行时跳转地址。

原创脚本、配置结构与文档采用仓库根目录 `LICENSE` 中的 MIT License。第三方规则、数据和材料继续遵循各自许可证；MIT License 不替代或覆盖第三方许可证。

公开仓库不得包含真实订阅地址、代理节点、Token、密码、Cookie、私钥或证书。`Rules/*.list`、`THIRD_PARTY_LICENSES/` 和维护工具属于审计链路，不应删除。
