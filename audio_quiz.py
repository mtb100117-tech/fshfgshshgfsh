import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt
from ...controllers.app_controller import AppController
from ...utils.logger import logger


class AudioQuiz(QWidget):
    """Аудио-викторина.

    Использует слова из тематических уроков (не из алфавита и не из
    диалогов). Обеспечивает 1 правильный ответ + до 3 дистракторов.

    Кнопки «Новый вопрос» и варианты ответа — БЕЗ @debounce.
    """

    LANGUAGES = [
        ('en', '🇬🇧 English'),
        ('ar', '🇸🇦 العربية'),
        ('zh', '🇨🇳 中文'),
    ]

    MIN_ITEMS = 4

    def __init__(self, controller: AppController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window

        self.current_language = 'en'
        self.current_lesson_items = []
        self.correct_answer = None
        self.previous_correct = None
        self.options_buttons = []

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(12, 12, 12, 12)
        self.layout().setSpacing(10)

        logger.debug("AudioQuiz инициализирован")

        self.label = QLabel("🎧 Аудио-викторина")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
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

        self.question_label = QLabel("Нажмите 'Новый вопрос'")
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question_label.setStyleSheet("font-size: 18px; padding: 8px;")
        self.layout().addWidget(self.question_label)

        self.options_layout = QVBoxLayout()
        self.layout().addLayout(self.options_layout)

        self.new_btn = QPushButton("🔄 Новый вопрос")
        self.new_btn.setMinimumHeight(44)
        self.new_btn.clicked.connect(self.new_question)
        self.layout().addWidget(self.new_btn)

        self.back_btn = QPushButton("🚪 В главное меню")
        self.back_btn.setMinimumHeight(44)
        self.back_btn.clicked.connect(self.main_window.show_main_menu)
        self.layout().addWidget(self.back_btn)

    def showEvent(self, event):
        self.load_lesson()
        super().showEvent(event)

    def on_language_changed(self, index):
        code = self.lang_combo.currentData()
        if not code or code == self.current_language:
            return
        self.current_language = code
        logger.info(f"Аудио-викторина: смена языка на {code}")

        self.clear_options()
        self.correct_answer = None
        self.previous_correct = None
        self.question_label.setText("Нажмите 'Новый вопрос'")
        self.load_lesson()

    def load_lesson(self):
        """Загружает слова из тематического урока."""
        lessons = self.controller.get_lessons(self.current_language)

        pool = None
        for lesson in lessons:
            if lesson.is_dialog or lesson.id.endswith('_alphabet'):
                continue
            if len(lesson.items) >= self.MIN_ITEMS:
                pool = lesson
                break

        if pool is None:
            for lesson in lessons:
                if lesson.is_dialog or lesson.id.endswith('_alphabet'):
                    continue
                if len(lesson.items) >= 2:
                    pool = lesson
                    break

        if pool is not None:
            self.current_lesson_items = pool.items
            logger.debug(f"Аудио-викторина: {len(pool.items)} слов "
                         f"из '{pool.id}' ({self.current_language})")
        else:
            self.current_lesson_items = []
            logger.warning(f"Аудио-викторина: нет подходящего урока для "
                           f"{self.current_language}")

    def _format_item_label(self, item) -> str:
        pinyin = getattr(item, 'pinyin', None)
        if self.current_language == 'zh' and pinyin:
            return f"{item.text}  ({pinyin})"
        return item.text

    def new_question(self):
        if not self.current_lesson_items:
            QMessageBox.information(
                self, "Нет данных",
                f"Нет уроков для языка {self.current_language.upper()}")
            return
        if len(self.current_lesson_items) < 2:
            QMessageBox.information(self, "Мало данных",
                                    "Для викторины нужно минимум 2 слова")
            return

        candidates = [i for i in self.current_lesson_items
                      if i != self.previous_correct]
        if not candidates:
            candidates = list(self.current_lesson_items)
        self.correct_answer = random.choice(candidates)
        self.previous_correct = self.correct_answer

        pool = [item for item in self.current_lesson_items
                if item != self.correct_answer]
        num_distractors = min(3, len(pool))
        options = [self.correct_answer]
        if num_distractors > 0:
            options += random.sample(pool, num_distractors)
        random.shuffle(options)

        if self.correct_answer.audio:
            self.controller.audio.play_audio(self.correct_answer.audio)

        self.clear_options()
        for item in options:
            btn = QPushButton(self._format_item_label(item))
            btn.setMinimumHeight(48)
            btn.clicked.connect(lambda checked, it=item: self.check_answer(it))
            self.options_layout.addWidget(btn)
            self.options_buttons.append(btn)

        self.question_label.setText("🎧 Выберите правильный вариант")

    def clear_options(self):
        for btn in self.options_buttons:
            self.options_layout.removeWidget(btn)
            btn.deleteLater()
        self.options_buttons.clear()

    def check_answer(self, selected):
        if selected == self.correct_answer:
            QMessageBox.information(self, "Правильно!", "Молодец! 🎉")
            self.new_question()
        else:
            QMessageBox.warning(self, "Неправильно", "Попробуй ещё раз")
            if self.correct_answer and self.correct_answer.audio:
                self.controller.audio.play_audio(self.correct_answer.audio)