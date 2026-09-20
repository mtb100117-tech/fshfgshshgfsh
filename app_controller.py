import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from ..db.db_manager import DBManager
from ..models.user import User
from ..models.settings import Settings
from ..controllers.content_loader import ContentLoader
from ..controllers.audio_manager import AudioManager
from ..controllers.updater import Updater
from ..utils.logger import logger
from ..utils.config import CONTENT_DIR


class AppController(QObject):
    user_changed = pyqtSignal(object)
    pin_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.content = ContentLoader()
        self.audio = AudioManager()
        self.current_user: User = None
        self.settings = Settings(pin=self.db.get_pin())
        self.load_content()
        self.updater = Updater()

    def load_content(self):
        self.content.load_all_lessons()

    def get_users(self):
        return self.db.get_all_users()

    def create_user(self, name: str, avatar: str) -> User:
        user = self.db.create_user(name, avatar)
        self.set_current_user(user)
        return user

    def set_current_user(self, user: User):
        self.current_user = user
        user.last_login = datetime.now().isoformat()
        self.db.update_user(user)
        self.user_changed.emit(user)

    def delete_user(self, user_id: int):
        self.db.delete_user(user_id)
        if self.current_user and self.current_user.id == user_id:
            self.current_user = None
            self.user_changed.emit(None)

    def get_progress(self, lesson_id: str):
        if self.current_user:
            return self.db.get_progress(self.current_user.id, lesson_id)
        return None

    def set_progress(self, lesson_id: str, stars: int, completed: bool,
                     mistakes: int, time_spent: int):
        if self.current_user:
            self.db.set_progress(self.current_user.id, lesson_id, stars,
                                 completed, mistakes, time_spent)
            self.check_and_unlock_achievements(self.current_user.id)

    def get_user_stats(self, user_id: int):
        return self.db.get_user_stats(user_id)

    def get_pin(self):
        return self.db.get_pin()

    def set_pin(self, pin: str):
        self.db.set_pin(pin)
        self.settings.pin = pin
        self.pin_changed.emit(pin)

    def get_lessons(self, language: str):
        return self.content.lessons.get(language, [])

    def is_internet_enabled(self) -> bool:
        return self.db.get_internet_enabled()

    def set_internet_enabled(self, enabled: bool):
        self.db.set_internet_enabled(enabled)
        logger.info(f"Интернет {'включён' if enabled else 'выключен'}")

    def get_update_url(self) -> str:
        return self.db.get_update_url()

    def set_update_url(self, url: str):
        self.db.set_update_url(url)

    def get_content_dir(self) -> Path:
        return CONTENT_DIR

    def check_updates(self) -> dict:
        if not self.is_internet_enabled():
            logger.warning("Попытка проверки обновлений при выключенном интернете")
            return None
        return self.updater.check_for_updates()

    def update_content(self, progress_callback=None) -> bool:
        if not self.is_internet_enabled():
            logger.warning("Попытка обновления контента при выключенном интернете")
            return False
        return self.updater.download_and_install_content(progress_callback)

    def update_app(self, progress_callback=None) -> bool:
        if not self.is_internet_enabled():
            logger.warning("Попытка обновления приложения при выключенном интернете")
            return False
        return self.updater.download_and_install_app(progress_callback)

    def import_content_from_zip(self, zip_path: str, progress_callback=None) -> bool:
        try:
            content_dir = CONTENT_DIR
            if content_dir.exists():
                shutil.rmtree(content_dir)
            content_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if progress_callback:
                    progress_callback(10)
                zip_ref.extractall(content_dir)
                if progress_callback:
                    progress_callback(90)
            if progress_callback:
                progress_callback(100)
            logger.info(f"Контент успешно импортирован из {zip_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка импорта контента: {e}")
            return False

    def check_and_unlock_achievements(self, user_id: int):
        stats = self.get_user_stats(user_id)
        unlocked = self.db.get_achievements(user_id)

        achievements_def = {
            "first_lesson": stats['lessons_completed'] >= 1,
            "five_lessons": stats['lessons_completed'] >= 5,
            "ten_lessons": stats['lessons_completed'] >= 10,
            "no_mistakes": stats['total_mistakes'] == 0 and stats['lessons_completed'] >= 1,
        }

        for ach_id, condition in achievements_def.items():
            if condition and ach_id not in unlocked:
                self.db.unlock_achievement(user_id, ach_id)
                logger.info(f"Пользователь {user_id} получил достижение: {ach_id}")

    def cleanup(self):
        self.audio.cleanup()
        self.db.close()