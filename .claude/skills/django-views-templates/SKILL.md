---
name: django-views-templates
description: 按 FunChinese 项目规范编写视图、URL、AJAX 端点与 DTL 模板。当需要新增页面、视图函数、表单提交或前端交互时使用。硬性约定：FBV、JsonResponse 手动序列化、DTL、app_name 命名空间、模板 main- 前缀、中文注释。
---

# Django 视图与模板编写规范（FunChinese）

## 何时使用
新增/修改视图函数、URL 路由、DTL 模板、AJAX 端点、表单交互时。

## 硬性约定
- **视图用 FBV**（Function-Based Views），不用 CBV
- **API 用 `django.http.JsonResponse` 手动序列化**，不用 DRF；返回中文时设 `ensure_ascii=False`
- **模板用 DTL**，不用 Jinja2 或其他引擎
- **URL 用 `app_name` 命名空间**，每个 app 的 `urls.py` 定义 `app_name`
- **模板 `main-` 前缀**：全局模板在根 `templates/`（`main-base.html` 等）；app 模板放 `app/templates/app/`
- 注释用中文；POST 表单必须带 `{% csrf_token %}`

## 现有实现参考
- `homeApp/views.py` 的 `home`、`courseApp/views.py` 的 `course`/`course_detail`、`practiceApp/views.py` 的 6 个 FBV
- 侧边栏激活态通过模板变量 `{{ active_menu }}` / `{{ collapse_menu }}` 控制
- `funchinese/urls.py` 根路由 + 8 个 admin AJAX 端点

## Gotchas（本项目常见坑）
- **前端技术栈过渡**：现有页面 jQuery 3.3.1 + Bootstrap 5；**后续新页面转 Vue 3 + Vite，不再用 jQuery 操作 DOM**。新写前端交互前确认当前页面属于哪一代。
- **FontAwesome 版本**：主站用 FontAwesome 7 Pro，练习页用 FontAwesome 5——勿混用 CDN。
- **练习模式共享数据**：practiceApp 四种模式共享 `exercises_by_mode_json` 题目数据，前端各自管理答题状态。
- **TTS 接口**：阿里云百炼 `qwen3-tts-flash`（默认）/ `qwen3-tts-instruct-flash`（支持情绪），调用见 `practiceApp/views.py` 的 `tts`。
- **口语评测**：腾讯云智聆 SOE，无凭证时自动降级本地模拟评分，见 `evaluate_speech`。
- **模板上下文处理器**：`settings.py` 的 TEMPLATES 只注册了 request/auth/messages，**没有** i18n/media/static/tz 处理器；模板里用 `{{ MEDIA_URL }}` 等需自行传上下文。
- **STATICFILES_DIRS 写法非常规**：`STATICFILES_DIRS = BASE_DIR, 'static'`（元组），改动静态目录时注意实际效果。
