---
name: run-tests
description: 运行 FunChinese 项目的 pytest 测试套件。当需要执行全部或单个 app 测试、确认某次改动未破坏既有功能、查看失败详情或统计覆盖率时使用。默认走 SQLite 测试库（funchinese.settings_test），不触碰真实 MySQL。
---

# pytest 测试运行规范（FunChinese）

## 何时使用
执行测试、查失败、确认改动无回归、统计覆盖率时。

## 常用命令
- 全量测试：`python -m pytest`
- 单 app：`python -m pytest courseApp/tests/ -q`
- 单测试：`python -m pytest courseApp/tests/test_smoke.py::test_lesson_chain_and_session_roundtrip -v`
- 关键字过滤 + 首个失败即停：`python -m pytest -k "enroll" -x -v`
- 详细失败回溯：`python -m pytest --tb=long`
- 覆盖率（需先装 pytest-cov）：`python -m pytest --cov=funchinese --cov-report=term-missing`

## Gotchas（本项目常见坑）
- **绝不 `python manage.py test` 连真实库**：测试统一走 pytest + `funchinese.settings_test`（SQLite 内存库）。Django 内置 `manage.py test` 会连真实 MySQL。
- **碰数据库的测试必须请求 `db` fixture** 或用 `pytest.mark.django_db`，否则报 `Database queries to 'default' are not allowed`。
- **外部 API 必须 mock**：DeepSeek/阿里 TTS/腾讯 SOE/Unsplash 真实调用会计费且慢。`conftest.py` 已全局屏蔽 `requests.get/post` 为抛错，测试内用 `monkeypatch` 覆盖具体函数。
- **settings_test 已置空 API key** 作为兜底，但依赖此兜底写测试是坏实践，仍应显式 mock。
- **models 导入即触发 settings 加载**：测试文件顶层 `from courseApp.models import ...` 没问题（pytest-django 已配置 settings），但不要在有数据库查询的顶层代码。
- **媒体/静态文件不影响测试**：`ImageField` 测试建议用 `SimpleUploadedFile` 或直接不赋值（字段多为 blank）。
- **JSONField**：`PracticeSession.exercise_snapshot`、`Exercise.word_analysis` 等是 JSONField，直接传 Python 对象即可。

## 验证边界
本 skill 仅负责 pytest 测试运行；页面/UI 的浏览器验证**默认不启用 mcp playwright**，除非用户明确要求使用。
