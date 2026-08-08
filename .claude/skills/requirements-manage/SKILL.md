---
name: requirements-manage
description: 安全维护 requirements.txt 依赖清单。当需要新增/升级/删除 Python 依赖并同步清单时使用。该文件为 UTF-16 编码，直接用普通文本工具写入会损坏；当前清单与实际安装不一致，修改前先核对。
---

# requirements.txt 依赖清单维护规范（FunChinese）

## 何时使用
安装/升级/卸载 Python 包后需同步清单，或核对依赖与文档一致性时。

## 标准流程
1. **安装/卸载**：用 `.venv/Scripts/python.exe -m pip install <pkg>==<ver>` 或 `uninstall`
2. **核对实际安装**：`.venv/Scripts/python.exe -m pip list`（列出 dist-info 为准）
3. **更新清单**：用 Python 以 `encoding='utf-16'` 读写（保留 BOM），**不要**用普通文本编辑器或 `pip freeze > requirements.txt`

## 编码警示（关键！）
- **`requirements.txt` 是 UTF-16-LE with BOM 编码**（非 UTF-8！）
- 直接 `pip freeze > requirements.txt` 会写成 UTF-8，破坏编码导致乱码
- 正确更新方式：
  ```python
  # 在 Django shell 或任意 Python 中
  from pathlib import Path
  p = Path('requirements.txt')
  lines = p.read_text(encoding='utf-16').splitlines()
  # ...修改 lines...
  p.write_text('\n'.join(lines) + '\n', encoding='utf-16')
  ```
- PowerShell 可用 `Out-File -Encoding unicode`

## Gotchas（本项目现状）
- **清单与安装不一致**：清单写 `django-simpleui`，但实际后台用 `django-unfold 0.102.0`（清单缺 unfold）；清单也缺 `pytest`/`pytest-django`（现已安装）。修改清单时应一并修正。
- **不要写入按需本地包**：torch/torchvision/easyocr 等 CLAUDE.md 声称已装的包实际**未安装**（文档理想化），不要误写入清单。
- **真实驱动是 PyMySQL**：`django.db.backends.mysql` + `funchinese/__init__.py` 中 `pymysql.install_as_MySQLdb()`，不是 mysqlclient。
- 核对版本以 `.venv/Lib/site-packages/*.dist-info` 为准，CLAUDE.md/dependencies.md 可能滞后。
