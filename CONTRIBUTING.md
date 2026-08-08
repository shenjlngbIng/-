# 贡献指南

## 基本要求

- 不提交真实订阅、节点、Token、密码或证书。
- 不引入未经固定版本的远程脚本或运行时 `RULE-SET`。
- 不为 Telegram 增加 `DIRECT` 路径。
- 不把全部 Apple 流量改为代理；APNs 只进入 `ApplePush` Fallback。
- DNS 必须保持加密出站，禁止恢复 `system` 上游或明文直连绕过。
- 不把 `Final` 改为默认直连。
- 不删除规则快照、许可证或审计工具。

## 修改流程

1. 修改配置或规则源。
2. 运行 `python3 tools/embed_runtime_rules.py`。
3. 执行全部审计和测试。
4. 重新生成 `SHA256SUMS.txt`。
5. 检查差异和敏感信息。
6. 在提交说明中描述行为变化及验证结果。

## 必须通过的命令

```bash
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/test_audit_config.py
python3 tools/test_stage_surge_zip.py
sha256sum -c SHA256SUMS.txt
```
