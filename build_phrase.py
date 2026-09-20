import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMessageBox, QComboBox, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, QTimer
from ...controllers.app_controller import AppController
from ...utils.logger import logger


class BuildPhrase(QWidget):
    """Игра «Собери фразу» — из диалогов выбранного языка.

    При открытии автоматически выбирает случайную фразу, чтобы
    пользователь не видел пустой экран. Кнопки — без @debounce.
    """

    LANGUAGES = [
        ('en', '🇬🇧 English'),
        ('ar', '🇸🇦 العربية'),
        ('zh', '🇨🇳 中文'),
    ]

    BUTTON_MIN_HEIGHT = 44
    TILE_MIN_WIDTH = 64

    def __init__(self, controller: AppController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window

        self.current_language = 'en'
        self.phrase_pool = []
        self.current_phrase = None
        self.previous_phrase = None
        self.correct_tiles = []
        self.pool_tiles = []
        self.answer_indices = []

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(12, 12, 12, 12)
        self.layout().setSpacing(10)

        logger.debug("BuildPhrase инициализирован")

        title = QLabel("🔤 Собери фразу")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 8px;")
        self.layout().addWidget(title)

        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(QLabel("Язык:"))
        self.lang_combo = QComboBox()
        for code, label in self.LANGUAGES:
            self.lang_combo.addItem(label, code)
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        header.addWidget(self.lang_combo)
        header.addStretch()

        self.audio_btn = QPushButton("🔊 Слушать")
        self.audio_btn.setMinimumHeight(self.BUTTON_MIN_HEIGHT)
        self.audio_btn.clicked.connect(self._play_current)
        header.addWidget(self.audio_btn)

        self.new_btn = QPushButton("🔄 Новая фраза")
        self.new_btn.setMinimumHeight(self.BUTTON_MIN_HEIGHT)
        self.new_btn.clicked.connect(self.new_phrase)
        header.addWidget(self.new_btn)
        self.layout().addLayout(header)

        phrase_frame = QFrame()
        phrase_frame.setStyleSheet(
            "QFrame { background-color: #FFF8E1; border: 2px solid #FFB74D; "
            "border-radius: 10px; }")
        phrase_layout = QVBoxLayout(phrase_frame)
        phrase_layout.setContentsMargins(16, 12, 16, 12)
        phrase_layout.setSpacing(4)
        hint = QLabel("Перевод:")
        hint.setStyleSheet("font-size: 13px; color: #888; "
                           "background: transparent; border: none;")
        phrase_layout.addWidget(hint)
        self.translation_label = QLabel("—")
        self.translation_label.setWordWrap(True)
        self.translation_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; "
            "background: transparent; border: none;")
        phrase_layout.addWidget(self.translation_label)
        self.pinyin_label = QLabel("")
        self.pinyin_label.setWordWrap(True)
        self.pinyin_label.setStyleSheet(
            "font-size: 16px; color: #555; "
            "background: transparent; border: none;")
        phrase_layout.addWidget(self.pinyin_label)
        self.layout().addWidget(phrase_frame)

        self.layout().addWidget(QLabel("Соберите фразу:"))
        self.answer_frame = QFrame()
        self.answer_frame.setMinimumHeight(70)
        self.answer_frame.setStyleSheet(
            "QFrame { background-color: #F5F5F5; border: 2px dashed #BDBDBD; "
            "border-radius: 10px; }")
        self.answer_layout = QHBoxLayout(self.answer_frame)
        self.answer_layout.setContentsMargins(8, 8, 8, 8)
        self.answer_layout.setSpacing(6)
        self.answer_layout.addStretch()
        self.layout().addWidget(self.answer_frame)

        self.layout().addWidget(QLabel("Доступные плитки:"))
        self.pool_frame = QFrame()
        self.pool_frame.setMinimumHeight(80)
        self.pool_frame.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 1px solid #C8E6C9; "
            "border-radius: 10px; }")
        self.pool_layout = QGridLayout(self.pool_frame)
        self.pool_layout.setContentsMargins(8, 8, 8, 8)
        self.pool_layout.setSpacing(6)
        self.layout().addWidget(self.pool_frame)
        self.layout().addStretch()

        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        self.clear_btn = QPushButton("🧹 Очистить")
        self.clear_btn.setMinimumHeight(self.BUTTON_MIN_HEIGHT)
        self.clear_btn.clicked.connect(self.clear_answer)
        bottom.addWidget(self.clear_btn)
        self.check_btn = QPushButton("✅ Проверить")
        self.check_btn.setMinimumHeight(self.BUTTON_MIN_HEIGHT)
        self.check_btn.clicked.connect(self.check_answer)
        bottom.addWidget(self.check_btn)
        self.layout().addLayout(bottom)

        back_btn = QPushButton("🚪 В главное меню")
        back_btn.setMinimumHeight(48)
        back_btn.clicked.connect(self.main_window.show_main_menu)
        self.layout().addWidget(back_btn)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.phrase_pool:
            self.load_phrases()
        if self.phrase_pool and self.current_phrase is None:
            QTimer.singleShot(50, self._pick_random_phrase)

    def on_language_changed(self, index):
        code = self.lang_combo.currentData()
        if not code or code == self.current_language:
            return
        self.current_language = code
        self.load_phrases()
        self.clear_game()
        if self.phrase_pool:
            QTimer.singleShot(50, self._pick_random_phrase)

    def load_phrases(self):
        lessons = self.controller.get_lessons(self.current_language)
        pool = []
        for lesson in lessons:
            if not lesson.is_dialog or not lesson.dialog:
                continue
            for line in lesson.dialog:
                tiles = self._split_to_tiles(line.text)
                if len(tiles) < 2:
                    continue
                pool.append({
                    'text': line.text,
                    'translation': line.translation or '',
                    'audio': line.audio,
                    'tiles': tiles,
                    'pinyin': getattr(line, 'pinyin', None),
                })
        self.phrase_pool = pool
        logger.info(f"BuildPhrase: {len(pool)} фраз для языка {self.current_language}")

    @staticmethod
    def _split_to_tiles(text: str):
        text = (text or '').strip()
        if not text:
            return []
        has_cjk = any('\u4e00' <= c <= '\u9fff' for c in text)
        if has_cjk:
            return [c for c in text if '\u4e00' <= c <= '\u9fff']
        return [w for w in text.split() if w]

    def _pick_random_phrase(self):
        if not self.phrase_pool:
            return
        candidates = [p for p in self.phrase_pool if p != self.previous_phrase]
        if not candidates:
            candidates = list(self.phrase_pool)
        self.current_phrase = random.choice(candidates)
        self.previous_phrase = self.current_phrase

        self.correct_tiles = list(self.current_phrase['tiles'])

        indexed = list(enumerate(self.correct_tiles))
        random.shuffle(indexed)
        self.pool_tiles = [{'text': t, 'used': False, 'orig': orig_idx}
                           for orig_idx, t in indexed]
        self.answer_indices = []

        self.translation_label.setText(self.current_phrase['translation'] or '—')
        if self.current_language == 'zh' and self.current_phrase.get('pinyin'):
            self.pinyin_label.setText(f"({self.current_phrase['pinyin']})")
        else:
            self.pinyin_label.setText("")

        self._render()

    def new_phrase(self):
        if not self.phrase_pool:
            QMessageBox.information(
                self, "Нет фраз",
                f"Для языка {self.current_language.upper()} нет диалогов.\n"
                "Запустите generate_content.py.")
            return
        self._pick_random_phrase()
        self._play_current()

    def _render(self):
        while self.answer_layout.count() > 1:
            item = self.answer_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for pos, pool_idx in enumerate(self.answer_indices):
            tile = self.pool_tiles[pool_idx]
            btn = QPushButton(tile['text'])
            btn.setMinimumHeight(44)
            btn.setMinimumWidth(self.TILE_MIN_WIDTH)
            btn.setStyleSheet(
                "QPushButton { background-color: #FFF59D; color: #333; "
                "border: 2px solid #FBC02D; border-radius: 8px; "
                "font-size: 18px; font-weight: bold; padding: 6px 12px; }"
                "QPushButton:hover { background-color: #FFF176; }")
            btn.clicked.connect(lambda checked, p=pos: self._return_to_pool(p))
            self.answer_layout.insertWidget(self.answer_layout.count() - 1, btn)

        while self.pool_layout.count():
            item = self.pool_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        free_tiles = [(i, t) for i, t in enumerate(self.pool_tiles) if not t['used']]
        cols = 6
        for slot, (pool_idx, tile) in enumerate(free_tiles):
            btn = QPushButton(tile['text'])
            btn.setMinimumHeight(44)
            btn.setMinimumWidth(self.TILE_MIN_WIDTH)
            btn.setStyleSheet(
                "QPushButton { background-color: #E8F5E9; color: #1B5E20; "
                "border: 2px solid #66BB6A; border-radius: 8px; "
                "font-size: 18px; font-weight: bold; padding: 6px 12px; }"
                "QPushButton:hover { background-color: #C8E6C9; }")
            btn.clicked.connect(lambda checked, p=pool_idx: self._pick_from_pool(p))
            row, col = divmod(slot, cols)
            self.pool_layout.addWidget(btn, row, col)

    def clear_game(self):
        self.current_phrase = None
        self.correct_tiles = []
        self.pool_tiles = []
        self.answer_indices = []
        self.translation_label.setText("—")
        self.pinyin_label.setText("")
        self._render()

    def clear_answer(self):
        if not self.pool_tiles:
            return
        for t in self.pool_tiles:
            t['used'] = False
        self.answer_indices = []
        self._render()

    def _pick_from_pool(self, pool_idx):
        if not (0 <= pool_idx < len(self.pool_tiles)):
            return
        tile = self.pool_tiles[pool_idx]
        if tile['used']:
            return
        tile['used'] = True
        self.answer_indices.append(pool_idx)
        self._render()

    def _return_to_pool(self, pos):
        if not (0 <= pos < len(self.answer_indices)):
            return
        pool_idx = self.answer_indices.pop(pos)
        self.pool_tiles[pool_idx]['used'] = False
        self._render()

    def _current_answer_text(self) -> str:
        parts = [self.pool_tiles[i]['text'] for i in self.answer_indices]
        if self._is_cjk_answer():
            return ''.join(parts)
        return ' '.join(parts)

    def _is_cjk_answer(self) -> bool:
        return any('\u4e00' <= c <= '\u9fff'
                   for c in ''.join(t['text'] for t in self.pool_tiles))

    def check_answer(self):
        if not self.current_phrase or not self.correct_tiles:
            return
        if len(self.answer_indices) != len(self.correct_tiles):
            QMessageBox.information(self, "Не готово", "Используйте все плитки.")
            return

        user_joined = self._current_answer_text()
        if self._is_cjk_answer():
            correct_joined = ''.join(self.correct_tiles)
        else:
            correct_joined = ' '.join(self.correct_tiles)

        if user_joined == correct_joined:
            QMessageBox.information(self, "Правильно! 🎉",
                                    f"«{self.current_phrase['text']}»")
            self._play_current()
        else:
            QMessageBox.warning(self, "Не совсем",
                                "Порядок не совпал. Попробуйте ещё раз.")

    def _play_current(self):
        if not self.current_phrase:
            return
        audio = self.current_phrase.get('audio')
        if audio:
            self.controller.audio.play_audio(audio)