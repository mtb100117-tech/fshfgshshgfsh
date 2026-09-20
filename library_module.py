import json
import webbrowser
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QListWidget, QListWidgetItem, QSplitter,
                             QFrame, QScrollArea, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt
from ..controllers.app_controller import AppController
from ..utils.config import CONTENT_DIR
from ..utils.logger import logger


class LibraryModule(QWidget):
    """Каталог рекомендованных книг со ссылками на легальные архивы.

    Клик по кнопке-ссылке открывает URL мгновенно — без @debounce,
    чтобы пользователь мог открыть несколько ссылок подряд.
    """

    LANGUAGE_LABELS = {
        'en': '🇬🇧 Английский',
        'ar': '🇸🇦 Арабский',
        'zh': '🇨🇳 Китайский',
        'all': '🌍 Все языки',
    }

    def __init__(self, controller: AppController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(12, 12, 12, 12)
        self.layout().setSpacing(10)

        logger.debug("LibraryModule инициализирован")

        self.catalog = self._load_catalog()
        self.categories = self.catalog.get('categories', [])
        self.pronunciation = self.catalog.get('pronunciation_guides', {})

        title = QLabel("📚 Библиотека книг")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 8px;")
        self.layout().addWidget(title)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Язык:"))
        self.lang_filter = QComboBox()
        for code, label in self.LANGUAGE_LABELS.items():
            self.lang_filter.addItem(label, code)
        self.lang_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.lang_filter)
        filter_layout.addStretch()

        self.pron_btn = QPushButton("🗣 Произношение")
        self.pron_btn.setMinimumHeight(40)
        self.pron_btn.clicked.connect(self.show_pronunciation_guide)
        filter_layout.addWidget(self.pron_btn)
        self.layout().addLayout(filter_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        self.layout().addWidget(splitter, 1)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        left_header = QLabel("Книги по категориям")
        left_header.setStyleSheet("font-weight: bold; font-size: 15px;")
        left_layout.addWidget(left_header)
        self.book_list = QListWidget()
        self.book_list.itemClicked.connect(self._on_book_selected)
        left_layout.addWidget(self.book_list, 1)
        splitter.addWidget(left)

        self._right_scroll = QScrollArea()
        self._right_scroll.setWidgetResizable(True)
        self._right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.detail = QWidget()
        self.detail_layout = QVBoxLayout(self.detail)
        self.detail_layout.setContentsMargins(12, 0, 12, 0)
        self.detail_layout.setSpacing(10)
        self._right_scroll.setWidget(self.detail)
        splitter.addWidget(self._right_scroll)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 680])

        back = QPushButton("🚪 В главное меню")
        back.setMinimumHeight(48)
        back.clicked.connect(lambda: self.main_window.show_main_menu())
        self.layout().addWidget(back)

        self._populate_list()

    def _load_catalog(self):
        path = CONTENT_DIR / 'library.json'
        if not path.exists():
            logger.warning(f"library.json не найден: {path}")
            return {'categories': [], 'pronunciation_guides': {}}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка чтения library.json: {e}", exc_info=True)
            return {'categories': [], 'pronunciation_guides': {}}

    def showEvent(self, event):
        super().showEvent(event)
        if self._right_scroll:
            self._right_scroll.verticalScrollBar().setValue(0)

    def _on_filter_changed(self, index):
        self._populate_list()

    def _populate_list(self):
        self.book_list.clear()
        lang_filter = self.lang_filter.currentData() or 'all'
        for cat in self.categories:
            books = [b for b in cat.get('books', [])
                     if lang_filter == 'all' or b.get('language') == lang_filter]
            if not books:
                continue
            header = QListWidgetItem(f"— {cat['name_ru']} —")
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            header.setForeground(Qt.GlobalColor.darkGreen)
            header.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.book_list.addItem(header)
            for book in books:
                icon = {'en': '🇬🇧', 'ar': '🇸🇦', 'zh': '🇨🇳'}.get(book['language'], '📖')
                item = QListWidgetItem(f"{icon}  {book['title_ru']}")
                item.setData(Qt.ItemDataRole.UserRole, book)
                self.book_list.addItem(item)

    def _on_book_selected(self, item):
        book = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(book, dict):
            self._show_book(book)

    def _clear_detail(self):
        for i in reversed(range(self.detail_layout.count())):
            w = self.detail_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

    def _show_book(self, book):
        self._clear_detail()
        if self._right_scroll:
            self._right_scroll.verticalScrollBar().setValue(0)

        title = QLabel(book.get('title_ru', ''))
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        self.detail_layout.addWidget(title)

        original = book.get('title_original', '')
        if original and original != book.get('title_ru'):
            lbl = QLabel(original)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("font-size: 15px; color: #666; font-style: italic;")
            self.detail_layout.addWidget(lbl)

        meta_lines = []
        if book.get('author'):
            meta_lines.append(f"✍️ {book['author']}")
        if book.get('language'):
            meta_lines.append(f"🌍 {self.LANGUAGE_LABELS.get(book['language'], book['language'])}")
        if book.get('age'):
            meta_lines.append(f"👶 {book['age']}")
        if meta_lines:
            meta = QLabel("    ".join(meta_lines))
            meta.setStyleSheet("color: #444; font-size: 14px; padding: 4px 0;")
            meta.setWordWrap(True)
            self.detail_layout.addWidget(meta)

        self.detail_layout.addWidget(self._hline())

        if book.get('why_useful'):
            self._add_section("📖 Чем полезна", book['why_useful'])
        if book.get('format'):
            self._add_section("💾 Формат", book['format'])
        if book.get('key_words'):
            self._add_section("🔑 Ключевые слова", ", ".join(book['key_words']))
        if book.get('notes'):
            self._add_section("💡 Заметки", book['notes'])

        self.detail_layout.addWidget(self._hline())

        source_name = book.get('source_name', 'Источник')
        source_url = book.get('source_url', '')
        if source_url:
            btn = QPushButton(f"🔗 Открыть: {source_name}")
            btn.setMinimumHeight(44)
            btn.setStyleSheet(
                "QPushButton { background-color: #2196F3; color: white; "
                "border: none; border-radius: 8px; font-size: 15px; }"
                "QPushButton:hover { background-color: #1976D2; }")
            btn.clicked.connect(lambda checked, u=source_url: self._open_url(u))
            self.detail_layout.addWidget(btn)

        for alt in book.get('alternatives', []) or []:
            if not alt.get('url'):
                continue
            btn = QPushButton(f"🔗 {alt.get('name', 'Альтернатива')}")
            btn.setMinimumHeight(40)
            btn.setStyleSheet(
                "QPushButton { background-color: #E8F5E9; color: #1B5E20; "
                "border: 1px solid #66BB6A; border-radius: 8px; font-size: 14px; }"
                "QPushButton:hover { background-color: #C8E6C9; }")
            btn.clicked.connect(lambda checked, u=alt['url']: self._open_url(u))
            self.detail_layout.addWidget(btn)

        tip = QLabel(
            "💡 Как заниматься: сначала слушаем, потом смотрим, потом читаем "
            "вместе. 5–7 слов на книгу. Ритм 10–15 минут, 4–5 раз в неделю.")
        tip.setWordWrap(True)
        tip.setStyleSheet(
            "color: #555; font-size: 13px; padding: 10px; "
            "background-color: #FFF8E1; border-radius: 8px;")
        self.detail_layout.addWidget(tip)
        self.detail_layout.addStretch()

    def _add_section(self, title: str, text: str):
        label = QLabel(title)
        label.setStyleSheet("font-weight: bold; font-size: 15px; padding-top: 4px;")
        self.detail_layout.addWidget(label)
        body = QLabel(text)
        body.setWordWrap(True)
        body.setStyleSheet("font-size: 14px; color: #333; padding-left: 4px;")
        self.detail_layout.addWidget(body)

    def _hline(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def _open_url(self, url: str):
        """БЕЗ @debounce — можно открыть несколько ссылок подряд."""
        try:
            webbrowser.open(url)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка",
                                f"Не удалось открыть ссылку:\n{url}\n\n{e}")

    def show_pronunciation_guide(self):
        """БЕЗ @debounce — смена фильтра + повторный клик должны работать."""
        lang = self.lang_filter.currentData()
        if lang == 'all':
            parts = []
            for code in ('en', 'ar', 'zh'):
                g = self.pronunciation.get(code)
                if g:
                    parts.append(f"── {g['title']} ──\n{g['text']}")
            text = "\n\n".join(parts) or "Гид по произношению не найден."
        else:
            g = self.pronunciation.get(lang)
            text = g['text'] if g else "Гид по произношению не найден."
        QMessageBox.information(self, "Произношение", text)