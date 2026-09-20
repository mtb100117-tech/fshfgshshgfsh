import os
import requests
import zipfile
import shutil
from pathlib import Path
from ..utils.config import CONTENT_DIR
from ..utils.logger import logger


class Updater:
    """Модуль обновления приложения и контента."""

    FALLBACK_HOSTS = ("https://ya.ru", "https://www.google.com")

    def __init__(self, base_url: str = None):
        self.base_url = base_url or "https://example.com/update"
        logger.debug(f"Updater инициализирован с URL: {self.base_url}")

    def check_internet_available(self) -> bool:
        """Проверяет доступность интернета.

        Сначала — хост обновлений (если это не заглушка), затем нейтральные.
        """
        candidates = []
        base = (self.base_url or "").strip()
        if base and "example.com" not in base:
            candidates.append(base)
        candidates.extend(self.FALLBACK_HOSTS)

        for url in candidates:
            try:
                response = requests.head(url, timeout=3, allow_redirects=True)
                if response.status_code < 500:
                    logger.info(f"Интернет доступен (проверено через {url})")
                    return True
            except Exception as e:
                logger.debug(f"Проверка {url} не удалась: {e}")
                continue

        logger.warning("Интернет недоступен (все проверки провалились)")
        return False

    def check_for_updates(self) -> dict:
        try:
            url = f"{self.base_url}/version.json"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Получена информация об обновлениях: {data}")
                return data
            return None
        except Exception as e:
            logger.error(f"Ошибка проверки обновлений: {e}", exc_info=True)
            return None

    def download_and_install_content(self, progress_callback=None) -> bool:
        try:
            url = f"{self.base_url}/content.zip"
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code != 200:
                return False

            total = int(response.headers.get('content-length', 0))
            downloaded = 0

            temp_file = CONTENT_DIR.parent / 'temp_content.zip'
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total > 0:
                            progress_callback(int(downloaded / total * 90))

            if CONTENT_DIR.exists():
                shutil.rmtree(CONTENT_DIR)
            CONTENT_DIR.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                zip_ref.extractall(CONTENT_DIR)

            temp_file.unlink()

            if progress_callback:
                progress_callback(100)

            logger.info("Контент успешно обновлён")
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления контента: {e}", exc_info=True)
            return False

    def download_and_install_app(self, progress_callback=None) -> bool:
        logger.warning("Обновление приложения не реализовано")
        if progress_callback:
            progress_callback(100)
        return False