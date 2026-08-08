"""
测试专用配置：pytest 使用，全部数据落在 SQLite 内存库，绝不触碰真实 MySQL。

复用主 settings.py 的全部配置，仅覆盖以下项：
1. DATABASES：从 MySQL 改为 SQLite（:memory:），测试数据不入真实库
2. PASSWORD_HASHERS：改用 MD5 加速测试
3. 外部 API Key：置空兜底，防止测试期间误触发真实请求与计费
"""
import os

from .settings import *  # noqa: F401,F403

# 测试数据库：默认 SQLite 内存库，可通过环境变量指定文件库
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('FUNCHINESE_TEST_DB', ':memory:'),
    }
}

# 加速测试：MD5 哈希替代 PBKDF2（仅测试环境使用，生产绝不使用）
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# 兜底置空外部 API Key，防止测试期间误触发真实请求与计费
DASHSCOPE_API_KEY = ''
DEEPSEEK_API_KEY = ''
UNSPLASH_ACCESS_KEY = ''
