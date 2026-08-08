---
name: django-migrate
description: 在 FunChinese 项目中创建、应用、检查数据库迁移。当新增或修改 models.py 后需要生成迁移、执行迁移、解决迁移冲突或回滚迁移时使用。涵盖 MySQL 正式库与 SQLite 测试库的差异处理。
---

# Django 迁移操作规范（FunChinese）

## 何时使用
新增/修改了 `models.py` 中的模型字段、外键、约束之后。

## 标准流程
1. **修改模型**：在对应 app 的 `models.py` 中改好字段，遵循 `verbose_name`/`related_name`/`sort_order` 约定
2. **生成迁移**：`python manage.py makemigrations <app_name>`（指定 app 避免误生成）
   - 先 `python manage.py makemigrations --dry-run --verbosity 3` 预览
3. **审查迁移文件**：读取生成的 `app/migrations/00XX_*.py`，确认字段增删符合预期
4. **应用迁移**：`python manage.py migrate`（针对真实 MySQL 库）
5. **核对**：`python manage.py showmigrations` 确认该迁移标记为 `[X]`

## Gotchas（本项目常见坑）
- **测试库自动建**：pytest 的 SQLite 测试库由 pytest-django 自动迁移建表，`migrate` 只针对真实 MySQL 库。跑测试不需要先 migrate。
- **makemigrations 不需要数据库连接**：即使 MySQL 未启动也能生成迁移文件。
- **中文元数据不产生迁移**：修改 `verbose_name`/`verbose_name_plural`/`help_text` 这类纯展示字段，`makemigrations` 不会生成新迁移。
- **迁移文件先 review 再应用**：不要盲目 `migrate`，先看生成的迁移内容。
- **不在迁移里写业务逻辑**：迁移只描述数据结构变化；数据清洗用 `RunPython` 时需谨慎并在迁移中注释说明。
- **迁移冲突**：多分支同时改模型产生冲突时，先 `makemigrations --merge` 解决，不手动删迁移文件。
- **字段删除是破坏性操作**：删除字段/表前先确认没有生产数据依赖。
