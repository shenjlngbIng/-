# Surge iOS Stable Fail-Closed R10.6

本次更新修正 Telegram 与 iOS APNs 推送稳定性，并保持失败关闭设计。

## 核心行为

- Telegram 域名、IPv4 与 IPv6 规则始终进入 `Telegram` 代理策略。
- `include-apns = false`，系统 APNs 不由 Surge VIF 强制接管。
- 保留 APNs 精确 `DIRECT` 规则作为已捕获连接的兜底。
- 未匹配流量最终进入 `FINAL,Final,dns-failed`。
- 运行时不使用远程 `RULE-SET`。

## 需要上传

保持压缩包内目录结构，将所有文件覆盖到仓库根目录：

- `Surge.conf`
- `Rules/r10.lock.json`
- `tools/audit_config.py`
- `tools/audit_rules.py`
- `tools/test_audit_config.py`
- `README.md`

## 校验

```bash
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/test_audit_config.py
```
