import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QListWidget, QListWidgetItem, QStackedWidget,
                             QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap
from ..controllers.app_controller import AppController
from ..utils.config import CONTENT_DIR
from ..utils.debounce import debounce
from ..utils.logger import logger


class FlashcardsModule(QWidget):
    def __init__(self, controller: AppController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window
        self.current_lang = 'en'
        self.topics_data = []
        self.current_cards = []
        self.current_card_index = 0
        self._is_opening_topic = False

        self.setLayout(QVBoxLayout())

        logger.debug("FlashcardsModule инициализирован")

        self.title = QLabel("🖼 Карточки")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 28px; font-weight: bold; padding: 10px;")
        self.layout().addWidget(self.title)

        self.stack = QStackedWidget()
        self.layout().addWidget(self.stack)

        # Экран 1: Список тем
        self.topics_widget = QWidget()
        self.topics_layout = QVBoxLayout(self.topics_widget)

        lang_layout = QHBoxLayout()
        self.btn_en = QPushButton("🇬🇧 English")
        self.btn_ar = QPushButton("🇸🇦 العربية")
        self.btn_zh = QPushButton("🇨🇳 中文")
        for btn, lang in [(self.btn_en, 'en'), (self.btn_ar, 'ar'), (self.btn_zh, 'zh')]:
            btn.clicked.connect(lambda checked, l=lang: self.change_language(l))
            lang_layout.addWidget(btn)
        self.topics_layout.addLayout(lang_layout)

        self.topics_list = QListWidget()
        self.topics_list.setIconSize(QSize(64, 64))
        self.topics_list.setStyleSheet("font-size: 16px;")
        self.topics_list.itemDoubleClicked.connect(self.open_topic)
        self.topics_layout.addWidget(self.topics_list)

        self.stack.addWidget(self.topics_widget)

        # Экран 2: Просмотр карточек
        self.card_widget = QWidget()
        self.card_layout = QVBoxLayout(self.card_widget)

        self.card_image = QLabel()
        self.card_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_image.setStyleSheet(
            "background-color: #f0f8ff; border-radius: 15px; border: 2px solid #4CAF50;")
        self.card_image.setMinimumHeight(300)
        self.card_layout.addWidget(self.card_image)

        self.card_word = QLabel()
        self.card_word.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_word.setStyleSheet("font-size: 42px; font-weight: bold; color: #333;")
        self.card_layout.addWidget(self.card_word)

        self.card_translation = QLabel()
        self.card_translation.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_translation.setStyleSheet("font-size: 24px; color: #666;")
        self.card_layout.addWidget(self.card_translation)

        self.card_counter = QLabel()
        self.card_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_counter.setStyleSheet("font-size: 16px; color: #888;")
        self.card_layout.addWidget(self.card_counter)

        btn_layout = QHBoxLayout()
        self.btn_prev = QPushButton("◀ Назад")
        self.btn_prev.setFixedSize(120, 50)
        self.btn_prev.clicked.connect(self.prev_card)
        btn_layout.addWidget(self.btn_prev)

        self.btn_audio = QPushButton("🔊 Слушать")
        self.btn_audio.setFixedSize(150, 50)
        self.btn_audio.setStyleSheet("background-color: #FF9800; font-size: 18px;")
        self.btn_audio.clicked.connect(self.play_card_audio)
        btn_layout.addWidget(self.btn_audio)

        self.btn_next = QPushButton("Далее ▶")
        self.btn_next.setFixedSize(120, 50)
        self.btn_next.clicked.connect(self.next_card)
        btn_layout.addWidget(self.btn_next)

        self.card_layout.addLayout(btn_layout)

        self.btn_back_to_topics = QPushButton("⬅ К списку тем")
        self.btn_back_to_topics.clicked.connect(self._back_to_topics)
        self.card_layout.addWidget(self.btn_back_to_topics)

        self.stack.addWidget(self.card_widget)

        self.exit_btn = QPushButton("🚪 В главное меню")
        self.exit_btn.clicked.connect(lambda: self.main_window.show_main_menu())
        self.layout().addWidget(self.exit_btn)

        self.load_topics()

    def change_language(self, lang):
        logger.info(f"Смена языка в карточках: {lang}")
        self.current_lang = lang
        self.load_topics()

    def load_topics(self):
        self.topics_list.clear()
        flashcards_path = CONTENT_DIR / self.current_lang / 'flashcards.json'

        if not flashcards_path.exists():
            logger.warning(f"Файл flashcards.json не найден: {flashcards_path}")
            self.topics_list.addItem("Нет загруженного контента для этого языка.\n"
                                     "Запустите generate_content.py или импортируйте ZIP.")
            return

        try:
            with open(flashcards_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.topics_data = data.get('topics', [])
            logger.info(f"Загружено {len(self.topics_data)} тем для языка {self.current_lang}")

            for topic in self.topics_data:
                cards_count = len(topic.get('cards', []))

                name = topic.get('name') or topic.get('id', 'Topic')
                icon = topic.get('icon', '📚')
                if icon and not name.startswith(icon):
                    name = f"{icon} {name}"

                item = QListWidgetItem(f"{name}  ({cards_count} слов)")
                item.setData(Qt.ItemDataRole.UserRole, topic.get('id', ''))
                self.topics_list.addItem(item)
        except Exception as e:
            logger.error(f"Ошибка загрузки flashcards.json: {e}", exc_info=True)
            self.topics_list.addItem(f"Ошибка загрузки: {e}")

    @debounce(300)
    def open_topic(self, item):
        if self._is_opening_topic:
            return
        self._is_opening_topic = True

        try:
            try:
                topic_id = item.data(Qt.ItemDataRole.UserRole)
            except RuntimeError:
                return

            if not topic_id:
                return

            topic = None
            for t in self.topics_data:
                if t.get('id') == topic_id:
                    topic = t
                    break

            if not topic:
                return

            self.current_cards = topic.get('cards', [])
            if not self.current_cards:
                QMessageBox.information(self, "Пусто", "В этой теме нет карточек")
                return

            logger.info(f"Открыта тема: {topic.get('name')} ({len(self.current_cards)} карточек)")
            self.current_card_index = 0
            self.show_current_card()
            self.stack.setCurrentIndex(1)
        finally:
            self._is_opening_topic = False

    def _back_to_topics(self):
        self._is_opening_topic = False
        self.stack.setCurrentIndex(0)

    def show_current_card(self):
        if not self.current_cards:
            return
        card = self.current_cards[self.current_card_index]

        img_rel = card.get('image', '')
        img_path = CONTENT_DIR / img_rel if img_rel else None
        if img_path and img_path.exists():
            pixmap = QPixmap(str(img_path))
            if not pixmap.isNull():
                self.card_image.setPixmap(pixmap.scaled(
                    max(self.card_image.width(), 1),
                    max(self.card_image.height() - 20, 1),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))
            else:
                self.card_image.setText(f"🖼 {card.get('word', '')}")
        else:
            self.card_image.setText(f"🖼 {card.get('word', '')}")

        word = card.get('word', '')
        if self.current_lang == 'zh':
            pinyin = card.get('pinyin', '')
            self.card_word.setText(f"{pinyin}\n{word}" if pinyin else word)
        else:
            self.card_word.setText(word)

        self.card_translation.setText(card.get('translation', ''))
        self.card_counter.setText(f"Карточка {self.current_card_index + 1} из {len(self.current_cards)}")

        from ..utils.rtl_helper import set_rtl_for_label, set_ltr_for_label, set_cjk_for_label
        if self.current_lang == 'ar':
            set_rtl_for_label(self.card_word)
            set_rtl_for_label(self.card_translation)
        elif self.current_lang == 'zh':
            set_cjk_for_label(self.card_word)
            set_ltr_for_label(self.card_translation)
        else:
            set_ltr_for_label(self.card_word)
            set_ltr_for_label(self.card_translation)

    def prev_card(self):
        if self.current_card_index > 0:
            self.current_card_index -= 1
            self.show_current_card()

    def next_card(self):
        if self.current_card_index < len(self.current_cards) - 1:
            self.current_card_index += 1
            self.show_current_card()
        else:
            QMessageBox.information(self, "Ура!", "Ты выучил все карточки в этой теме! 🎉")
            self._back_to_topics()

    def play_card_audio(self):
        if not self.current_cards:
            return
        card = self.current_cards[self.current_card_index]
        audio_rel = card.get('audio', '')
        audio_path = CONTENT_DIR / audio_rel if audio_rel else None
        if audio_path and audio_path.exists():
            self.controller.audio.play_audio(str(audio_path))
        else:
            QMessageBox.warning(self, "Ошибка", f"Аудиофайл не найден:\n{audio_path}")