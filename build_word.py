import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from ...controllers.app_controller import AppController
from ...utils.config import CONTENT_DIR
from ...utils.logger import logger


class BuildWord(QWidget):
    """Игра «Собери слово» — из тематического урока выбранного языка.

    Исключает алфавит (там односимвольные слова — собирать нечего)
    и диалоги (там реплики, а не отдельные слова).

    Клики по буквам и кнопка «Новое слово» — БЕЗ @debounce.
    """

    LANGUAGES = [
        ('en', '🇬🇧 English'),
        ('ar', '🇸🇦 العربية'),
        ('zh', '🇨🇳 中文'),
    ]

    MIN_WORD_LEN = 2
    MAX_WORD_LEN = 12
    BUTTON_MIN_HEIGHT = 44
    LETTER_BTN_SIZE = 48
    PICTURE_W, PICTURE_H = 200, 200

    def __init__(self, controller: AppController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window

        self.current_language = 'en'
        self.word_pool = []
        self.current_word = None
        self.current_item = None
        self.previous_item = None
        self.shuffled_letters = []
        self.selected_letters = []
        self.letter_buttons = []

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(12, 12, 12, 12)
        self.layout().setSpacing(10)

        logger.debug("BuildWord инициализирован")

        self.label = QLabel("🔤 Собери слово")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 8px;")
        self.layout().addWidget(self.label)

        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Язык:"))
        self.lang_combo = QComboBox()
        for code, name in self.LANGUAGES:
            self.lang_combo.addItem(name, code)
        self.lang_combo.setCurrentIndex(0)
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        self.layout().addLayout(lang_layout)

        self.picture_label = QLabel("Картинка")
        self.picture_label.setFixedSize(self.PICTURE_W, self.PICTURE_H)
        self.picture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.picture_label.setStyleSheet(
            "border: 1px dashed #BDBDBD; background-color: #FAFAFA; "
            "color: #9E9E9E; font-size: 13px;")
        picture_row = QHBoxLayout()
        picture_row.addStretch()
        picture_row.addWidget(self.picture_label)
        picture_row.addStretch()
        self.layout().addLayout(picture_row)

        self.answer_field = QLabel("")
        self.answer_field.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.answer_field.setStyleSheet(
            "border: 2px solid #4CAF50; border-radius: 8px; min-height: 44px; "
            "font-size: 24px; font-weight: bold; color: #333; "
            "background-color: #FFFFFF; padding: 4px;")
        self.layout().addWidget(self.answer_field)

        self.letters_layout = QHBoxLayout()
        self.letters_layout.setSpacing(8)
        self.letters_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout().addLayout(self.letters_layout)

        self.layout().addStretch()

        self.new_btn = QPushButton("🔄 Новое слово")
        self.new_btn.setMinimumHeight(self.BUTTON_MIN_HEIGHT)
        self.new_btn.clicked.connect(self.new_word)
        self.layout().addWidget(self.new_btn)

        self.back_btn = QPushButton("🚪 В главное меню")
        self.back_btn.setMinimumHeight(self.BUTTON_MIN_HEIGHT)
        self.back_btn.clicked.connect(self.main_window.show_main_menu)
        self.layout().addWidget(self.back_btn)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.word_pool:
            self.load_words()
        if not self.current_word and self.word_pool:
            self.new_word()

    def on_language_changed(self, index):
        code = self.lang_combo.currentData()
        if not code or code == self.current_language:
            return
        self.current_language = code
        self.load_words()
        self.new_word()

    def load_words(self):
        lessons = self.controller.get_lessons(self.current_language)
        pool = []
        for lesson in lessons:
            if lesson.is_dialog or lesson.id.endswith('_alphabet'):
                continue
            for item in lesson.items:
                text = (item.text or '').strip()
                plain = text.replace(' ', '')
                if not (self.MIN_WORD_LEN <= len(plain) <= self.MAX_WORD_LEN):
                    continue
                pool.append(item)
        self.word_pool = pool
        logger.info(f"BuildWord: {len(pool)} слов для языка {self.current_language}")

    def new_word(self):
        if not self.word_pool:
            self.current_word = None
            self.current_item = None
            self.picture_label.clear()
            self.picture_label.setText("Нет слов для этой игры")
            self.answer_field.setText("")
            self.clear_letter_buttons()
            QMessageBox.information(
                self, "Нет данных",
                f"Нет подходящих слов для языка {self.current_language.upper()}.\n"
                "Запустите generate_content.py.")
            return

        candidates = [w for w in self.word_pool if w != self.previous_item]
        if not candidates:
            candidates = list(self.word_pool)
        self.current_item = random.choice(candidates)
        self.previous_item = self.current_item

        self.current_word = (self.current_item.text or '').strip()
        letters = list(self.current_word.replace(' ', ''))
        random.shuffle(letters)
        self.shuffled_letters = letters
        self.selected_letters = []
        self._render_picture()
        self.update_ui()

    def _render_picture(self):
        img_rel = getattr(self.current_item, 'image', '') if self.current_item else ''
        img_path = CONTENT_DIR / img_rel if img_rel else None
        if img_path and img_path.exists():
            pixmap = QPixmap(str(img_path))
            if not pixmap.isNull():
                self.picture_label.setPixmap(pixmap.scaled(
                    self.PICTURE_W, self.PICTURE_H,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))
                self.picture_label.setStyleSheet(
                    "border: 1px solid #BDBDBD; background-color: #FFFFFF;")
                return
        self.picture_label.clear()
        self.picture_label.setText("Картинка не найдена")
        self.picture_label.setStyleSheet(
            "border: 1px dashed #BDBDBD; background-color: #FAFAFA; "
            "color: #9E9E9E; font-size: 13px;")

    def update_ui(self):
        self.answer_field.setText("".join(self.selected_letters))
        self.clear_letter_buttons()
        for i, ch in enumerate(self.shuffled_letters):
            btn = QPushButton(ch)
            btn.setFixedSize(self.LETTER_BTN_SIZE, self.LETTER_BTN_SIZE)
            btn.setStyleSheet(
                "QPushButton { background-color: #E8F5E9; color: #1B5E20; "
                "border: 2px solid #66BB6A; border-radius: 8px; "
                "font-size: 22px; font-weight: bold; }"
                "QPushButton:hover { background-color: #C8E6C9; }")
            btn.clicked.connect(lambda checked, idx=i: self.select_letter(idx))
            self.letters_layout.addWidget(btn)
            self.letter_buttons.append(btn)

    def clear_letter_buttons(self):
        for btn in self.letter_buttons:
            self.letters_layout.removeWidget(btn)
            btn.deleteLater()
        self.letter_buttons.clear()

    def select_letter(self, idx):
        """Клик по букве. БЕЗ @debounce — при наборе слова важен каждый клик."""
        if not (0 <= idx < len(self.shuffled_letters)):
            return
        letter = self.shuffled_letters.pop(idx)
        self.selected_letters.append(letter)
        self.update_ui()

        target = self.current_word.replace(' ', '')
        if "".join(self.selected_letters) == target:
            audio = getattr(self.current_item, 'audio', None)
            if audio:
                self.controller.audio.play_audio(audio)
            QMessageBox.information(self, "Поздравляю!",
                                    "Ты собрал слово правильно! 🎉")
            self.new_word()
        elif len(self.shuffled_letters) == 0:
            QMessageBox.warning(self, "Неправильно", "Попробуй ещё раз")
            self.new_word()