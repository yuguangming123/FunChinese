---
name: unfold-admin
description: 使用 django-unfold 0.102.0 定制 FunChinese 后台管理界面。当需要修改 admin 列表页、表单、内联表格、自定义按钮、站点配色，或处理后台 AJAX 端点（auto_analyze、auto_image 等）时使用。simpleui 已停用，勿再按 simpleui 文档编写。
---

# django-unfold 后台定制规范（FunChinese）

## 何时使用
修改 `admin.py`、后台 AJAX 端点、Unfold 主题配置、站点外观时。

## 核心要点
- Admin 类继承 `unfold.admin.ModelAdmin`（不是 Django 默认 `admin.ModelAdmin`，不是 simpleui 的）
- 内联表格用 `unfold.admin.TabularInline` / `unfold.admin.StackedInline`
- 现有最佳参考：`courseApp/admin.py`（Exercise 三段式表单、自动分词/配图按钮、自定义词库选择）
- 自定义 JS/CSS 通过 ModelAdmin 的 `class Media` 注入
- 后台 AJAX 端点放在 `admin_views.py`，参考 `courseApp/admin_views.py`（`@csrf_exempt` + is_staff 校验）
- Unfold 主题配置在 `settings.py` 的 `UNFOLD = {...}` 字典（当前**尚未配置**，需要配色/菜单/导航时新建）

## Gotchas（本项目常见坑）
- **simpleui 已停用**：`settings.py` L34 `'simpleui'` 已注释；L50-54 的 `SIMPLEUI_*` 配置是死配置，修改后台相关配置时可直接清理。
- **CLAUDE.md 文档滞后**：仍写着 django-simpleui，属历史文档未同步；改代码时顺带修正文档（委派 docs-writer）。
- **userApp/admin.py 设置站点标题**：`admin.site.site_header/site_title = "趣学汉语后台管理"`，改站点标题时看这里。
- **没有 `UNFOLD` 配置块**：要改主题配色、侧边栏菜单、顶部导航，先在 settings.py 加 `UNFOLD = {...}`（参考 django-unfold 官方文档）。
- **Exercise 编辑页有深度定制**：修改 admin 时不要破坏 `ExerciseAdminForm` 三段式表单与逐词分析内联表格。
- **后台 AJAX 端点都挂在 `/admin/courseApp/exercise/`**：见 `funchinese/urls.py`，8 个端点（auto_analyze/auto_image/upload_dict/list_dicts/extract_keywords/cleanup_images/save_image_url/upload_image）。
