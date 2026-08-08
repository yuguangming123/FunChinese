---
description: 委派 django-tester 运行 pytest 全量测试并汇报结果（走 SQLite 测试库）
---

# 运行测试

委派 **django-tester** 子智能体执行以下任务契约：

## 任务标题
运行 FunChinese 全量 pytest 测试并汇报结果。

## 背景
项目已配置 pytest（`pytest.ini` 指向 `funchinese.settings_test`，SQLite 测试库）。测试文件在各 app 的 `tests/` 目录。

## 范围
1. 运行 `python -m pytest -q` 全量测试
2. 如有失败，提取失败用例、报错堆栈与根因
3. 汇报通过数/失败数/耗时

## 禁止改动
- 不修改任何测试文件或业务代码——本次只运行与汇报

## 交付格式
- 测试结果摘要（通过/失败/跳过数）
- 失败用例列表（如有）：文件:行号 + 报错摘要 + 初步根因判断
- 测试耗时
