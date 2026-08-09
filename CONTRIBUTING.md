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
2. 运行 `python3 tools/convert_to_remote_rules.py`，确认主配置只引用外部规则集。
3. 运行 `python3 tools/embed_runtime_rules.py` 刷新元数据；该历史文件名不会嵌入规则内容。
4. 执行全部审计、打包和测试。
5. 重新生成 `RELEASE_MANIFEST.txt`、`SHA256SUMS.txt` 和 `SHA256SUMS_fixed.txt`。
6. 检查差异和敏感信息。
7. 在提交说明中描述行为变化及验证结果。

## 必须通过的命令

```bash
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/test_audit_config.py
python3 tools/test_stage_surge_zip.py
python3 tools/package_release.py --output ../Surge-R12-release.zip
sha256sum -c SHA256SUMS.txt
```
