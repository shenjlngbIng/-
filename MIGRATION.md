# R10.5 一次性升级说明

## 上传方式

将本包 `UPLOAD/` 目录中的全部内容复制到仓库根目录，保持目录层级并覆盖同名文件。

必须覆盖：

- `Surge.conf`
- `README.md`
- `CHANGELOG.md`
- `NOTICE.md`
- `MIGRATION.md`
- `Rules/r10.lock.json`
- `tools/` 下四个 Python 文件
- `.github/workflows/audit.yml`

不要删除现有 `Rules/*.list`、`THIRD_PARTY_LICENSES/`、`.gitignore`。上传后在 GitHub Actions 中确认三个步骤全部通过。
