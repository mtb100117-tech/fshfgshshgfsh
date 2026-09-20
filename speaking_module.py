from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QProgressBar, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt
from ..controllers.app_controller import AppController


class SpeakingModule(QWidget):
    """Разговорная речь: эталон, запись, прослушка.

    Все кнопки работают мгновенно, без @debounce — toggle_recording
    должен переключаться на каждый клик, а не ждать 200 мс.
    """

    LANGUAGES = [
        ('en', '🇬🇧 English'),
        ('ar', '🇸🇦 العربية'),
        ('zh', '🇨🇳 中文'),
    ]

    def __init__(self, controller: AppController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window
        self.current_language = 'en'

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(12, 12, 12, 12)
        self.layout().setSpacing(10)

        self.label = QLabel("🎤 Разговорная речь")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 8px;")
        self.layout().addWidget(self.label)

        # Выбор языка
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Язык:"))
        self.lang_combo = QComboBox()
        for code, name in self.LANGUAGES:
            self.lang_combo.addItem(name, code)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        self.layout().addLayout(lang_layout)

        self.play_btn = QPushButton("▶ Прослушать эталон")
        self.play_btn.setMinimumHeight(44)
        self.play_btn.clicked.connect(self.play_example)
        self.layout().addWidget(self.play_btn)

        self.volume_bar = QProgressBar()
        self.volume_bar.setRange(0, 100)
        self.volume_bar.setValue(0)
        self.layout().addWidget(self.volume_bar)

        self.record_btn = QPushButton("🎙 Запись")
        self.record_btn.setMinimumHeight(44)
        self.record_btn.clicked.connect(self.toggle_recording)
        self.layout().addWidget(self.record_btn)

        self.play_record_btn = QPushButton("▶ Прослушать запись")
        self.play_record_btn.setMinimumHeight(44)
        self.play_record_btn.clicked.connect(self.play_recorded)
        self.layout().addWidget(self.play_record_btn)

        self.back_btn = QPushButton("Назад")
        self.back_btn.setMinimumHeight(44)
        self.back_btn.clicked.connect(lambda: self.main_window.show_main_menu())
        self.layout().addWidget(self.back_btn)

        self.mic_available = self.controller.audio.is_microphone_available()
        if not self.mic_available:
            self.record_btn.setEnabled(False)
            self.record_btn.setText("Микрофон недоступен")
            QMessageBox.information(self, "Микрофон",
                                    "Микрофон не обнаружен. Запись недоступна.")

        self.controller.audio.volume_updated.connect(self.update_volume)
        self.is_recording = False

    def _on_language_changed(self, index):
        code = self.lang_combo.currentData()
        if code:
            self.current_language = code

    def play_example(self):
        """Проигрывает эталонное аудио ТЕКУЩЕГО языка.

        Берёт первый урок выбранного языка, пропускает алфавит
        (там короткие слоги, не фразы для повторения), и озвучивает
        первый элемент тематического урока.
        """
        lessons = self.controller.get_lessons(self.current_language)
        for lesson in lessons:
            if lesson.is_dialog:
                continue
            if lesson.id.endswith('_alphabet'):
                continue
            for item in lesson.items:
                if item.audio:
                    self.controller.audio.play_audio(item.audio)
                    return
        QMessageBox.information(
            self, "Нет аудио",
            f"Нет эталонного аудио для языка {self.current_language.upper()}.")

    def toggle_recording(self):
        """БЕЗ @debounce — иначе быстрое «старт-стоп» инвертируется."""
        if not self.mic_available:
            return
        if self.is_recording:
            self.controller.audio.stop_recording()
            self.record_btn.setText("🎙 Запись")
            self.is_recording = False
        else:
            try:
                self.controller.audio.start_recording()
                self.record_btn.setText("⏹ Остановить")
                self.is_recording = True
            except Exception as e:
                self.record_btn.setEnabled(False)
                self.record_btn.setText("Ошибка микрофона")
                QMessageBox.critical(self, "Ошибка",
                                     f"Не удалось начать запись: {e}")

    def play_recorded(self):
        self.controller.audio.play_recorded()

    def update_volume(self, value):
        self.volume_bar.setValue(int(value * 100))