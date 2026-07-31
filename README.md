# Surge iOS Stable Fail-Closed R10.5

面向 **Surge iOS 5.14.6+** 的公开失败关闭配置。仓库运行文件不含真实节点、订阅 URL、Token、密码或设备证书。

## 当前基线

- 配置：`Surge.conf`
- 有效规则：5546
- DNS：AliDNS + DNSPod DoH；国内明文 DNS 用作容灾
- 未知流量：`FINAL,Final,dns-failed`
- Telegram：始终进入代理策略
- APNs：已捕获的精确规则直连
- 规则来源：本地 `Rules/` 快照；设备运行时不使用 `RULE-SET`

## 使用

Raw 地址：

```text
https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf
```

导入后必须保持规则模式，不加载未经审计的 Module。将 `AllServer` 的占位 `policy-path` 替换为自己的 Sub-Store 订阅转换地址。

## 自动审计

```bash
python tools/audit_config.py
python tools/audit_rules.py
python tools/test_audit_config.py
```

配置发生有意修改后，先运行：

```bash
python tools/embed_runtime_rules.py
```

随后重新执行全部审计并提交 `Rules/r10.lock.json`。
