"""
pytest 全局配置（FunChinese 项目）。

作用：
1. 兜底设置 DJANGO_SETTINGS_MODULE 指向 funchinese.settings_test（SQLite 测试库）
2. 提供全局防护：阻止测试误触发外部 API 真实调用（DeepSeek / TTS / Unsplash / SOE）
3. 提供常用 fixture：admin_user（超级用户）、mock_deepseek（DeepSeek 模拟）

注意：本文件在项目根目录，pytest 会自动加载（rootdir conftest）。
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'funchinese.settings_test')

import pytest  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402


@pytest.fixture(autouse=True)
def _guard_external_requests(monkeypatch):
    """全局兜底：屏蔽外部 API 真实调用。

    各测试按其场景在用例内 monkeypatch 具体函数；此处仅做通用防护，
    例如将 requests 库的网络请求替换为直接抛错，确保误用即失败而非真实外呼。
    """
    import requests

    def _no_network(*args, **kwargs):
        raise AssertionError('测试中禁止真实网络请求（外部 API 必须 mock）')

    monkeypatch.setattr(requests, 'get', _no_network)
    monkeypatch.setattr(requests, 'post', _no_network)
    monkeypatch.setattr(requests, 'put', _no_network)
    yield


@pytest.fixture
def admin_user(db):
    """创建一个可登录后台的超级用户，返回 UserInfo 实例。"""
    User = get_user_model()
    return User.objects.create_superuser(
        username='test_admin',
        password='test_pass_123',
        email='admin@example.com',
    )


@pytest.fixture
def mock_deepseek(monkeypatch):
    """模拟 DeepSeek API 返回，避免真实计费与网络延迟。

    用法：在测试内通过 monkeypatch.setattr 覆盖 courseApp.utils 中
    调用 DeepSeek 的具体函数；此 fixture 提供统一入口。
    """
    return monkeypatch
