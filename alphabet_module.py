from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QScrollArea, QFrame,
                             QMessageBox)
from PyQt6.QtCore import Qt
from ..controllers.app_controller import AppController
from ..utils.rtl_helper import set_rtl_for_label, set_cjk_for_label
from ..utils.logger import logger


class AlphabetModule(QWidget):
    """Три алфавита рядом: EN / AR / ZH.

    Источник данных — урок `{lang}_alphabet` из lessons.json.
    """

    LANGUAGES = [
        ('en', '🇬🇧 English', 'Comic Sans MS'),
        ('ar', '🇸🇦 العربية', 'Noto Naskh Arabic'),
        ('zh', '🇨🇳 中文',     'Noto Sans SC Thin'),
    ]

    def __init__(self, controller: AppController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(12, 12, 12, 12)
        self.layout().setSpacing(10)

        logger.debug("AlphabetModule инициализирован")

        self.title = QLabel("🔤 Алфавит — три языка рядом")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 8px;")
        self.layout().addWidget(self.title)

        hint = QLabel("Нажимайте ▶ у каждой буквы, чтобы услышать произношение")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #666; font-size: 14px; padding: 4px;")
        self.layout().addWidget(hint)

        header = QHBoxLayout()
        header.setSpacing(8)
        for _, label, _ in self.LANGUAGES:
            h = QLabel(label)
            h.setAlignment(Qt.AlignmentFlag.AlignCenter)
            h.setStyleSheet(
                "font-size: 18px; font-weight: bold; padding: 6px; "
                "background-color: #E8F5E9; border-radius: 8px;")
            header.addWidget(h, 1)
        self.layout().addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.layout().addWidget(self.scroll, 1)

        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setSpacing(6)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.scroll.setWidget(self.grid_widget)

        back_btn = QPushButton("🚪 В главное меню")
        back_btn.setMinimumHeight(48)
        back_btn.clicked.connect(lambda: self.main_window.show_main_menu())
        self.layout().addWidget(back_btn)

        self._populated = False

    def showEvent(self, event):
        super().showEvent(event)
        if not self._populated:
            self._populate()
            self._populated = True

    def _find_alphabet_lesson(self, lang: str):
        target_id = f"{lang}_alphabet"
        for lesson in self.controller.get_lessons(lang):
            if lesson.id == target_id:
                return lesson
        return None

    def _populate(self):
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w:
                w.deleteLater()

        lessons = {code: self._find_alphabet_lesson(code)
                   for code, _, _ in self.LANGUAGES}

        # Диагностика: покажет в логе, что нашлось для каждого языка.
        for code, _, _ in self.LANGUAGES:
            lsn = lessons.get(code)
            if lsn is None:
                logger.warning(f"AlphabetModule: урок '{code}_alphabet' не найден")
            else:
                logger.info(f"AlphabetModule: {code} — {len(lsn.items)} элементов")

        max_len = max(
            (len(l.items) for l in lessons.values() if l is not None),
            default=0,
        )

        if max_len == 0:
            empty = QLabel("Алфавит не найден. Запустите generate_content.py.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #C62828; font-size: 16px; padding: 20px;")
            self.grid.addWidget(empty, 0, 0, 1, len(self.LANGUAGES))
            return

        for row in range(max_len):
            for col, (lang, _, font_family) in enumerate(self.LANGUAGES):
                lesson = lessons.get(lang)
                if lesson is None or row >= len(lesson.items):
                    # Если для этого языка данных нет — показываем
                    # информативную заглушку только в первой строке.
                    if row == 0:
                        miss = QLabel(f"Нет данных для «{lang}».\n"
                                      f"Запустите generate_content.py.")
                        miss.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        miss.setWordWrap(True)
                        miss.setStyleSheet(
                            "color: #C62828; font-size: 13px; padding: 8px; "
                            "background-color: #FFEBEE; border-radius: 6px;")
                        self.grid.addWidget(miss, row, col)
                    else:
                        self.grid.addWidget(QLabel(""), row, col)
                    continue
                item = lesson.items[row]
                self.grid.addWidget(self._build_card(lang, item, font_family), row, col)

        for col in range(len(self.LANGUAGES)):
            self.grid.setColumnStretch(col, 1)

    def _build_card(self, lang: str, item, font_family: str) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 1px solid #C8E6C9; "
            "border-radius: 8px; } QFrame:hover { border: 2px solid #4CAF50; }")
        card.setMinimumHeight(64)

        row = QHBoxLayout(card)
        row.setContentsMargins(10, 6, 10, 6)
        row.setSpacing(8)

        char_label = QLabel(item.text)
        char_label.setStyleSheet(
            f"font-family: '{font_family}'; font-size: 28px; font-weight: bold; "
            f"background: transparent; border: none;")
        char_label.setMinimumWidth(70)

        if lang == 'ar':
            set_rtl_for_label(char_label)
        elif lang == 'zh':
            set_cjk_for_label(char_label)
        row.addWidget(char_label)

        info = item.translation or ""
        if lang == 'zh' and getattr(item, 'pinyin', None):
            info = f"{item.pinyin} — {info}"
        info_label = QLabel(info)
        info_label.setStyleSheet(
            "font-size: 14px; color: #444; background: transparent; border: none;")
        info_label.setWordWrap(True)
        row.addWidget(info_label, 1)

        play_btn = QPushButton("▶")
        play_btn.setFixedSize(36, 36)
        play_btn.setStyleSheet(
            "font-size: 16px; background-color: #4CAF50; color: white; "
            "border-radius: 18px; border: none;")
        play_btn.clicked.connect(lambda checked, a=item.audio: self._play(a))
        row.addWidget(play_btn)
        return card

    def _play(self, audio_path):
        if not audio_path:
            QMessageBox.information(self, "Аудио",
                                    "У этого элемента нет аудиофайла.\n"
                                    "Запустите generate_content.py.")
            return
        self.controller.audio.play_audio(audio_path)