import sqlite3
from typing import List, Optional, Dict
from ..models.user import User
from ..models.settings import Settings
from ..models.lesson import Lesson, LessonItem
from ..models.phrase import Phrase
from ..utils.config import DB_PATH
import json
from datetime import datetime
from ..utils.logger import logger


class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH))
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                avatar TEXT,
                created_at TEXT,
                last_login TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                user_id INTEGER,
                lesson_id TEXT,
                stars INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                mistakes INTEGER DEFAULT 0,
                time_spent INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, lesson_id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS phrases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                language TEXT NOT NULL,
                text TEXT NOT NULL,
                translation TEXT NOT NULL,
                audio_path TEXT,
                image_path TEXT,
                created_at TEXT,
                last_practiced TEXT,
                practice_count INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                user_id INTEGER,
                achievement_id TEXT,
                unlocked_at TEXT,
                PRIMARY KEY (user_id, achievement_id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('pin', '1234')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('internet_enabled', '0')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('update_url', 'https://example.com/update')")
        self.conn.commit()

    def get_all_users(self) -> List[User]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, avatar, created_at, last_login FROM users")
        rows = cursor.fetchall()
        return [User(id=row[0], name=row[1], avatar=row[2], created_at=row[3], last_login=row[4]) for row in rows]

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, avatar, created_at, last_login FROM users WHERE id=?", (user_id,))
        row = cursor.fetchone()
        if row:
            return User(id=row[0], name=row[1], avatar=row[2], created_at=row[3], last_login=row[4])
        return None

    def create_user(self, name: str, avatar: str) -> User:
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("INSERT INTO users (name, avatar, created_at) VALUES (?, ?, ?)",
                           (name, avatar, now))
            user_id = cursor.lastrowid
            cursor.execute("COMMIT")
            return self.get_user_by_id(user_id)
        except Exception as e:
            cursor.execute("ROLLBACK")
            logger.error(f"Ошибка создания пользователя: {e}")
            raise

    def update_user(self, user: User):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET name=?, avatar=?, last_login=? WHERE id=?",
                       (user.name, user.avatar, user.last_login, user.id))
        self.conn.commit()

    def delete_user(self, user_id: int):
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
            cursor.execute("DELETE FROM progress WHERE user_id=?", (user_id,))
            cursor.execute("DELETE FROM phrases WHERE user_id=?", (user_id,))
            cursor.execute("DELETE FROM achievements WHERE user_id=?", (user_id,))
            cursor.execute("COMMIT")
        except Exception as e:
            cursor.execute("ROLLBACK")
            logger.error(f"Ошибка удаления пользователя: {e}")
            raise

    def get_progress(self, user_id: int, lesson_id: str) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT stars, completed, mistakes, time_spent FROM progress WHERE user_id=? AND lesson_id=?",
                       (user_id, lesson_id))
        row = cursor.fetchone()
        if row:
            return {'stars': row[0], 'completed': bool(row[1]), 'mistakes': row[2], 'time_spent': row[3]}
        return None

    def set_progress(self, user_id: int, lesson_id: str, stars: int, completed: bool,
                     mistakes: int, time_spent: int):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO progress (user_id, lesson_id, stars, completed, mistakes, time_spent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, lesson_id, stars, int(completed), mistakes, time_spent))
        self.conn.commit()

    def reset_all_progress(self) -> None:
        """Удаляет прогресс всех пользователей.

        Не трогает users, phrases и achievements.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM progress")
        self.conn.commit()
        logger.info("Весь прогресс сброшен")

    def get_user_stats(self, user_id: int) -> Dict[str, int]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as lessons_completed,
                   SUM(mistakes) as total_mistakes,
                   SUM(time_spent) as total_time
            FROM progress
            WHERE user_id = ? AND completed = 1
        ''', (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                'lessons_completed': row[0] or 0,
                'total_mistakes': row[1] or 0,
                'total_time': row[2] or 0
            }
        return {'lessons_completed': 0, 'total_mistakes': 0, 'total_time': 0}

    def add_phrase(self, user_id: int, language: str, text: str, translation: str,
                   audio_path: str = None, image_path: str = None) -> Phrase:
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO phrases (user_id, language, text, translation, audio_path, image_path, created_at, practice_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        ''', (user_id, language, text, translation, audio_path, image_path, now))
        self.conn.commit()
        phrase_id = cursor.lastrowid
        return self.get_phrase(phrase_id)

    def get_phrase(self, phrase_id: int) -> Optional[Phrase]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, language, text, translation, audio_path, image_path, created_at, last_practiced, practice_count
            FROM phrases WHERE id=?
        ''', (phrase_id,))
        row = cursor.fetchone()
        if row:
            return Phrase(id=row[0], language=row[1], text=row[2], translation=row[3],
                          audio_path=row[4], image_path=row[5], created_at=row[6],
                          last_practiced=row[7], practice_count=row[8])
        return None

    def get_phrases_for_user(self, user_id: int, language: str = None) -> List[Phrase]:
        cursor = self.conn.cursor()
        if language:
            cursor.execute('''
                SELECT id, language, text, translation, audio_path, image_path, created_at, last_practiced, practice_count
                FROM phrases WHERE user_id=? AND language=?
                ORDER BY created_at DESC
            ''', (user_id, language))
        else:
            cursor.execute('''
                SELECT id, language, text, translation, audio_path, image_path, created_at, last_practiced, practice_count
                FROM phrases WHERE user_id=?
                ORDER BY created_at DESC
            ''', (user_id,))
        rows = cursor.fetchall()
        return [Phrase(id=r[0], language=r[1], text=r[2], translation=r[3],
                       audio_path=r[4], image_path=r[5], created_at=r[6],
                       last_practiced=r[7], practice_count=r[8]) for r in rows]

    def update_phrase(self, phrase: Phrase):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE phrases SET text=?, translation=?, audio_path=?, image_path=?, last_practiced=?, practice_count=?
            WHERE id=?
        ''', (phrase.text, phrase.translation, phrase.audio_path, phrase.image_path,
              phrase.last_practiced, phrase.practice_count, phrase.id))
        self.conn.commit()

    def delete_phrase(self, phrase_id: int):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM phrases WHERE id=?", (phrase_id,))
        self.conn.commit()

    def update_practice(self, phrase_id: int):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE phrases SET last_practiced=?, practice_count=practice_count+1
            WHERE id=?
        ''', (now, phrase_id))
        self.conn.commit()

    def get_setting(self, key: str) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None

    def set_setting(self, key: str, value: str):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def get_pin(self) -> str:
        return self.get_setting('pin') or '1234'

    def set_pin(self, pin: str):
        self.set_setting('pin', pin)

    def get_internet_enabled(self) -> bool:
        return self.get_setting('internet_enabled') == '1'

    def set_internet_enabled(self, enabled: bool):
        self.set_setting('internet_enabled', '1' if enabled else '0')

    def get_update_url(self) -> str:
        return self.get_setting('update_url') or 'https://example.com/update'

    def set_update_url(self, url: str):
        self.set_setting('update_url', url)

    def unlock_achievement(self, user_id: int, achievement_id: str):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT OR IGNORE INTO achievements (user_id, achievement_id, unlocked_at)
            VALUES (?, ?, ?)
        ''', (user_id, achievement_id, now))
        self.conn.commit()

    def get_achievements(self, user_id: int) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT achievement_id FROM achievements WHERE user_id=?", (user_id,))
        return [row[0] for row in cursor.fetchall()]

    def close(self):
        self.conn.close()