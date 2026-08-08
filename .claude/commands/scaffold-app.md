---
description: 委派 django-coder 按项目约定生成新 Django app 骨架（app_name 命名空间、tests/ 目录、unfold admin）
argument-hint: <app_name>
---

# 新建 Django App 骨架

委派 **django-coder** 子智能体执行以下任务契约：

## 任务标题
创建新 Django app「{app_name}」骨架。

## 背景
FunChinese 项目按以下约定组织 app。参照现有 app（如 `vocabularyAPP`/`textbookApp` 的占位结构）生成。

## 范围
1. 运行 `python manage.py startapp {app_name}` 生成骨架
2. 在 `funchinese/settings.py` 的 INSTALLED_APPS 中追加 `{app_name}`
3. 创建 `{app_name}/urls.py`，定义 `app_name = '{app_name}'`，预留一个占位视图路由
4. 建 `{app_name}/tests/__init__.py` 与 `{app_name}/tests/test_smoke.py`（一个最小导入冒烟测试）
5. 如涉及后台管理，`admin.py` 注册模型用 `unfold.admin.ModelAdmin`

## 禁止改动
- 不修改其他 app 的业务代码
- 不触碰 `funchinese/settings.py` 中的密钥/数据库配置

## 验收标准
- [ ] app 骨架可导入，`python manage.py check` 通过
- [ ] INSTALLED_APPS 已注册
- [ ] `app_name` 命名空间已定义
- [ ] 冒烟测试通过：`python -m pytest {app_name}/tests/ -q`

## 交付格式
- 创建的文件清单（绝对路径）
- `settings.py` 改动位置
- `python manage.py check` 与 pytest 结果
