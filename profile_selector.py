from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt
from ..controllers.app_controller import AppController
from ..utils.config import MAX_PROFILES
from ..utils.logger import logger


class ProfileSelector(QWidget):
    """Экран выбора профиля.

    Все кнопки работают мгновенно. Диалог создания профиля модальный,
    поэтому двойной клик по «+ Создать» не откроет два окна.
    """

    def __init__(self, controller: AppController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window
        self.main_layout = QVBoxLayout(self)

        logger.debug("ProfileSelector инициализирован")

        self.title = QLabel("Выбери свой профиль")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.title)

        self.profile_buttons = []
        self.profile_layout = QHBoxLayout()
        self.main_layout.addLayout(self.profile_layout)

        self.parent_btn = QPushButton("🔒 Родительский контроль")
        self.parent_btn.setMinimumHeight(44)
        self.parent_btn.clicked.connect(self.open_parent_control)
        self.main_layout.addWidget(self.parent_btn)

        self.refresh_profiles()

    def refresh_profiles(self):
        logger.debug("Обновление списка профилей")
        for btn in self.profile_buttons:
            self.profile_layout.removeWidget(btn)
            btn.deleteLater()
        self.profile_buttons.clear()

        users = self.controller.get_users()
        logger.info(f"Загружено {len(users)} профилей из {MAX_PROFILES} возможных")

        for i in range(MAX_PROFILES):
            if i < len(users):
                user = users[i]
                btn = QPushButton(f"{user.name}\n{user.avatar or '👤'}")
                btn.clicked.connect(lambda checked, u=user: self.select_profile(u))
            else:
                btn = QPushButton("+ Создать")
                btn.clicked.connect(lambda checked, idx=i: self.create_profile(idx))
            self.profile_buttons.append(btn)
            self.profile_layout.addWidget(btn)

    def select_profile(self, user):
        logger.info(f"Выбран профиль: {user.name} (id={user.id})")
        self.controller.set_current_user(user)
        self.main_window.show_main_menu()

    def create_profile(self, slot_index):
        logger.info(f"Попытка создания профиля в слоте {slot_index}")
        if len(self.controller.get_users()) >= MAX_PROFILES:
            logger.warning("Достигнут максимум профилей")
            QMessageBox.warning(self, "Ошибка", "Достигнут максимум профилей (4)")
            return

        name, ok = QInputDialog.getText(self, "Новый профиль", "Введите имя:")
        if ok and name.strip():
            avatar = "👦"
            user = self.controller.create_user(name.strip(), avatar)
            logger.info(f"Создан новый профиль: {user.name} (id={user.id})")
            self.refresh_profiles()
        elif ok:
            logger.warning("Попытка создать профиль с пустым именем")
            QMessageBox.warning(self, "Ошибка", "Имя не может быть пустым")

    def open_parent_control(self):
        logger.info("Открыт родительский контроль")
        self.main_window.show_parent_control()