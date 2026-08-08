# FunChinese 技术栈

> 本文档定义了 **FunChinese（趣学汉语）** 项目采用的技术栈及其版本约定，与 [CLAUDE.md](./CLAUDE.md) 配合使用。
> CLAUDE.md 侧重**项目架构与操作指南**，本文档侧重**技术选型与使用规范**。

---

## 一、后端核心

| 技术 | 版本 | 说明 |
|------|------|------|
| **Python** | 3.13.12 | 运行时 |
| **Django** | 6.0.7 | Web 框架（**不**使用 Django REST Framework） |
| **MySQL** | 5.7+ | 数据库（`127.0.0.1:3306`, 库名 `FunChinese`） |
| **django-simpleui** | 2026.1.13 | 后台管理皮肤（主题 `element.css`，离线模式） |
| **mysqlclient** | 2.2.8 | MySQL 驱动 |

### 后端约束

- **视图模式**：统一使用 **Function-Based Views (FBV)**，不使用 Class-Based Views 或 Django REST Framework。
- **序列化**：自定义 API 端点通过 `django.http.JsonResponse` 手动序列化，不使用 DRF 序列化器。
- **ORM**：使用 Django ORM（`select_related` / `prefetch_related` 优化查询）。
- **模板**：Django Template Language (DTL)，不使用 Jinja2 或其他模板引擎。
- **表单**：使用 Django Forms（后台 `ModelForm`），前端无独立表单验证框架。
- **URL 命名空间**：每个 app 通过 `app_name` 定义，根路由通过 `include()` 引入。

---

## 二、前端技术

### 技术路线（分阶段）

> 已开发页面保持原有技术栈，**后续新开发页面统一转向 Vue.js 体系**。

### 已开发部分（保持现状）

| 技术 | 版本 | 说明 |
|------|------|------|
| **Bootstrap** | 5.0 | UI 框架（本地静态文件 + CDN） |
| **jQuery** | 3.3.1 | DOM 操作（所有自定义 JS 依赖） |
| **FontAwesome** | 7 Pro（主站）/ 5（练习页） | 图标库 |

### 后续开发转向

| 技术 | 版本 | 说明 |
|------|------|------|
| **Bootstrap** | 5.x | 继续使用，提供布局和组件样式 |
| **Vue.js** | 3.x | 替代 jQuery，采用 Options API / Composition API |
| **FontAwesome** | 保持现有 | 图标库继续使用 |
| **Vite** | 最新稳定版 | 推荐构建工具（仅在 Vue 项目中使用） |

### 前端约束

- 已开发页面：Bootstrap + jQuery + FontAwesome，**无前端框架**。
- 后续开发：Bootstrap + **Vue.js** + FontAwesome，**不再使用 jQuery 操作 DOM**。
- **不**使用 React / Svelte 等其他前端框架。
- Vue 项目建议配合 **Vite** 构建。
- 可选用 **Pinia** 管理全局状态、**Vue Router** 管理前端路由（若需要 SPA 子模块）。
- 不强制使用 TypeScript（Vue 项目可选 JS 或 TS）。
- **不**使用 CSS 预处理器（纯 CSS + Bootstrap 类）。

---

## 三、AI 与云服务

| 服务 | 用途 | 配置项（`settings.py`） |
|------|------|------------------------|
| **阿里云百炼 DashScope** | TTS 语音合成 | `DASHSCOPE_API_KEY`, `DASHSCOPE_BASE_URL` |
| | 模型：`qwen3-tts-flash`（默认） | `QWEN3_TTS_MODEL` |
| | 模型：`qwen3-tts-instruct-flash`（支持情绪） | `QWEN3_TTS_INSTRUCT_MODEL` |
| **腾讯云智聆 SOE** | 口语评测 | `TENCENT_SOE_SECRET_ID` / `_KEY` / `_APP_ID` |
| **DeepSeek** | AI 逐词分析 + 语法提示 + 配图关键词 | `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL` |
| **Unsplash** | 配图搜索下载 | `UNSPLASH_ACCESS_KEY` |

