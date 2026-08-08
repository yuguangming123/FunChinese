# Django 迁移安全流程（Migration Safety）

FunChinese 项目修改数据模型的固定流程。适用于：新增字段、改字段类型、加外键、删除字段、加约束。

## 流程

1. **基线确认**：`git status` 确认工作区状态，`git log --oneline -3` 了解最近改动。
2. **修改模型**：在 `models.py` 完成字段修改，遵循 `verbose_name`/`related_name`/`sort_order` 约定。
3. **生成迁移**：
   - 预览：`python manage.py makemigrations --dry-run --verbosity 3`
   - 生成：`python manage.py makemigrations <app_name>`（指定 app，避免误生成其他 app 迁移）
4. **审查迁移文件**：读取 `app/migrations/00XX_*.py`，逐条确认字段增删/约束符合预期。
5. **应用迁移**：`python manage.py migrate`（作用于真实 MySQL 库）。
6. **核对**：`python manage.py showmigrations` 确认该迁移标记 `[X]`。
7. **回归验证**：`python -m pytest` 全量测试（SQLite 测试库自动建表，不影响真实库）。

## 安全规则

- **makemigrations 不需要数据库连接**；MySQL 未启动也能生成。
- **迁移文件先 review 再应用**，不盲目 migrate。
- **删除字段是破坏性操作**：确认无生产数据依赖后再删。
- **不在迁移中写业务逻辑**：数据清洗用 `RunPython` 时须谨慎并加中文注释。
- **迁移冲突**：多分支并发改模型导致冲突时用 `makemigrations --merge`，不手动删迁移文件。
- **纯展示字段**（verbose_name/help_text）改动不产生迁移，属正常现象。

## 委派建议

- 模型修改 + 迁移生成：委派 `django-coder`
- 迁移文件审查：委派 `django-reviewer`（只读）
- 迁移后回归测试：委派 `django-tester`
