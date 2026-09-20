from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QScrollArea, QFrame)
from PyQt6.QtCore import Qt
from ..controllers.app_controller import AppController


class MainMenu(QWidget):
    def __init__(self, controller: AppController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.layout().addWidget(self.scroll)

        self.inner = QWidget()
        self.inner_layout = QVBoxLayout(self.inner)
        self.inner_layout.setContentsMargins(20, 20, 20, 20)
        self.inner_layout.setSpacing(12)
        self.scroll.setWidget(self.inner)

        self.title_label = QLabel("Главное меню")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; padding: 12px;")
        self.title_label.setWordWrap(True)
        self.inner_layout.addWidget(self.title_label)

        # Алфавит — первое, что видит ребёнок
        self.alphabet_btn = QPushButton("🔤 Алфавит (3 языка рядом)")
        self.alphabet_btn.setMinimumHeight(56)
        self.alphabet_btn.setStyleSheet(
            "font-size: 18px; font-weight: bold; background-color: #FF9800;")
        self.alphabet_btn.clicked.connect(lambda: self.main_window.show_alphabet())
        self.inner_layout.addWidget(self.alphabet_btn)

        self.reading_btn = QPushButton("📖 Чтение")
        self.reading_btn.setMinimumHeight(48)
        self.reading_btn.clicked.connect(lambda: self.main_window.show_reading())
        self.inner_layout.addWidget(self.reading_btn)

        self.speaking_btn = QPushButton("🎤 Разговорная речь")
        self.speaking_btn.setMinimumHeight(48)
        self.speaking_btn.clicked.connect(lambda: self.main_window.show_speaking())
        self.inner_layout.addWidget(self.speaking_btn)

        self.practice_btn = QPushButton("📝 Практика")
        self.practice_btn.setMinimumHeight(48)
        self.practice_btn.clicked.connect(lambda: self.main_window.show_practice())
        self.inner_layout.addWidget(self.practice_btn)

        self.flashcards_btn = QPushButton("🖼 Карточки")
        self.flashcards_btn.setMinimumHeight(48)
        self.flashcards_btn.clicked.connect(lambda: self.main_window.show_flashcards())
        self.inner_layout.addWidget(self.flashcards_btn)

        self.library_btn = QPushButton("📚 Библиотека книг")
        self.library_btn.setMinimumHeight(48)
        self.library_btn.setStyleSheet(
            "background-color: #7B1FA2; color: white; font-size: 16px; "
            "font-weight: bold;")
        self.library_btn.clicked.connect(lambda: self.main_window.show_library())
        self.inner_layout.addWidget(self.library_btn)

        self.achievements_btn = QPushButton("🏆 Достижения")
        self.achievements_btn.setMinimumHeight(48)
        self.achievements_btn.clicked.connect(lambda: self.main_window.show_achievements())
        self.inner_layout.addWidget(self.achievements_btn)

        games_label = QLabel("🎮 Игры")
        games_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        games_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px;")
        self.inner_layout.addWidget(games_label)

        games_row1 = QHBoxLayout()
        games_row1.setSpacing(10)
        self.memory_btn = QPushButton("🔍 Найди пару")
        self.memory_btn.setMinimumHeight(48)
        self.memory_btn.clicked.connect(lambda: self.main_window.show_memory())
        games_row1.addWidget(self.memory_btn)

        self.quiz_btn = QPushButton("🎧 Аудио-викторина")
        self.quiz_btn.setMinimumHeight(48)
        self.quiz_btn.clicked.connect(lambda: self.main_window.show_audio_quiz())
        games_row1.addWidget(self.quiz_btn)
        self.inner_layout.addLayout(games_row1)

        games_row2 = QHBoxLayout()
        games_row2.setSpacing(10)
        self.build_btn = QPushButton("🔤 Собери слово")
        self.build_btn.setMinimumHeight(48)
        self.build_btn.clicked.connect(lambda: self.main_window.show_build_word())
        games_row2.addWidget(self.build_btn)

        self.phrase_btn = QPushButton("💬 Собери фразу")
        self.phrase_btn.setMinimumHeight(48)
        self.phrase_btn.clicked.connect(lambda: self.main_window.show_build_phrase())
        games_row2.addWidget(self.phrase_btn)
        self.inner_layout.addLayout(games_row2)

        self.exit_btn = QPushButton("🚪 Выйти из профиля")
        self.exit_btn.setMinimumHeight(48)
        self.exit_btn.clicked.connect(lambda: self.main_window.show_profile_selector())
        self.inner_layout.addWidget(self.exit_btn)

        self.inner_layout.addStretch()

    def showEvent(self, event):
        if self.controller.current_user:
            self.title_label.setText(
                f"Привет, {self.controller.current_user.name}! 👋")
        else:
            self.title_label.setText("Главное меню")
        super().showEvent(event)