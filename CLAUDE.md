# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## 项目简介

**FunChinese（趣学汉语）** —— 中文学习平台，基于 Django 6.0 构建。

## 常用命令

### 开发服务器
```bash
python manage.py runserver
```
> `manage.py` 默认以 `--noreload`（单进程）模式启动 runserver。

### 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
```

### 创建超级用户
```bash
python manage.py createsuperuser
```

### 测试
```bash
pytest                        # 使用 pytest（首选）
pytest courseApp/tests/       # 单个 app 测试
python manage.py test         # Django test runner（备选）
```
> 页面/UI 验证：默认只做代码审查与 pytest 回归，**不启用 mcp playwright 浏览器验证**；除非用户明确要求使用 playwright。

### Django 管理命令
```bash
python manage.py dbshell              # 数据库交互界面
python manage.py shell                # Django shell
python manage.py collectstatic        # 收集静态文件
python manage.py check                # 检查项目完整性
```

### 环境
- Python 3.13.12，虚拟环境 `.venv/`
- 包管理器：`pip`（无 requirements.txt）
- 数据库：MySQL 5.7+（`127.0.0.1:3306`, 库名 `FunChinese`）

---

## 项目架构

### 目录结构
```
FunChinese/
├── funchinese/                    # Django 项目配置
│   ├── settings.py                #  含 DeepSeek / Unsplash / 阿里云 / 腾讯云 配置
│   └── urls.py                    #  根路由 + 4 个自定义 admin AJAX 端点
├── homeApp/                       # 首页应用
├── courseApp/                     # 核心：课程 + 习题 + 后台管理
│   ├── models.py                  #  8 个模型（CourseCategory → Course → Chapter → Lesson → LearningContent / Exercise）
│   ├── admin.py                   #  深度定制：逐词分析内联表格 + 自动分词/配图按钮 + 自定义词库选择
│   ├── admin_views.py             #  4 个 AJAX 端点（auto_analyze, auto_image, upload_dict, list_dicts）
│   ├── utils.py                   #  jieba 分词（支持自定义词库）、DeepSeek API、Unsplash 配图搜索
│   └── templates/                 #  course.html, course_detail.html
├── textbookApp/                   # 教材同步（占位）
├── vocabularyAPP/                 # 词汇仓库（占位）
├── userApp/                       # 用户系统（UserInfo 继承 AbstractUser）
│   └── models.py                  #  telephone, nickname, headimg 字段
├── practiceApp/                   # 练习功能（4 种模式 + TTS + 口语评测）
│   ├── models.py                  #  PracticeSession, PracticeRecord
│   ├── views.py                   #  practice / start_session / submit_answer / tts / evaluate_speech
│   └── templates/                 #  listening|speaking|typing|translate_mode.html
├── templates/                     # 全局模板
│   ├── main-base.html             #  基础布局（Bootstrap 5 Flex）
│   ├── main-navtop.html           #  顶部导航栏
│   ├── main-navslider.html        #  左侧手风琴菜单
│   ├── main-header.html           #  Logo 区（未启用）
│   └── main-footer.html           #  页脚
├── static/
│   ├── css/                       #  自定义样式
│   ├── js/                        #  jquery-3.3.1.min.js, voice_player.js
│   ├── img/
│   ├── dicts/                     #  自定义分词词库（.txt 文件）
│   └── plugins/                   #  第三方插件
│       ├── bootstrap-5.3.2/       #  Bootstrap 5.3.2（主站与练习页统一使用）
│       ├── font-awesome-7pro/     #  FontAwesome 7 Pro（主站与练习页统一使用）
│       ├── sweetalert/            #  弹窗组件
│       ├── layDate-v5.0.9/        #  日期选择器
│       ├── canvasjs/              #  图表库（主站）
│       ├── spectrum-visualizer/   #  频谱可视化（练习页）
│       └── xlsTableFilter/        #  表格筛选
├── manage.py                      #  自定义：runserver 默认 --noreload
└── media/                         #  用户上传文件
```

### 数据模型层级（courseApp）
```
CourseCategory（树形，parent 自关联）
  └── Course（分类、难度、价格、教师）
        └── Chapter（同一 course 内 sort_order 唯一）
              └── Lesson（同一 chapter 内 sort_order 唯一）
                    ├── LearningContent（JSONField，8 种类型）
                    └── Exercise（sentences JSON + word_analysis JSON + image + audio）
```

### 练习功能架构（practiceApp）
```
PracticeSession（关联课时 + 练习模式 + 状态 + 得分）
  └── PracticeRecord（单题答题记录）
