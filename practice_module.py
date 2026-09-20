import os
import tempfile
import re
import soundfile as sf
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QListWidget, QListWidgetItem,
                             QFileDialog, QMessageBox, QSplitter, QGroupBox,
                             QFormLayout, QComboBox, QInputDialog, QScrollArea,
                             QFrame)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QPixmap
from ..controllers.app_controller import AppController
from ..models.phrase import Phrase
from ..utils.debounce import debounce
from ..utils.config import CONTENT_DIR
from ..utils.logger import logger


BUTTON_MIN_HEIGHT = 44
IMAGE_W, IMAGE_H = 220, 165
VIDEO_MIN_HEIGHT = 280
LEFT_PANEL_MIN_WIDTH = 240
LEFT_PANEL_MAX_WIDTH = 380


class PracticeModule(QWidget):
    def __init__(self, controller: AppController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window

        self.current_phrase = None
        self.phrases = []
        self.current_language = 'en'
        self.recorded_file = None
        self.is_recording = False
        self._subtitle_timeline = []
        self._subtitle_timer = None

        self._build_ui()
        self.load_phrases()

    def showEvent(self, event):
        super().showEvent(event)
        if self._right_scroll is not None:
            self._right_scroll.verticalScrollBar().setValue(0)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)

        header.addWidget(QLabel("Язык:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['en', 'ar', 'zh'])
        self.lang_combo.currentTextChanged.connect(self.on_language_changed)
        header.addWidget(self.lang_combo)

        header.addStretch()

        self.import_btn = QPushButton("📥 Импортировать из уроков")
        self.import_btn.setMinimumHeight(BUTTON_MIN_HEIGHT)
        self.import_btn.clicked.connect(self.import_from_lessons)
        header.addWidget(self.import_btn)

        root.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 720])

        back_btn = QPushButton("🚪 Назад в главное меню")
        back_btn.setMinimumHeight(48)
        back_btn.clicked.connect(lambda: self.main_window.show_main_menu())
        root.addWidget(back_btn)

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMinimumWidth(LEFT_PANEL_MIN_WIDTH)
        panel.setMaximumWidth(LEFT_PANEL_MAX_WIDTH)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("📚 Сохранённые фразы")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        self.phrase_list = QListWidget()
        self.phrase_list.itemClicked.connect(self.on_phrase_selected)
        layout.addWidget(self.phrase_list, 1)

        self.btn_add = QPushButton("➕ Добавить фразу")
        self.btn_add.setMinimumHeight(BUTTON_MIN_HEIGHT)
        self.btn_add.clicked.connect(self.add_phrase)
        layout.addWidget(self.btn_add)

        self.btn_delete = QPushButton("🗑 Удалить выбранную")
        self.btn_delete.setMinimumHeight(BUTTON_MIN_HEIGHT)
        self.btn_delete.clicked.connect(self.delete_phrase)
        layout.addWidget(self.btn_delete)

        return panel

    def _build_right_panel(self) -> QWidget:
        self._right_scroll = QScrollArea()
        self._right_scroll.setWidgetResizable(True)
        self._right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._right_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_detail_group())
        layout.addWidget(self._build_exercise_group())
        layout.addWidget(self._build_video_group())
        layout.addStretch()

        self._right_scroll.setWidget(content)
        return self._right_scroll

    def _build_detail_group(self) -> QGroupBox:
        group = QGroupBox("Фраза")
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setContentsMargins(12, 16, 12, 12)
        form.setSpacing(8)

        self.text_value = QLabel("—")
        self.text_value.setWordWrap(True)
        self.text_value.setStyleSheet("font-size: 18px; font-weight: bold;")
        form.addRow("Текст:", self.text_value)

        self.trans_value = QLabel("—")
        self.trans_value.setWordWrap(True)
        self.trans_value.setStyleSheet("font-size: 16px; color: #444;")
        form.addRow("Перевод:", self.trans_value)

        self.image_label = QLabel("Нет изображения")
        self.image_label.setFixedSize(IMAGE_W, IMAGE_H)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(
            "border: 1px dashed #BDBDBD; "
            "background-color: #FAFAFA; color: #9E9E9E; font-size: 13px;")

        img_row = QHBoxLayout()
        img_row.addWidget(self.image_label)
        img_row.addStretch()
        form.addRow(img_row)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        btn_image = QPushButton("🖼 Выбрать изображение")
        btn_image.setMinimumHeight(BUTTON_MIN_HEIGHT)
        btn_image.clicked.connect(self.select_image)
        actions.addWidget(btn_image)

        btn_audio = QPushButton("🔊 Воспроизвести аудио")
        btn_audio.setMinimumHeight(BUTTON_MIN_HEIGHT)
        btn_audio.clicked.connect(self.play_audio)
        actions.addWidget(btn_audio)

        form.addRow(actions)
        return group

    def _build_exercise_group(self) -> QGroupBox:
        group = QGroupBox("Упражнения")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        row1.addWidget(QLabel("Обратный перевод:"))
        self.translate_input = QLineEdit()
        self.translate_input.setPlaceholderText("Введите перевод на иностранный...")
        self.translate_input.setMinimumHeight(BUTTON_MIN_HEIGHT)
        row1.addWidget(self.translate_input, 1)

        btn_check = QPushButton("Проверить")
        btn_check.setMinimumHeight(BUTTON_MIN_HEIGHT)
        btn_check.clicked.connect(self.check_translation)
        row1.addWidget(btn_check)
        layout.addLayout(row1)

        self.translate_result = QLabel("")
        self.translate_result.setWordWrap(True)
        self.translate_result.setStyleSheet("font-size: 15px; padding: 4px;")
        layout.addWidget(self.translate_result)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        row2.addWidget(QLabel("Пересказ (запись):"))
        self.recite_btn = QPushButton("🎙 Начать запись")
        self.recite_btn.setMinimumHeight(BUTTON_MIN_HEIGHT)
        self.recite_btn.clicked.connect(self.toggle_recording)
        row2.addWidget(self.recite_btn)

        self.recite_play_btn = QPushButton("▶ Прослушать запись")
        self.recite_play_btn.setMinimumHeight(BUTTON_MIN_HEIGHT)
        self.recite_play_btn.clicked.connect(self.play_recording)
        row2.addWidget(self.recite_play_btn)
        row2.addStretch()
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(8)
        row3.addWidget(QLabel("Аудирование:"))
        self.listen_btn = QPushButton("▶ Слушать эталон")
        self.listen_btn.setMinimumHeight(BUTTON_MIN_HEIGHT)
        self.listen_btn.clicked.connect(self.listen_audio)
        row3.addWidget(self.listen_btn)
        row3.addStretch()
        layout.addLayout(row3)

        return group

    def _build_video_group(self) -> QGroupBox:
        group = QGroupBox("Видео с субтитрами")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(8)

        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(VIDEO_MIN_HEIGHT)
        self.video_widget.setStyleSheet("background-color: #000;")
        self.video_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self._audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self._audio_output)

        layout.addWidget(self.video_widget)

        controls = QHBoxLayout()
        controls.setSpacing(8)

        btn_open_video = QPushButton("📂 Открыть видео")
        btn_open_video.setMinimumHeight(BUTTON_MIN_HEIGHT)
        btn_open_video.clicked.connect(self.open_video)
        controls.addWidget(btn_open_video)

        btn_open_sub = QPushButton("💬 Загрузить субтитры (SRT)")
        btn_open_sub.setMinimumHeight(BUTTON_MIN_HEIGHT)
        btn_open_sub.clicked.connect(self.open_subtitles)
        controls.addWidget(btn_open_sub)

        self.play_pause_btn = QPushButton("▶")
        self.play_pause_btn.setMinimumHeight(BUTTON_MIN_HEIGHT)
        self.play_pause_btn.setFixedWidth(60)
        self.play_pause_btn.clicked.connect(self.toggle_video)
        controls.addWidget(self.play_pause_btn)

        controls.addStretch()
        layout.addLayout(controls)

        self.subtitle_label = QLabel("Субтитры: —")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet(
            "font-size: 16px; background-color: #222; color: white; padding: 8px; "
            "border-radius: 6px; min-height: 24px;")
        layout.addWidget(self.subtitle_label)

        return group

    def load_phrases(self):
        user = self.controller.current_user
        if not user:
            return

        self.phrases = self.controller.db.get_phrases_for_user(
            user.id, self.current_language)
        self.phrase_list.clear()
        self.clear_details()

        if not self.phrases:
            placeholder = QListWidgetItem(
                "Список пуст.\n\n"
                "Нажмите «Добавить фразу»\n"
                "или «Импортировать из уроков».")
            placeholder.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            self.phrase_list.addItem(placeholder)
            return

        for p in self.phrases:
            text = p.text if len(p.text) <= 40 else p.text[:37] + "…"
            label = f"{text}\n{p.translation}" if p.translation else text
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, p.id)
            self.phrase_list.addItem(item)

    def on_language_changed(self, lang):
        self.current_language = lang
        self.load_phrases()

    def clear_details(self):
        self.text_value.setText("—")
        self.trans_value.setText("—")
        self.image_label.clear()
        self.image_label.setText("Нет изображения")
        self.image_label.setStyleSheet(
            "border: 1px dashed #BDBDBD; "
            "background-color: #FAFAFA; color: #9E9E9E; font-size: 13px;")
        self.translate_input.clear()
        self.translate_result.setText("")
        self.current_phrase = None

    def on_phrase_selected(self, item):
        phrase_id = item.data(Qt.ItemDataRole.UserRole)
        if phrase_id is None:
            return
        for p in self.phrases:
            if p.id == phrase_id:
                self.current_phrase = p
                self.show_phrase_details(p)
                break

    def show_phrase_details(self, phrase: Phrase):
        self.text_value.setText(phrase.text or "—")
        self.trans_value.setText(phrase.translation or "—")

        if phrase.image_path and os.path.exists(phrase.image_path):
            pixmap = QPixmap(phrase.image_path)
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(
                    IMAGE_W, IMAGE_H,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))
                self.image_label.setStyleSheet(
                    "border: 1px solid #BDBDBD; background-color: #FFFFFF;")
            else:
                self.image_label.setText("Нет изображения")
                self.image_label.setStyleSheet(
                    "border: 1px dashed #BDBDBD; background-color: #FAFAFA; "
                    "color: #9E9E9E; font-size: 13px;")
        else:
            self.image_label.setText("Нет изображения")
            self.image_label.setStyleSheet(
                "border: 1px dashed #BDBDBD; background-color: #FAFAFA; "
                "color: #9E9E9E; font-size: 13px;")

        self.translate_input.clear()
        self.translate_result.setText("")

    @debounce(200)
    def add_phrase(self):
        user = self.controller.current_user
        if not user:
            QMessageBox.warning(self, "Ошибка", "Выберите профиль")
            return

        text, ok = QInputDialog.getText(self, "Новая фраза",
                                        "Введите текст на иностранном языке:")
        if not ok or not text.strip():
            return

        trans, ok = QInputDialog.getText(self, "Перевод", "Введите перевод:")
        if not ok or not trans.strip():
            return

        self.controller.db.add_phrase(
            user.id, self.current_language, text.strip(), trans.strip())
        self.load_phrases()
        QMessageBox.information(self, "Готово", "Фраза сохранена")

    @debounce(200)
    def delete_phrase(self):
        if not self.current_phrase:
            QMessageBox.warning(self, "Ошибка", "Выберите фразу")
            return
        reply = QMessageBox.question(
            self, "Подтверждение", "Удалить фразу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.db.delete_phrase(self.current_phrase.id)
            self.load_phrases()

    @debounce(200)
    def import_from_lessons(self):
        user = self.controller.current_user
        if not user:
            QMessageBox.warning(self, "Ошибка", "Выберите профиль")
            return

        lessons = self.controller.get_lessons(self.current_language)
        if not lessons:
            QMessageBox.information(
                self, "Нет уроков",
                f"Нет уроков для языка {self.current_language.upper()}")
            return

        all_items = []
        seen = set()
        for lesson in lessons:
            for item in lesson.items:
                key = (item.text or '').strip().lower()
                if not key or key in seen:
                    continue
                seen.add(key)
                all_items.append(item)

        if not all_items:
            QMessageBox.information(self, "Пусто", "В уроках нет слов")
            return

        count, ok = QInputDialog.getInt(
            self, "Импорт из уроков",
            f"Найдено {len(all_items)} уникальных слов.\n"
            f"Сколько добавить в список фраз?",
            value=len(all_items), min=1, max=len(all_items))
        if not ok:
            return

        existing = {(p.text.strip().lower(), (p.translation or '').strip().lower())
                    for p in self.phrases}

        added = 0
        for item in all_items[:count]:
            key = (item.text.strip().lower(),
                   (item.translation or '').strip().lower())
            if key in existing:
                continue

            img_path = None
            if item.image:
                candidate = CONTENT_DIR / item.image
                if candidate.exists():
                    img_path = str(candidate)

            try:
                self.controller.db.add_phrase(
                    user.id, self.current_language,
                    item.text, item.translation or '',
                    audio_path=item.audio,
                    image_path=img_path)
                added += 1
            except Exception as e:
                logger.error(f"Ошибка импорта фразы: {e}")

        self.load_phrases()
        QMessageBox.information(
            self, "Готово",
            f"Импортировано {added} фраз (пропущено {count - added})")

    def select_image(self):
        if not self.current_phrase:
            QMessageBox.warning(self, "Ошибка", "Выберите фразу")
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение",
            "", "Изображения (*.png *.jpg *.jpeg *.bmp *.webp)")
        if file_path:
            self.current_phrase.image_path = file_path
            self.controller.db.update_phrase(self.current_phrase)
            self.show_phrase_details(self.current_phrase)

    def play_audio(self):
        if not self.current_phrase:
            QMessageBox.information(self, "Информация", "Выберите фразу")
            return
        if not self.current_phrase.audio_path:
            QMessageBox.information(self, "Информация",
                                    "У этой фразы нет аудио")
            return
        if os.path.exists(self.current_phrase.audio_path):
            self.controller.audio.play_audio(self.current_phrase.audio_path)
        else:
            QMessageBox.warning(
                self, "Ошибка",
                f"Аудиофайл не найден:\n{self.current_phrase.audio_path}")

    def check_translation(self):
        if not self.current_phrase:
            QMessageBox.warning(self, "Ошибка", "Выберите фразу")
            return
        user_trans = self.translate_input.text().strip().lower()
        correct = (self.current_phrase.text or '').lower()
        if user_trans and user_trans == correct:
            self.translate_result.setText("✅ Правильно!")
            self.translate_result.setStyleSheet("color: #2E7D32; font-size: 15px;")
            self.controller.db.update_practice(self.current_phrase.id)
        else:
            self.translate_result.setText(
                f"❌ Неправильно. Правильный ответ: {self.current_phrase.text}")
            self.translate_result.setStyleSheet("color: #C62828; font-size: 15px;")

    def toggle_recording(self):
        if not self.current_phrase:
            QMessageBox.warning(self, "Ошибка", "Выберите фразу")
            return

        if self.is_recording:
            self.controller.audio.stop_recording()
            self.is_recording = False
            self.recite_btn.setText("🎙 Начать запись")

            if self.controller.audio.recorded_data is not None:
                try:
                    temp_dir = tempfile.gettempdir()
                    self.recorded_file = os.path.join(
                        temp_dir, f"practice_{self.current_phrase.id}.wav")
                    sf.write(self.recorded_file,
                             self.controller.audio.recorded_data, 44100)
                    self.current_phrase.audio_path = self.recorded_file
                    self.controller.db.update_phrase(self.current_phrase)
                    QMessageBox.information(self, "Готово", "Запись сохранена")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка",
                                         f"Не удалось сохранить запись: {e}")
        else:
            try:
                self.controller.audio.start_recording()
                self.is_recording = True
                self.recite_btn.setText("⏹ Остановить запись")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка",
                                     f"Не удалось начать запись: {e}")

    def play_recording(self):
        if self.recorded_file and os.path.exists(self.recorded_file):
            self.controller.audio.play_audio(self.recorded_file)
        else:
            QMessageBox.warning(self, "Ошибка",
                                "Нет сохранённой записи.\n"
                                "Сначала запишите пересказ.")

    def listen_audio(self):
        if self.current_phrase and self.current_phrase.audio_path:
            self.play_audio()
        else:
            QMessageBox.information(self, "Информация",
                                    "У этой фразы нет эталонного аудио")

    def open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите видео",
            "", "Видео (*.mp4 *.avi *.mkv *.mov *.wmv)")
        if file_path:
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.media_player.play()
            self.play_pause_btn.setText("⏸")

    def toggle_video(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_pause_btn.setText("▶")
        else:
            self.media_player.play()
            self.play_pause_btn.setText("⏸")

    def open_subtitles(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл субтитров (SRT)", "", "SRT файлы (*.srt)")
        if file_path:
            self.load_subtitles(file_path)

    def load_subtitles(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            blocks = re.split(r'\n\s*\n', content.strip())
            self._subtitle_timeline = []
            for block in blocks:
                lines = block.split('\n')
                if len(lines) >= 3:
                    time_line = lines[1]
                    text = ' '.join(lines[2:]).strip()
                    m = re.search(
                        r'(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*'
                        r'(\d{2}:\d{2}:\d{2}[,.]\d{3})', time_line)
                    if m:
                        start = self._time_to_seconds(m.group(1).replace(',', '.'))
                        end = self._time_to_seconds(m.group(2).replace(',', '.'))
                        self._subtitle_timeline.append((start, end, text))

            if self._subtitle_timer is None:
                self._subtitle_timer = QTimer()
                self._subtitle_timer.timeout.connect(self._update_subtitle)
            self._subtitle_timer.start(100)

            QMessageBox.information(
                self, "Субтитры",
                f"Загружено {len(self._subtitle_timeline)} субтитров")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Не удалось загрузить субтитры: {e}")
            logger.error(f"Ошибка загрузки субтитров: {e}", exc_info=True)

    @staticmethod
    def _time_to_seconds(time_str):
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = parts
            s = s.replace('.', ':').split(':')
            sec = float(s[0]) + (float(s[1]) / 1000.0 if len(s) == 2 else 0)
            return int(h) * 3600 + int(m) * 60 + sec
        return 0.0

    def _update_subtitle(self):
        if self.media_player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            return
        pos = self.media_player.position() / 1000.0
        for start, end, text in self._subtitle_timeline:
            if start <= pos <= end:
                self.subtitle_label.setText(f"Субтитры: {text}")
                return
        self.subtitle_label.setText("Субтитры: —")

    def cleanup(self):
        if hasattr(self, 'media_player'):
            self.media_player.stop()
        if self.recorded_file and os.path.exists(self.recorded_file):
            try:
                os.remove(self.recorded_file)
            except Exception:
                pass