---

## 四、文档处理与 NLP

| 包 | 用途 | 状态 |
|----|------|------|
| **jieba** | 中文分词（支持自定义词库） | ✅ 核心使用 |
| **easyocr** | OCR 文字识别 | ⏸ 预留 |
| **pytesseract** | Tesseract OCR | ⏸ 预留 |
| **PyMuPDF (fitz)** | PDF 解析 | ⏸ 预留 |
| **pdfminer.six** | PDF 文本提取 | ⏸ 预留 |
| **pdf2image** | PDF → 图片 | ⏸ 预留 |
| **python-docx** | Word 读写 | ⏸ 预留 |
| **python-pptx** | PowerPoint 读写 | ⏸ 预留 |
| **opencv-python-headless** | 图像处理 | ⏸ 预留 |
| **Pillow** | 图片处理（PIL Fork） | ✅ 核心使用 |
| **pydub** | 音频处理 | ⏸ 预留 |

---

## 五、数据科学与机器学习

| 包 | 版本 | 用途 | 状态 |
|----|------|------|------|
| **torch** | 2.13.0+cpu | 深度学习框架 | ⏸ 预留 |
| **torchvision** | 0.27.0 | 视觉模型 | ⏸ 预留 |
| **modelscope** | 1.38.1 | ModelScope 模型库 | ⏸ 预留 |
| **librosa** | 0.11.0 | 音频分析 | ⏸ 预留 |
| **scipy** | 1.18.0 | 科学计算 | ⏸ 预留 |
| **numpy** | 2.4.6 | 数值计算 | ✅ 核心使用 |
| **pandas** | 3.0.5 | 数据分析 | ⏸ 预留 |

---

## 六、开发工具与测试

| 工具/包 | 说明 |
|---------|------|
| **pytest** | 测试框架（首选） |
| **playwright** | 浏览器自动化测试 |
| **pip** | 包管理器（**不**使用 uv / poetry） |
| **.venv/** | 虚拟环境（项目根目录） |

### 测试约定

- 测试文件位于各 app 的 `tests/` 目录下。
- 优先使用 `pytest` 而非 `python manage.py test`。

---

## 七、URL 路由模式

```
funchinese/urls.py（根路由）
  ├── homeApp               / → home
  ├── courseApp              /courseApp/course/  /courseApp/course/<id>/
  ├── textbookApp            /textbookApp/textbook/
  ├── vocabularyAPP          /vocabularyAPP/vocabulary/
  ├── practiceApp            /practiceApp/<lesson_id>/  /practiceApp/api/*
  ├── admin/                 django-simpleui 后台
  └── admin/courseApp/exercise/  auto_analyze, auto_image, upload_dict, list_dicts
```

---

## 八、架构约定总结

| 方面 | 约定 |
|------|------|
| **视图** | Function-Based Views (FBV)，**无** CBV |
| **API** | 自定义 `JsonResponse`，**无** DRF |
| **模板** | DTL，**无** Jinja2/其他引擎 |
| **前端（现有）** | Bootstrap + jQuery + FontAwesome |
| **前端（后续）** | Bootstrap + **Vue.js** + FontAwesome |
| **构建（现有）** | **无** 前端构建工具 |
| **构建（后续）** | Vue 项目配合 **Vite** |
| **类型** | Python 建议类型提示，JS 无 TypeScript |
| **ORM** | Django ORM |

---

## 九、与 CLAUDE.md 的关系

- **CLAUDE.md**：项目的"操作手册"——目录结构、数据模型、URL 路由、常用命令等日常开发信息。
- **tech-stack.md**：项目的"技术规范"——定义技术选型边界，约束"能用什么、不能用什么"。

修改任一时应检查另一个文件的一致性。
