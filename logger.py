import os
import sys
import logging
from pathlib import Path


def setup_logger():
    logger = logging.getLogger('AppLogger')
    logger.setLevel(logging.DEBUG)

    local_app_data = os.environ.get('LOCALAPPDATA')
    if not local_app_data:
        local_app_data = str(Path.home() / 'AppData' / 'Local')

    log_dir = Path(local_app_data) / 'AppName'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / 'app.log'

    fh = logging.FileHandler(log_path, encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger


logger = setup_logger()
logger.info("Логгер инициализирован")
