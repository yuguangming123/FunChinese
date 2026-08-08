# 测试先行流程（Test-First）

FunChinese 项目为**新功能**编写时的推荐流程，尤其适用于报名/进度等业务逻辑。

## 流程

1. **拆需求**：主智能体把功能需求拆成可测试的单元。
2. **委派 django-tester 写失败测试**：先按预期行为编写测试（会失败——功能未实现）。
3. **验收测试设计**：主智能体审查测试是否真正断言了预期行为，而非空壳。
4. **委派 django-coder 实现**：下发契约时附上失败测试作为"期望行为定义"。
5. **跑到全绿**：django-tester 运行 `python -m pytest` 至通过；主智能体验收。
6. **委派 django-reviewer 审查**：只读审查实现代码与测试质量（五维 + 密钥排查）。

## 适用场景

- **报名/进度链路**（当前缺口）：
  - `practiceApp/views.py` 的 `complete_session` 完成练习后，应更新 `UserLessonProgress`（is_completed/score/attempt_count）并聚合回写 `UserCourseEnrollment.progress`
  - `UserCourseEnrollment`/`UserLessonProgress` 已建表但无业务引用——测试先行最合适
- 新的 AJAX 端点、新的模型方法、新的业务规则

## 测试硬性要求

- 走 `funchinese.settings_test`（SQLite 内存库），不连真实 MySQL
- 外部 API（DeepSeek/TTS/SOE/Unsplash）必须 mock
- 触碰 DB 的测试用 `pytest.mark.django_db` 或请求 `db` fixture

## 循环反馈

- 测试失败 → 主智能体判断是测试错还是实现错，反馈给对应子智能体
- 测试通过但实现丑陋 → 委派 django-refactor（行为不变）
