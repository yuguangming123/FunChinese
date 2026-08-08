# FunChinese 项目依赖清单

> 本文档记录项目虚拟环境（`.venv/`）中当前保留的全部 20 个 pip 包的功能、引用位置及其在本项目中的作用。
> 与 [tech-stack.md](./tech-stack.md) 和 [CLAUDE.md](./CLAUDE.md) 配合使用。
> 已将阿里云 TTS 从 `dashscope` SDK 改为直接 HTTP 调用，减少 22 个传递依赖。

---

## 一、直接依赖（项目代码中显式 import 或配置）

| # | pip 包名 | 版本 | 功能 | 项目中的作用 | 引用位置 |
|---|----------|------|------|-------------|---------|
| 1 | **Django** | 6.0.7 | Web 框架 | 项目核心框架，提供 ORM、模板、Admin、请求路由 | 所有 `models.py`、`views.py`、`admin.py`、`settings.py` |
| 2 | **django-simpleui** | 2026.1.13 | 后台管理皮肤 | 美化 Django Admin，主题 `element.css` | `settings.py:34` 的 `INSTALLED_APPS` |
| 3 | **PyMySQL** | 1.2.0 | MySQL 数据库驱动 | 替代 mysqlclient，连接 MySQL 数据库 | `funchinese/__init__.py:1`（`import pymysql` + `install_as_MySQLdb()`） |
| 4 | **jieba** | 0.42.1 | 中文分词库 | 练习题逐词分析中的中文分词，支持自定义词库 | `courseApp/utils.py:19` |
| 5 | **requests** | 2.34.2 | HTTP 请求库 | DeepSeek API、Unsplash 配图搜索下载、阿里云 TTS（直接 REST API） | `courseApp/utils.py:20`，`practiceApp/views.py:168` |
| 6 | **urllib3** | 2.7.0 | HTTP 底层库 | 抑制 SSL 不安全请求警告，requests 的底层依赖 | `courseApp/utils.py:25` |
| 7 | **tencentcloud-sdk-python-common** | 3.1.141 | 腾讯云 SDK 公共库 | 智聆口语评测的凭证和异常处理 | `practiceApp/views.py:273-274` |
| 8 | **tencentcloud-sdk-python-soe** | 3.0.1459 | 腾讯云智聆 SOE SDK | 口语评测（录音评分 API） | `practiceApp/views.py:275` |

---

## 二、运行时依赖（被一中的包在运行时加载，项目代码未直接 import）

| # | pip 包名 | 版本 | 功能 | 被谁依赖 | 引用位置 |
|---|----------|------|------|---------|---------|
| 9 | **asgiref** | 3.12.1 | ASGI 协议适配 | Django → | Django 6.0 的 WSGI/ASGI 处理 |
| 10 | **sqlparse** | 0.5.5 | SQL 格式化工具 | Django → | ORM SQL 语句格式化（debug/migrate） |
| 11 | **tzdata** | 2026.3 | IANA 时区数据 | Django → | 时区数据库（`TIME_ZONE = 'Asia/Shanghai'`） |
| 12 | **pytz** | 2026.2 | 时区库 | Django → | 时区感知时间和日期操作（`USE_TZ = True`） |
| 13 | **MarkupSafe** | 3.0.3 | HTML/XML 安全转义 | Django → | Django 模板引擎 `mark_safe` 底层转义 |
| 14 | **pillow** | 12.3.0 | 图片处理库 | Django → | `ImageField` 运行时必须，处理课程封面、习题配图、用户头像 |
| 15 | **certifi** | 2026.7.22 | SSL 证书包 | requests → | HTTPS 证书验证 |
| 16 | **charset-normalizer** | 3.4.9 | 字符编码检测 | requests → | HTTP 响应编码自动识别 |
| 17 | **idna** | 3.18 | 国际化域名解析 | requests → | 支持非 ASCII 域名 |

---

## 三、系统工具（pip 自带，非项目依赖）

| # | pip 包名 | 版本 | 功能 | 说明 |
|---|----------|------|------|------|
| 18 | **pip** | 26.1.2 | Python 包管理器 | 安装/管理依赖 |
| 19 | **setuptools** | 83.0.0 | 包构建工具 | 构建和安装包 |
| 20 | **wheel** | 0.47.0 | 包格式标准 | 加速包安装 |

---

## 四、按功能分类汇总

| 功能领域 | 涉及包 | 数量 |
|---------|--------|------|
| **Web 框架** | Django, asgiref, sqlparse, tzdata, pytz, MarkupSafe | 6 |
| **后台管理** | django-simpleui | 1 |
| **数据库** | PyMySQL | 1 |
| **中文分词** | jieba | 1 |
| **HTTP 通信** | requests, urllib3, certifi, charset-normalizer, idna | 5 |
| **阿里云 TTS** | requests（直接 REST API，替代 dashscope SDK） | 0 |
| **腾讯云口语评测** | tencentcloud-sdk-python-common, tencentcloud-sdk-python-soe | 2 |
| **图片处理** | pillow | 1 |
| **系统工具** | pip, setuptools, wheel | 3 |

---

## 五、优化记录

| 日期 | 优化内容 | 减少包数 |
|------|---------|---------|
| 2026-07-31 | 删除实验性大包（torch, librosa, gradio, scikit-learn 等） | 74 |
| 2026-07-31 | dashscope SDK → 直接 requests 调用 TTS REST API | 22 |
| **合计** | 从 123 个精简至 **20 个** | **-103** |

---

## 六、与 CLAUDE.md 的关系

- **CLAUDE.md**：项目架构和操作手册
- **tech-stack.md**：技术选型规范
- **dependencies.md**（本文档）：虚拟环境依赖明细

> **注意**：本文档仅记录 pip 包依赖。前端静态插件（Bootstrap、FontAwesome、jQuery、SweetAlert、CanvasJS、SpectrumVisualizer 等）位于 `static/plugins/`，不在此列。
