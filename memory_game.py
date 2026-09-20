import os
import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from ...controllers.app_controller import AppController
from ...utils.config import CONTENT_DIR
from ...utils.logger import logger


class MemoryGame(QWidget):
    """Игра «Найди пару» со словами и озвучкой.

    Пары формируются из первых PAIRS_COUNT слов тематического урока
    выбранного языка. При открытии карточки показывается слово и
    проигрывается его аудио.
    """

    LANGUAGES = [
        ('en', '🇬🇧 English'),
        ('ar', '🇸🇦 العربية'),
        ('zh', '🇨🇳 中文'),
    ]

    PAIRS_COUNT = 8
    CARD_SIZE = 110

    def __init__(self, controller: AppController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window

        self.current_language = 'en'
        self.words_pool = []        # список dict {emoji, word, audio}
        self.cards = []             # 2*PAIRS_COUNT карточек с полем pair_id
        self.revealed = []
        self.matched = set()
        self.first_card = None
        self.second_card = None
        self.lock = False
        self.stars = 3
        self.mistakes = 0
        self.lesson_id = "memory_game_1"
        self._closing = False

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(12, 12, 12, 12)
        self.layout().setSpacing(10)

        logger.debug("MemoryGame инициализирован")

        # Заголовок
        self.label = QLabel("🔍 Найди пару")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 8px;")
        self.layout().addWidget(self.label)

        # Выбор языка
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Язык:"))
        self.lang_combo = QComboBox()
        for code, name in self.LANGUAGES:
            self.lang_combo.addItem(name, code)
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        self.layout().addLayout(lang_layout)

        # Сетка
        self.grid = QGridLayout()
        self.grid.setSpacing(8)
        self.layout().addLayout(self.grid)

        self.new_game_btn = QPushButton("🔄 Новая игра")
        self.new_game_btn.setMinimumHeight(44)
        self.new_game_btn.clicked.connect(self.init_game)
        self.layout().addWidget(self.new_game_btn)

        self.back_btn = QPushButton("🚪 В главное меню")
        self.back_btn.setMinimumHeight(44)
        self.back_btn.clicked.connect(self.main_window.show_main_menu)
        self.layout().addWidget(self.back_btn)

        self._load_words()
        self.init_game()

    # ---------- Загрузка слов ----------

    def _load_words(self):
        """Берёт первые PAIRS_COUNT слов из первого тематического урока."""
        lessons = self.controller.get_lessons(self.current_language)
        for lesson in lessons:
            if lesson.is_dialog or lesson.id.endswith('_alphabet'):
                continue
            if len(lesson.items) < self.PAIRS_COUNT:
                continue
            self.words_pool = []
            for item in lesson.items[:self.PAIRS_COUNT]:
                emoji = "🖼"  # запасной вариант
                img_rel = getattr(item, 'image', '') or ''
                img_path = CONTENT_DIR / img_rel if img_rel else None
                # Если есть PNG — можно было бы использовать его,
                # но по умолчанию берём эмодзи-заглушку по id слова.
                # Эмодзи достаём из того, что записано в TOPICS — но
                # у LessonItem этого поля нет, поэтому используем
                # первый символ картинки (или общий значок).
                self.words_pool.append({
                    'text': item.text,
                    'audio': item.audio,
                    'emoji': emoji,
                })
            logger.info(f"MemoryGame: {len(self.words_pool)} слов "
                        f"из '{lesson.id}' ({self.current_language})")
            return
        self.words_pool = []
        logger.warning(f"MemoryGame: нет урока с ≥{self.PAIRS_COUNT} словами "
                       f"для {self.current_language}")

    # ---------- Игра ----------

    def init_game(self):
        """Строит 16 карточек (8 пар) со случайным расположением."""
        logger.debug("MemoryGame: инициализация новой игры")

        if not self.words_pool:
            self._clear_grid()
            msg = QLabel(f"Нет слов для языка {self.current_language.upper()}.\n"
                         f"Запустите generate_content.py.")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setStyleSheet("color: #C62828; font-size: 16px; padding: 20px;")
            self.grid.addWidget(msg, 0, 0, 1, 4)
            return

        # Создаём карточки: по 2 копии каждого слова, с pair_id.
        cards = []
        for pair_id, w in enumerate(self.words_pool):
            for _ in range(2):
                cards.append({
                    'pair_id': pair_id,
                    'text': w['text'],
                    'audio': w['audio'],
                })
        random.shuffle(cards)

        self.cards = cards
        self.revealed = [False] * len(cards)
        self.matched = set()
        self.first_card = None
        self.second_card = None
        self.lock = False
        self.mistakes = 0
        self.stars = 3
        self._closing = False

        self._setup_grid()

        if self.controller.current_user:
            self.controller.set_progress(self.lesson_id, 0, False, 0, 0)

    def _clear_grid(self):
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def _setup_grid(self):
        self._clear_grid()
        cols = 4
        for idx in range(len(self.cards)):
            btn = QPushButton("?")
            btn.setFixedSize(self.CARD_SIZE, self.CARD_SIZE)
            btn.setStyleSheet(
                "QPushButton { font-size: 20px; background-color: #4CAF50; "
                "color: white; border-radius: 10px; font-weight: bold; }"
                "QPushButton:hover { background-color: #45a049; }")
            btn.clicked.connect(lambda checked, i=idx: self.on_card_click(i))
            self.grid.addWidget(btn, idx // cols, idx % cols)

    def on_card_click(self, idx):
        """Обработка клика. БЕЗ @debounce — иначе теряются вторые клики."""
        if self._closing or self.lock:
            return
        if idx in self.matched or self.revealed[idx]:
            return

        self.revealed[idx] = True
        self.update_card(idx)

        # Проигрываем аудио слова при открытии карточки.
        card = self.cards[idx]
        if card.get('audio') and os.path.exists(card['audio']):
            self.controller.audio.play_audio(card['audio'])

        if self.first_card is None:
            self.first_card = idx
        elif self.second_card is None:
            self.second_card = idx
            self.check_match()

    def check_match(self):
        c1 = self.cards[self.first_card]
        c2 = self.cards[self.second_card]
        if c1['pair_id'] == c2['pair_id']:
            self.matched.add(self.first_card)
            self.matched.add(self.second_card)
            self.first_card = None
            self.second_card = None
            if len(self.matched) == len(self.cards):
                self.end_game()
        else:
            self.mistakes += 1
            self.lock = True
            QTimer.singleShot(1200, self.reset_cards)

    def reset_cards(self):
        if self._closing:
            return
        if self.first_card is not None:
            self.revealed[self.first_card] = False
            self.update_card(self.first_card)
        if self.second_card is not None:
            self.revealed[self.second_card] = False
            self.update_card(self.second_card)
        self.first_card = None
        self.second_card = None
        self.lock = False

    def update_card(self, idx):
        widget = self.grid.itemAt(idx).widget()
        if not widget:
            return
        card = self.cards[idx]
        if idx in self.matched:
            widget.setText(f"✓\n{card['text']}")
            widget.setEnabled(False)
        elif self.revealed[idx]:
            widget.setText(card['text'])
        else:
            widget.setText("?")

    def end_game(self):
        if self._closing:
            return
        self._closing = True
        if self.mistakes <= 1:
            stars = 3
        elif self.mistakes <= 3:
            stars = 2
        else:
            stars = 1
        self.stars = stars
        if self.controller.current_user:
            self.controller.set_progress(self.lesson_id, stars, True, self.mistakes, 0)
        logger.info(f"MemoryGame: игра окончена. Звёзды: {stars}, Ошибки: {self.mistakes}")
        QMessageBox.information(self, "Игра окончена",
                                f"Ошибки: {self.mistakes}\nЗвёзды: {'⭐' * stars}")
        QTimer.singleShot(100, self._go_back)

    def _go_back(self):
        self.main_window.show_main_menu()
        self._closing = False

    def on_language_changed(self, index):
        code = self.lang_combo.currentData()
        if not code or code == self.current_language:
            return
        self.current_language = code
        self._load_words()
        self.init_game()