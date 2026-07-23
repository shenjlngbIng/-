# R10.1 仓库升级说明

## 是否需要删除旧文件

不需要删除任何已跟踪文件。本升级包已经同步更新 R10.1 配置、文档、工具和工作流，并保留规则来源与许可证。

本地如果出现 `tools/__pycache__/`，可以删除；它已在 `.gitignore` 中忽略，不应上传到 GitHub。

## 推荐升级方式

### 使用 Git

1. 解压本包。
2. 将解压目录中的内容复制到仓库根目录，保持 `.github/`、`Rules/`、`tools/` 和 `THIRD_PARTY_LICENSES/` 的层级。
3. 检查差异后提交并推送。
4. 等待 `Audit Surge R10.1 profile` 工作流全部通过。

### 使用 GitHub 网页

上传时必须保持目录结构。不要只上传 `Surge.conf` 后留下 R7 审计器，否则 Actions 会按旧版约束报错。

需要新增的文件：

```text
Rules/r10.lock.json
MIGRATION.md
```

需要替换的主要文件：

```text
Surge.conf
README.md
CHANGELOG.md
NOTICE.md
.github/workflows/audit.yml
.github/workflows/unpack.yml
tools/audit_config.py
tools/audit_rules.py
tools/embed_runtime_rules.py
tools/test_audit_config.py
tools/stage_surge_zip.py
tools/test_stage_surge_zip.py
```

其余 `Rules/*.list`、`Rules/upstreams.lock.json`、第三方许可证和 `tools/update_service_rules.py` 继续保留。

## 上传后检查

仓库根目录应直接看到 `Surge.conf`，而不是额外嵌套一层升级包目录。

配置 Raw 地址保持：

```text
https://raw.githubusercontent.com/shenjlngbIng/-/main/Surge.conf
```

在 GitHub Actions 中确认以下检查通过：

- R10/R10.1 规则锁和 32 个本地规则文件检查。
- R10.1 内嵌规则可复现检查。
- 策略闭环与配置检查。
- 20 项安全变异回归测试。
- ZIP 暂存路径回归测试。

公开仓库不要加入真实节点、订阅 URL、Token、密码或设备证书。
