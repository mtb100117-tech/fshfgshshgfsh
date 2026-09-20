import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                             QListWidget, QFrame, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from ..controllers.app_controller import AppController
from ..utils.rtl_helper import set_rtl_for_label, set_ltr_for_label, set_cjk_for_label
from ..utils.config import CONTENT_DIR
from ..utils.logger import logger


class ReadingModule(QWidget):
    """Чтение с методикой «аудио сначала».

    Клик по слову в списке и кнопки воспроизведения работают мгновенно —
    без @debounce. Debounce применяется только в родительском контроле
    для антибрутфорса PIN.
    """

    DIALOG_PAUSE_MS = 2500

    def __init__(self, controller: AppController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window
        self.current_lesson = None
        self.current_item_index = 0
        self.current_lesson_index = 0
        self.all_lessons = []

        self.text_visible = False
        self.role_mode = 'all'

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(12, 12, 12, 12)
        self.layout().setSpacing(8)

        logger.debug("ReadingModule инициализирован")

        self.top_layout = QHBoxLayout()
        self.level_label = QLabel("Уровень: 0")
        self.level_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.top_layout.addWidget(self.level_label)
        self.top_layout.addStretch()
        self.progress_label = QLabel("⭐ 0/0")
        self.progress_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.top_layout.addWidget(self.progress_label)
        self.layout().addLayout(self.top_layout)

        self.lang_layout = QHBoxLayout()
        self.lang_btns = {}
        for lang in ['en', 'ar', 'zh']:
            btn = QPushButton(lang.upper())
            btn.clicked.connect(lambda checked, l=lang: self.load_lesson(l))
            self.lang_layout.addWidget(btn)
            self.lang_btns[lang] = btn
        self.layout().addLayout(self.lang_layout)

        self.mode_layout = QHBoxLayout()
        self.toggle_text_btn = QPushButton("👁 Показать текст")
        self.toggle_text_btn.setMinimumHeight(40)
        self.toggle_text_btn.clicked.connect(self.toggle_text)
        self.mode_layout.addWidget(self.toggle_text_btn)

        self.replay_btn = QPushButton("🔊 Повторить")
        self.replay_btn.setMinimumHeight(40)
        self.replay_btn.clicked.connect(self.replay_current)
        self.mode_layout.addWidget(self.replay_btn)

        self.mode_layout.addStretch()
        self.layout().addLayout(self.mode_layout)

        self.role_layout = QHBoxLayout()
        self.role_label = QLabel("Роль:")
        self.role_layout.addWidget(self.role_label)
        self.role_combo = QComboBox()
        self.role_combo.addItem("Слушаю все реплики", 'all')
        self.role_combo.currentIndexChanged.connect(self._on_role_changed)
        self.role_layout.addWidget(self.role_combo)
        self.role_layout.addStretch()
        self.layout().addLayout(self.role_layout)
        self._set_role_visible(False)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.layout().addWidget(self.content_widget)

        self.dialog_widget = QWidget()
        self.dialog_layout = QVBoxLayout(self.dialog_widget)
        self.dialog_widget.hide()

        self.word_widget = QWidget()
        self.word_layout = QHBoxLayout(self.word_widget)
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 200)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: white;")
        self.word_layout.addWidget(self.image_label)
        self.text_display = QLabel("")
        self.text_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_display.setWordWrap(True)
        self.text_display.setStyleSheet("font-size: 24px; padding: 20px; color: #333;")
        self.word_layout.addWidget(self.text_display)
        self.content_layout.addWidget(self.word_widget)
        self.content_layout.addWidget(self.dialog_widget)

        self.word_list = QListWidget()
        self.word_list.itemClicked.connect(self.on_word_clicked)
        self.content_layout.addWidget(self.word_list)

        self.controls = QHBoxLayout()
        self.play_btn = QPushButton("▶ Воспроизвести всё")
        self.play_btn.setMinimumHeight(44)
        self.play_btn.clicked.connect(lambda: self.play_all())
        self.controls.addWidget(self.play_btn)
        self.next_lesson_btn = QPushButton("Следующий урок →")
        self.next_lesson_btn.setMinimumHeight(44)
        self.next_lesson_btn.clicked.connect(self.next_lesson)
        self.controls.addWidget(self.next_lesson_btn)
        self.back_btn = QPushButton("Назад")
        self.back_btn.setMinimumHeight(44)
        self.back_btn.clicked.connect(lambda: self.main_window.show_main_menu())
        self.controls.addWidget(self.back_btn)
        self.layout().addLayout(self.controls)

        self.current_lang = 'en'
        self.play_timer = QTimer()
        self.play_timer.setSingleShot(True)
        self.play_timer.timeout.connect(self._play_next_audio)
        self._play_queue = []
        self._play_index = 0
        self._dialog_next_idx = 0

    def toggle_text(self):
        self.text_visible = not self.text_visible
        self.toggle_text_btn.setText(
            "🙈 Скрыть текст" if self.text_visible else "👁 Показать текст")
        self.update_display()

    def replay_current(self):
        if not self.current_lesson:
            return
        if self.current_lesson.is_dialog and self.current_lesson.dialog:
            if 0 <= self.current_item_index < len(self.current_lesson.dialog):
                item = self.current_lesson.dialog[self.current_item_index]
                if item.audio and os.path.exists(item.audio):
                    self.controller.audio.play_audio(item.audio)
        else:
            if 0 <= self.current_item_index < len(self.current_lesson.items):
                item = self.current_lesson.items[self.current_item_index]
                if item.audio and os.path.exists(item.audio):
                    self.controller.audio.play_audio(item.audio)

    def _set_role_visible(self, visible: bool):
        for i in range(self.role_layout.count()):
            w = self.role_layout.itemAt(i).widget()
            if w:
                w.setVisible(visible)

    def _rebuild_role_choices(self):
        self.role_combo.blockSignals(True)
        self.role_combo.clear()
        self.role_combo.addItem("Слушаю все реплики", 'all')
        if self.current_lesson and self.current_lesson.is_dialog:
            seen = []
            for line in self.current_lesson.dialog:
                sp = (line.speaker or '').strip()
                if sp and sp not in seen:
                    seen.append(sp)
            for sp in seen:
                self.role_combo.addItem(f"Я — {sp}", sp)
        self.role_combo.blockSignals(False)

    def _on_role_changed(self, index):
        self.role_mode = self.role_combo.currentData() or 'all'
        logger.info(f"Роль в диалоге: {self.role_mode}")
        self.update_display()

    def showEvent(self, event):
        # При первом показе загружаем урок языка, который был выбран
        # в прошлый раз (self.current_lang), а не жёстко 'en'.
        if self.current_lesson is None:
            self.load_lesson(self.current_lang or 'en')
        super().showEvent(event)

    def load_lesson(self, lang):
        if not isinstance(lang, str):
            lang = 'en'
        self.current_lang = lang
        self.all_lessons = self.controller.get_lessons(lang)
        logger.info(f"Загрузка уроков для языка {lang}: {len(self.all_lessons)}")

        if not self.all_lessons:
            self.text_display.setText(f"Нет уроков для языка {lang}")
            self.word_list.clear()
            self.image_label.clear()
            self.level_label.setText("Уровень: -")
            self.progress_label.setText("⭐ 0/0")
            self.current_lesson = None
            return

        self.current_lesson_index = 0
        self._set_lesson(self.current_lesson_index)

    def _set_lesson(self, index):
        if index >= len(self.all_lessons):
            QMessageBox.information(self, "Информация", "Все уроки пройдены!")
            return

        self.current_lesson_index = index
        self.current_lesson = self.all_lessons[index]
        self.current_item_index = 0
        self.text_visible = False
        self.toggle_text_btn.setText("👁 Показать текст")

        logger.debug(f"Урок {index + 1}/{len(self.all_lessons)}: "
                     f"{self.current_lesson.title}")

        if self.current_lesson.is_dialog:
            self._rebuild_role_choices()
            self._set_role_visible(True)
        else:
            self._set_role_visible(False)

        self.update_display()
        self.update_progress()

        if index == len(self.all_lessons) - 1:
            self.next_lesson_btn.setText("Завершить")
        else:
            self.next_lesson_btn.setText("Следующий урок →")

        QTimer.singleShot(200, self._play_first_audio)

    def _play_first_audio(self):
        if not self.current_lesson:
            return
        if self.current_lesson.is_dialog and self.current_lesson.dialog:
            self._dialog_next_idx = 0
            self._play_next_audio()
        elif self.current_lesson.items:
            it = self.current_lesson.items[0]
            if it.audio and os.path.exists(it.audio):
                self.controller.audio.play_audio(it.audio)

    def next_lesson(self):
        if self.current_lesson and self.current_lesson.is_dialog:
            self.complete_lesson()
        self._set_lesson(self.current_lesson_index + 1)

    def complete_lesson(self):
        if not self.current_lesson or not self.controller.current_user:
            return
        progress = self.controller.get_progress(self.current_lesson.id)
        if not progress or not progress.get('completed', False):
            self.controller.set_progress(self.current_lesson.id, 1, True, 0, 0)
            self.update_progress()
            QMessageBox.information(self, "Отлично!",
                                    f"Урок '{self.current_lesson.title}' завершён!")

    def _format_word_with_pinyin(self, text: str, pinyin: str) -> str:
        if self.current_lang == 'zh' and pinyin:
            return f"{text}  ({pinyin})"
        return text

    def _apply_language_style(self, label):
        if self.current_lang == 'ar':
            set_rtl_for_label(label)
        elif self.current_lang == 'zh':
            set_cjk_for_label(label)
        else:
            set_ltr_for_label(label)

    def update_display(self):
        if not self.current_lesson:
            return

        if self.current_lesson.is_dialog and self.current_lesson.dialog:
            self.word_widget.hide()
            self.dialog_widget.show()
            self.word_list.hide()

            for i in reversed(range(self.dialog_layout.count())):
                w = self.dialog_layout.itemAt(i).widget()
                if w:
                    w.deleteLater()

            for idx, item in enumerate(self.current_lesson.dialog):
                frame = QFrame()
                frame.setFrameShape(QFrame.Shape.Box)
                frame.setFrameShadow(QFrame.Shadow.Raised)
                layout = QHBoxLayout(frame)

                speaker_label = QLabel(f"{item.speaker}: ")
                speaker_label.setStyleSheet("font-weight: bold;")
                layout.addWidget(speaker_label)

                if self.text_visible:
                    text_to_show = item.text
                    if self.current_lang == 'zh' and item.pinyin:
                        text_to_show = f"{item.text}\n({item.pinyin})"
                    text_label = QLabel(text_to_show)
                    if self.current_lang == 'zh':
                        set_cjk_for_label(text_label)
                    elif self.current_lang == 'ar':
                        set_rtl_for_label(text_label)
                else:
                    text_label = QLabel("🔊 нажмите ▶ или «Показать текст»")
                    text_label.setStyleSheet("color: #888; font-style: italic;")
                text_label.setWordWrap(True)
                layout.addWidget(text_label)

                play_btn = QPushButton("▶")
                play_btn.setFixedSize(32, 32)
                play_btn.clicked.connect(lambda checked, i=idx: self.play_dialog_line(i))
                layout.addWidget(play_btn)

                if item.translation and self.text_visible:
                    trans_label = QLabel(f"({item.translation})")
                    trans_label.setStyleSheet("color: gray;")
                    layout.addWidget(trans_label)

                self.dialog_layout.addWidget(frame)

            self.level_label.setText(
                f"Уровень: {self.current_lesson.level}  —  {self.current_lesson.title}")
            return

        self.word_widget.show()
        self.dialog_widget.hide()
        self.word_list.show()

        items = self.current_lesson.items
        if not items:
            self.text_display.setText("В уроке нет элементов")
            self.image_label.clear()
            return

        item = items[self.current_item_index]
        self._apply_language_style(self.text_display)

        if self.text_visible:
            self.text_display.setText(
                self._format_word_with_pinyin(item.text, item.pinyin))
        else:
            self.text_display.setText("🔊 Слушайте аудио")

        image_path = CONTENT_DIR / item.image if item.image else None
        if image_path and image_path.exists():
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                self.image_label.setPixmap(
                    pixmap.scaled(200, 200,
                                  Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation))
            else:
                self.image_label.clear()
        else:
            self.image_label.clear()

        self.word_list.clear()
        for it in items:
            self.word_list.addItem(
                self._format_word_with_pinyin(it.text, it.pinyin))

        self.level_label.setText(
            f"Уровень: {self.current_lesson.level}  —  {self.current_lesson.title}")

    def play_dialog_line(self, idx):
        if self.current_lesson and idx < len(self.current_lesson.dialog):
            item = self.current_lesson.dialog[idx]
            if item.audio and os.path.exists(item.audio):
                self.controller.audio.play_audio(item.audio)

    def update_progress(self):
        if not self.current_lesson or not self.controller.current_user:
            return
        progress = self.controller.get_progress(self.current_lesson.id)
        if progress:
            stars = progress.get('stars', 0)
            completed = progress.get('completed', False)
            self.progress_label.setText(
                f"⭐ {stars} звёзд" if completed else "⭐ 0/1")
        else:
            self.progress_label.setText("⭐ 0/1")

    def on_word_clicked(self, item):
        """Клик по слову в списке. БЕЗ @debounce — каждый клик важен."""
        idx = self.word_list.row(item)
        if self.current_lesson and idx < len(self.current_lesson.items):
            lesson_item = self.current_lesson.items[idx]
            self.current_item_index = idx
            if lesson_item.audio and os.path.exists(lesson_item.audio):
                self.controller.audio.play_audio(lesson_item.audio)
            if lesson_item.translation:
                self.text_display.setToolTip(lesson_item.translation)
            self.update_display()

    def play_all(self):
        """БЕЗ @debounce — повторный клик должен перезапустить очередь."""
        if not self.current_lesson:
            return

        if self.current_lesson.is_dialog and self.current_lesson.dialog:
            self._dialog_next_idx = 0
            self._play_next_audio()
            return

        self._play_queue = [it.audio for it in self.current_lesson.items
                            if it.audio and os.path.exists(it.audio)]
        if not self._play_queue:
            return
        self._play_index = 0
        self._play_next_audio()

    def _play_next_audio(self):
        if not self.current_lesson:
            return

        if self.current_lesson.is_dialog and self.current_lesson.dialog:
            dialog = self.current_lesson.dialog

            while self._dialog_next_idx < len(dialog):
                item = dialog[self._dialog_next_idx]
                if self.role_mode != 'all' and (item.speaker or '') == self.role_mode:
                    self._dialog_next_idx += 1
                    continue
                break

            if self._dialog_next_idx >= len(dialog):
                return

            item = dialog[self._dialog_next_idx]
            self.current_item_index = self._dialog_next_idx
            self.update_display()
            if item.audio and os.path.exists(item.audio):
                self.controller.audio.play_audio(item.audio)

            self._dialog_next_idx += 1
            if self._dialog_next_idx < len(dialog):
                self.play_timer.start(self.DIALOG_PAUSE_MS)
            return

        if self._play_index >= len(self._play_queue):
            self.word_list.setCurrentRow(-1)
            return

        audio_file = self._play_queue[self._play_index]
        self.controller.audio.play_audio(audio_file)

        for i, it in enumerate(self.current_lesson.items):
            if it.audio == audio_file:
                self.word_list.setCurrentRow(i)
                self.current_item_index = i
                self.update_display()
                break

        self._play_index += 1
        self.play_timer.start(3000)