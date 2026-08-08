---
name: chinese-content
description: 处理中文教学内容生成：jieba 分词、DeepSeek 逐词分析、Unsplash 配图搜索与缓存。当需要实现或修改自动分词、语法提示、配图关键词、自定义词库逻辑时使用。
---

# 中文教学内容生成规范（FunChinese）

## 何时使用
修改/实现自动分词、逐词分析、语法提示、配图关键词、自定义词库逻辑时。

## 现有实现（复用，不要重写）
- **核心实现**：`courseApp/utils.py`（约 854 行）——jieba 分词、DeepSeek API、Unsplash 配图搜索、自定义词库匹配
- **后台端点**：`courseApp/admin_views.py` 的 8 个 AJAX 端点（auto_analyze/auto_image/extract_keywords/upload_dict/list_dicts 等）
- **词库文件**：`static/dicts/` 下的 .txt 文件（jieba 优先匹配自定义词语）
- **数据结构**：`Exercise.word_analysis`（JSONField 逐词分析）、`Exercise.grammar_hint`（语法提示）、`Exercise.sentences`（chinese/pinyin/english 三段 JSON）

## Gotchas（本项目常见坑）
- **API key 一律从 `settings` 读取**（`DASHSCOPE_API_KEY`/`DEEPSEEK_API_KEY`/`UNSPLASH_ACCESS_KEY`），**禁止硬编码**到代码中
- **外部调用慢且收费**：测试必须 mock；`conftest.py` 已全局屏蔽真实网络请求
- **配图关键词有缓存逻辑**：历史提交修过"配图关键词缓存问题"，改动关键词生成逻辑时勿破坏缓存
- **`static/dicts/阿里云RAM.txt` 疑似含凭据内容**：处理词库目录时避免读取/上传该文件，不要将其内容写入任何输出
- **jieba 词典加载**：自定义词库需在分词前 `jieba.load_userdict(...)`，参考 `courseApp/utils.py` 的 `get_available_dicts`
- 逐词分析输出结构（word/pinyin/english/pos/grammar）与 `courseApp/admin.py` 的逐词分析内联表格字段保持一致
