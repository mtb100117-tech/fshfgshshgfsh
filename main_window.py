import sys
from PyQt6.QtWidgets import (QMainWindow, QStackedWidget, QMessageBox,
                             QApplication, QStatusBar, QLabel)
from PyQt6.QtCore import Qt
from ..controllers.app_controller import AppController
from ..utils.session_timer import SessionTimer
from ..utils.logger import logger
from .profile_selector import ProfileSelector
from .parent_control import ParentControl
from .reading_module import ReadingModule
from .speaking_module import SpeakingModule
from .practice_module import PracticeModule
from .flashcards_module import FlashcardsModule
from .achievements_module import AchievementsModule
from .alphabet_module import AlphabetModule
from .library_module import LibraryModule
from .games.memory_game import MemoryGame
from .games.audio_quiz import AudioQuiz
from .games.build_word import BuildWord
from .games.build_phrase import BuildPhrase
from .main_menu import MainMenu


class MainWindow(QMainWindow):
    MIN_WIDTH = 820
    MIN_HEIGHT = 560
    MAX_WIDTH = 1280
    MAX_HEIGHT = 900
    SCREEN_MARGIN = 40

    def __init__(self, controller: AppController):
        super().__init__()
        self.controller = controller

        self.setWindowTitle("Обучение языкам")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Счётчик времени сессии
        self.session_timer = SessionTimer(self)
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.time_label = QLabel("Сессия: 00:00")
        status_bar.addPermanentWidget(self.time_label)
        self.session_timer.tick.connect(self._on_session_tick)

        # Экраны
        self.profile_selector = ProfileSelector(self.controller, self)
        self.parent_control = ParentControl(self.controller, self)
        self.main_menu = MainMenu(self.controller, self)
        self.alphabet_module = AlphabetModule(self.controller, self)
        self.reading_module = ReadingModule(self.controller, self)
        self.speaking_module = SpeakingModule(self.controller, self)
        self.practice_module = PracticeModule(self.controller, self)
        self.flashcards_module = FlashcardsModule(self.controller, self)
        self.library_module = LibraryModule(self.controller, self)
        self.achievements_module = AchievementsModule(self.controller, self)
        self.memory_game = MemoryGame(self.controller, self)
        self.audio_quiz = AudioQuiz(self.controller, self)
        self.build_word = BuildWord(self.controller, self)
        self.build_phrase = BuildPhrase(self.controller, self)

        self.stack.addWidget(self.profile_selector)    # 0
        self.stack.addWidget(self.parent_control)      # 1
        self.stack.addWidget(self.main_menu)           # 2
        self.stack.addWidget(self.alphabet_module)     # 3
        self.stack.addWidget(self.reading_module)      # 4
        self.stack.addWidget(self.speaking_module)     # 5
        self.stack.addWidget(self.practice_module)     # 6
        self.stack.addWidget(self.flashcards_module)   # 7
        self.stack.addWidget(self.library_module)      # 8
        self.stack.addWidget(self.achievements_module) # 9
        self.stack.addWidget(self.memory_game)         # 10
        self.stack.addWidget(self.audio_quiz)          # 11
        self.stack.addWidget(self.build_word)          # 12
        self.stack.addWidget(self.build_phrase)        # 13

        self._fit_to_screen()
        self.show_profile_selector()
        self.controller.user_changed.connect(self.on_user_changed)
        self.session_timer.start()

    def _on_session_tick(self, elapsed_sec: int, need_reminder: bool):
        self.time_label.setText(f"Сессия: {self.session_timer.elapsed_text()}")
        if need_reminder:
            QMessageBox.information(
                self, "Пора отдохнуть",
                "Ты уже занимаешься больше 15 минут.\n"
                "Сделай паузу, разомнись, попей воды — и возвращайся! 🌟")

    def _fit_to_screen(self):
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            self.setGeometry(100, 100, self.MIN_WIDTH, self.MIN_HEIGHT)
            return
        available = screen.availableGeometry()
        w = min(self.MAX_WIDTH, 1000, available.width() - self.SCREEN_MARGIN)
        h = min(self.MAX_HEIGHT, 700, available.height() - self.SCREEN_MARGIN)
        w = max(w, min(self.MIN_WIDTH, available.width()))
        h = max(h, min(self.MIN_HEIGHT, available.height()))
        x = available.x() + (available.width() - w) // 2
        y = available.y() + (available.height() - h) // 2
        self.setGeometry(x, y, w, h)
        self.setMinimumSize(min(self.MIN_WIDTH, available.width()),
                            min(self.MIN_HEIGHT, available.height()))

    def show_profile_selector(self):
        self.stack.setCurrentWidget(self.profile_selector)

    def show_parent_control(self):
        self.stack.setCurrentWidget(self.parent_control)

    def show_main_menu(self):
        self.stack.setCurrentWidget(self.main_menu)

    def show_alphabet(self):
        self.stack.setCurrentWidget(self.alphabet_module)

    def show_reading(self):
        self.stack.setCurrentWidget(self.reading_module)

    def show_speaking(self):
        self.stack.setCurrentWidget(self.speaking_module)

    def show_practice(self):
        self.stack.setCurrentWidget(self.practice_module)

    def show_flashcards(self):
        self.stack.setCurrentWidget(self.flashcards_module)

    def show_library(self):
        self.stack.setCurrentWidget(self.library_module)

    def show_achievements(self):
        self.stack.setCurrentWidget(self.achievements_module)

    def show_memory(self):
        self.stack.setCurrentWidget(self.memory_game)

    def show_audio_quiz(self):
        self.stack.setCurrentWidget(self.audio_quiz)

    def show_build_word(self):
        self.stack.setCurrentWidget(self.build_word)

    def show_build_phrase(self):
        self.stack.setCurrentWidget(self.build_phrase)

    def on_user_changed(self, user):
        if user is None:
            self.show_profile_selector()
        else:
            self.show_main_menu()

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Выход", "Ты уверен, что хочешь выйти?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.session_timer.stop()
            self.controller.cleanup()
            event.accept()
        else:
            event.ignore()