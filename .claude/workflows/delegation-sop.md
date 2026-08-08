# 委派—验收标准作业流程（Delegation SOP）

FunChinese 项目所有编程任务的协作基准流程。主智能体（orchestrator）按此流程运行。

## 一、任务契约模板

委派时整段放入子智能体 prompt（替换 `{...}` 占位）：

```markdown
你是子智能体「{role}」，在独立上下文内完成以下任务契约。完成后只返回交付摘要，不返回完整 diff。

## 任务标题
{一句话}

## 背景
{必要上下文：相关文件绝对路径、现有实现说明、需求来源/期望行为。注意子智能体看不到此前对话，背景必须自带。}

## 范围（必须完成）
1. {具体事项}
2. {具体事项}

## 禁止改动
- {白名单外文件一律不允许修改：如 funchinese/settings.py 的密钥、media/、requirements.txt}
（白名单外一律不允许修改）

## 编码约束（硬性）
- 视图用 FBV，不用 CBV；API 用 django.http.JsonResponse，不用 DRF
- 模板用 DTL，不用 Jinja2；URL 用 app_name 命名空间
- 注释与提交信息用中文；模型用 verbose_name/related_name/sort_order 约定
- 密钥严禁写入代码、日志、提交（含 DEBUG 输出）
- 用户模型是 userApp.UserInfo；测试一律用 SQLite 测试库（funchinese.settings_test），不连真实 MySQL

## 前置与依赖
{如：先读 CLAUDE.md；先 python manage.py makemigrations --dry-run；先 git status 确认基线}

## 验收标准（DoD，全部满足才算完成）
- [ ] 功能满足需求
- [ ] 只改了白名单内文件
- [ ] 符合全部编码约束
- [ ] 相关 pytest 通过（python -m pytest {路径} -x）
- [ ] 无密钥/密码泄露
- [ ] 未破坏相邻功能（回归）

## 测试要求
{必须执行的验证命令}

## 交付格式（返回给主智能体）
1. 改动文件清单（绝对路径 + 一句话改动说明）
2. 关键实现点（≤200 字）
3. 测试/验证结果（命令 + 输出摘要）
4. 遗留风险或未完成项
5. DoD 逐项勾选结果
```

## 二、角色选择

| 任务类型 | 子智能体 | 说明 |
|---|---|---|
| 新增/修改功能 | `django-coder` | 写代码 |
| 重构（行为不变） | `django-refactor` | worktree 隔离 |
| 写/修测试 | `django-tester` | 写测试 |
| 调试 Bug | `django-debugger` | 先复现再修复 |
| 只读审查/验收 | `django-reviewer` | 绝不写 |
| 探索/调研 | `django-explorer` | 只读，成本低 |
| 文档/注释 | `docs-writer` | 写文档 |

## 三、执行流程

1. **分析**：主智能体拆解需求 → 定范围 → 选角色 → 写契约。
2. **委派**：通过子智能体调用，契约整体作为 prompt 下发。
3. **执行**：子智能体独立上下文执行，只返回交付摘要。
4. **验收**：主智能体对照 DoD——`git diff --stat` 核对改动范围、`git diff` 抽查、跑 pytest、必要时再委派 django-reviewer 只读审查。
5. **决策**：通过 → 记录，主智能体提交（**提交永远由主智能体执行，子智能体不提交**）；不通过 → 给出失败点，携带失败点重新委派同角色。
6. **循环**：复杂任务拆成多个串行契约，每份契约对应一个原子交付。

## 四、失败反馈原则

- 措辞具体到「文件:行号 + 期望 vs 实际」，不要只说"不合格"
- 示例：「`practiceApp/views.py:206` 期望 complete_session 回写 UserLessonProgress，实际只更新了 session.status，请补齐」
- 一次只聚焦本轮失败点，避免一次反馈过多让子智能体无从下手