```

API 端点：`start_session/` / `submit_answer/` / `complete_session/` / `tts/` / `evaluate_speech/`

四种练习模式共享同一套题目数据（`exercises_by_mode_json`），前端各自独立 JS 管理答题状态。

---

## 后台管理系统（django-simpleui + 深度定制）

### 通用配置
- 主题：`element.css`，离线模式（`SIMPLEUI_STATIC_OFFLINE = True`）
- 站点标题：`趣学汉语后台管理`

### Exercise 练习题编辑页（核心功能）
| 功能 | 说明 |
|------|------|
| **三段式表单** | `chinese` / `pinyin` / `english` 自动合并为 JSON 存入 `sentences` |
| **自动分词** | 点击按钮 → DeepSeek AI 分析 → 自动填充逐词分析表格 + 语法提示 + 配图关键词 |
| **自定义词库** | 选择 .txt 词库文件 → jieba 优先匹配自定义词语 |
| **上传词库** | 浏览器上传 .txt 文件到 `static/dicts/` |
| **逐词分析编辑** | 可视化表格内联编辑（word / pinyin / english / pos / grammar） |
| **自动配图** | 基于关键词搜索 Unsplash → 下载保存到 `exercise.image` |
| **新建 + 自动配图** | 新建习题模式下可一次性创建习题并配图 |

### 后端 AJAX 端点
| 路径 | 功能 |
|------|------|
| `/admin/courseApp/exercise/auto_analyze/` | DeepSeek 逐词分析 + 语法提示 + 配图关键词 |
| `/admin/courseApp/exercise/auto_image/` | Unsplash 搜索配图并保存 |
| `/admin/courseApp/exercise/upload_dict/` | 上传自定义词库文件 |
| `/admin/courseApp/exercise/list_dicts/` | 返回词库列表（刷新用） |

---

## AI 与云服务

### 阿里云百炼（DashScope）
- TTS 语音合成，配置在 `settings.py` 中
- 模型：`qwen3-tts-flash`（默认）/ `qwen3-tts-instruct-flash`（支持情绪）
- API Key / Base URL 配置项

### 腾讯云智聆（SOE）
- 口语评测（录音评分），配置在 `settings.py` 中
- 无凭证时自动降级为本地模拟评分

### DeepSeek（AI 分词/分析）
- 用于后台逐词分析、语法提示、配图关键词生成
- 配置：`DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`

### Unsplash（配图搜索）
- 用于后台自动配图
- 配置：`UNSPLASH_ACCESS_KEY`

---

## 编码约定

- **视图**：Function-Based Views (FBV)，无 Class-Based Views
- **API**：`django.http.JsonResponse` 手动序列化，无 DRF
- **模板**：Django Template Language (DTL)，无 Jinja2 或其他引擎
- **前端框架（现有）**：Bootstrap 5.3.2 + jQuery 3.3.1 + FontAwesome 7 Pro（主站与练习页统一使用）
- **前端框架（后续开发）**：Bootstrap + **Vue.js 3.x** + FontAwesome（不再使用 jQuery 操作 DOM）
- **频谱可视化**：主站 `canvasjs`；练习页 `spectrum-visualizer` + `voice_player.js`（`AudioContext + Canvas`）
- **前端构建**：现有页面无构建工具；后续 Vue 项目配合 **Vite**
- **侧边栏**：激活状态通过 `{{ active_menu }}`、`{{ collapse_menu }}` 模板变量控制
- **类型注解**：Python 建议加类型提示，JS 无 TypeScript
- **URL 命名空间**：每个 app 通过 `app_name` 定义
- **模板前缀**：全局模板使用 `main-` 前缀（如 `main-base.html`）

### model verbose_name 约定
- 所有模型使用 `verbose_name` / `verbose_name_plural` 定义中文显示名
- 外键字段使用 `related_name` 指定反向查询名
- 使用 `sort_order` 字段控制排序
- `unique_together` 约束同一层级内的排序唯一性

---

## 已安装的关键依赖

| 包 | 用途 |
|----|------|
| Django 6.0.7 | Web 框架 |
| django-simpleui | 后台管理皮肤 |
| mysqlclient | MySQL 驱动 |
| jieba | 中文分词（自定义词库） |
| dashscope | 阿里云百炼 SDK（TTS） |
| tencentcloud-sdk-python-soe | 腾讯云智聆口语评测 |
| requests | HTTP 请求 |
| Pillow | 图片处理 |
| pytest | 测试框架 |
| playwright | 浏览器自动化测试 |
| easyocr / pytesseract | OCR 文字识别 |
| PyMuPDF / pdfminer.six / pdf2image | PDF 处理 |
| python-docx / python-pptx | Office 文档处理 |
| torch / torchvision | 深度学习框架 |
| librosa | 音频分析 |
| modelscope | 模型库 |

> **技术栈规范**：完整的版本约束和使用约定详见 [tech-stack.md](./tech-stack.md)。
> **依赖明细**：虚拟环境中每个 pip 包的功能和引用位置详见 [dependencies.md](./dependencies.md)。
