import os
import sys
from pathlib import Path


def get_app_data_dir():
    """Возвращает путь к %LOCALAPPDATA%\AppName"""
    local_app_data = os.environ.get('LOCALAPPDATA')
    if not local_app_data:
        local_app_data = os.path.expanduser('~\\AppData\\Local')
    app_dir = Path(local_app_data) / 'AppName'
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_content_dir():
    """Папка content рядом с исполняемым файлом"""
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
    else:
        # Исправлено: было Path(file), стало Path(__file__)
        base = Path(__file__).parent.parent.parent  # app/utils/../../..
    content = base / 'content'
    content.mkdir(exist_ok=True)
    return content


DB_PATH = get_app_data_dir() / 'users.db'
LOG_PATH = get_app_data_dir() / 'app.log'
CONTENT_DIR = get_content_dir()
DEFAULT_PIN = "1234"
DEBOUNCE_MS = 200
MAX_PROFILES = 4