#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'funchinese.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # runserver 默认以单进程模式启动（禁用 auto-reloader 的双进程机制）
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver' and '--noreload' not in sys.argv and '--skip-checks' not in sys.argv:
        sys.argv.append('--noreload')
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
