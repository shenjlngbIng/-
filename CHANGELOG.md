# Changelog

## 2026-07-18 · R6

- 将 19 个服务规则快照与 `blackmatrix7/ios_rule_script@c00517ce10760a93728b241923a451dfa617be80` 合并，过滤 iOS 不支持或归属过宽的规则，并把运行时内嵌项从 8115 条更新到 10796 条。
- 将广告补充规则准确重命名为 `Ads_Custom_Extra.list` / `RS_Ads_Custom_Extra`。
- 为配置指定的 `223.5.5.5` DoH 增加精确冷启动例外；其他 DoH、DoH3、DoQ 继续进入 `Proxy`。
- 增加四条精确 mDNS/SSDP 局域网发现例外，更宽的多播地址继续拒绝。
- 将服务分流置于通用 STUN、QUIC、UDP 兜底之前，并固定 YouTube/Google、Game/Microsoft 等重叠规则优先级。
- 新增上游锁文件、可复现更新脚本、生成漂移检查和 push/PR GitHub Actions 审计。
- 公开配置继续拒绝设备专用 Host、真实订阅、节点和凭据；这些信息只能保留在私有副本。
