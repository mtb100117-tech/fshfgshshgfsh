from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout, QFrame
from PyQt6.QtCore import Qt
from ..controllers.app_controller import AppController


class AchievementsModule(QWidget):
    def __init__(self, controller: AppController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window
        self.setLayout(QVBoxLayout())

        self.title = QLabel("🏆 Ваши достижения")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 28px; font-weight: bold; padding: 20px; color: #FF9800;")
        self.layout().addWidget(self.title)

        self.grid = QGridLayout()
        self.layout().addLayout(self.grid)

        self.back_btn = QPushButton("🚪 В главное меню")
        self.back_btn.clicked.connect(lambda: self.main_window.show_main_menu())
        self.layout().addWidget(self.back_btn)

        self.achievements_def = {
            "first_lesson": {"icon": "🌟", "title": "Первый шаг", "desc": "Пройти 1 урок"},
            "five_lessons": {"icon": "🚀", "title": "Ученик", "desc": "Пройти 5 уроков"},
            "ten_lessons": {"icon": "👑", "title": "Знаток", "desc": "Пройти 10 уроков"},
            "no_mistakes": {"icon": "💎", "title": "Идеально", "desc": "Пройти урок без ошибок"},
        }

    def showEvent(self, event):
        self.load_achievements()
        super().showEvent(event)

    def load_achievements(self):
        # Очистка сетки
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if not self.controller.current_user:
            return

        # Сначала проверяем и разблокируем новые достижения
        self.controller.check_and_unlock_achievements(self.controller.current_user.id)
        unlocked = self.controller.db.get_achievements(self.controller.current_user.id)

        row, col = 0, 0
        for ach_id, data in self.achievements_def.items():
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.Box)
            frame.setFrameShadow(QFrame.Shadow.Raised)
            
            layout = QVBoxLayout(frame)
            
            icon = QLabel(data["icon"])
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setStyleSheet("font-size: 48px;")
            layout.addWidget(icon)
            
            title = QLabel(data["title"])
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setStyleSheet("font-size: 18px; font-weight: bold;")
            layout.addWidget(title)
            
            desc = QLabel(data["desc"])
            desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc.setStyleSheet("font-size: 14px; color: #666;")
            layout.addWidget(desc)

            if ach_id in unlocked:
                frame.setStyleSheet("background-color: #E8F5E9; border: 2px solid #4CAF50; border-radius: 10px; padding: 10px;")
            else:
                frame.setStyleSheet("background-color: #EEEEEE; border: 2px solid #BDBDBD; border-radius: 10px; padding: 10px;")
                icon.setStyleSheet("font-size: 48px; opacity: 0.5;")

            self.grid.addWidget(frame, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1