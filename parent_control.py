import os
import time
import webbrowser
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QMessageBox, QTableWidget,
                             QTableWidgetItem, QInputDialog, QTabWidget,
                             QProgressBar, QFileDialog, QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt
from ..controllers.app_controller import AppController
from ..controllers.updater import Updater
from ..utils.debounce import debounce


MAX_PIN_ATTEMPTS = 3
LOCKOUT_SECONDS = 30


class ParentControl(QWidget):
    def __init__(self, controller: AppController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window
        self.setLayout(QVBoxLayout())

        self._failed_attempts = 0
        self._locked_until = 0.0

        self.pin_label = QLabel("Введите PIN для доступа:")
        self.layout().addWidget(self.pin_label)
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.returnPressed.connect(self.check_pin)
        self.layout().addWidget(self.pin_input)
        self.check_btn = QPushButton("Войти")
        self.check_btn.clicked.connect(self.check_pin)
        self.layout().addWidget(self.check_btn)
        self.back_btn = QPushButton("Назад")
        self.back_btn.clicked.connect(lambda: self.main_window.show_profile_selector())
        self.layout().addWidget(self.back_btn)

        self.control_panel = QTabWidget()
        self.layout().addWidget(self.control_panel)
        self.control_panel.hide()

        # Статистика
        self.stats_tab = QWidget()
        self.stats_tab.setLayout(QVBoxLayout())
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels(
            ["Пользователь", "Время (мин)", "Уроков пройдено", "Ошибки"])
        self.stats_tab.layout().addWidget(self.stats_table)
        self.control_panel.addTab(self.stats_tab, "Статистика")

        # Управление
        self.manage_tab = QWidget()
        self.manage_tab.setLayout(QVBoxLayout())
        hbox = QHBoxLayout()
        self.reset_btn = QPushButton("Сбросить прогресс выбранного")
        self.reset_btn.clicked.connect(lambda: self.reset_progress())
        hbox.addWidget(self.reset_btn)
        self.change_pin_btn = QPushButton("Изменить PIN")
        self.change_pin_btn.clicked.connect(lambda: self.change_pin())
        hbox.addWidget(self.change_pin_btn)
        self.manage_tab.layout().addLayout(hbox)
        self.control_panel.addTab(self.manage_tab, "Управление")

        # Обновление
        self.update_tab = QWidget()
        self.update_tab.setLayout(QVBoxLayout())
        self.internet_status_label = QLabel("Интернет: отключён")
        self.update_tab.layout().addWidget(self.internet_status_label)
        self.toggle_internet_btn = QPushButton("Включить интернет")
        self.toggle_internet_btn.clicked.connect(self.toggle_internet)
        self.update_tab.layout().addWidget(self.toggle_internet_btn)

        self.url_label = QLabel("URL обновления:")
        self.update_tab.layout().addWidget(self.url_label)
        self.url_display = QLabel("не задан")
        self.url_display.setStyleSheet("color: blue; text-decoration: underline;")
        self.url_display.mousePressEvent = self.edit_url
        self.update_tab.layout().addWidget(self.url_display)

        self.check_updates_btn = QPushButton("Проверить обновления")
        self.check_updates_btn.clicked.connect(self.check_updates)
        self.check_updates_btn.setEnabled(False)
        self.update_tab.layout().addWidget(self.check_updates_btn)

        self.download_content_btn = QPushButton("Скачать и установить обновления контента")
        self.download_content_btn.clicked.connect(self.download_content)
        self.download_content_btn.setEnabled(False)
        self.update_tab.layout().addWidget(self.download_content_btn)

        self.download_app_btn = QPushButton("Обновить приложение")
        self.download_app_btn.clicked.connect(self.download_app)
        self.download_app_btn.setEnabled(False)
        self.update_tab.layout().addWidget(self.download_app_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.update_tab.layout().addWidget(self.progress_bar)
        self.control_panel.addTab(self.update_tab, "Обновление")

        # Импорт контента
        self.import_tab = QWidget()
        self.import_tab.setLayout(QVBoxLayout())
        self.import_label = QLabel("Импорт контента из ZIP-архива")
        self.import_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.import_tab.layout().addWidget(self.import_label)

        self.import_desc = QLabel(
            "Скачайте материалы с сайтов:\n"
            "• Английский: learnenglishkids.britishcouncil.org, kids-pages.com\n"
            "• Арабский: arabicplayground.com, lingust.ru/arabic\n"
            "• Китайский: chinese.littlefox.com, mandarinkids.com\n\n"
            "Поддерживаемые форматы:\n"
            "• Аудио: .mp3, .ogg (класть в папку audio/)\n"
            "• Изображения: .png, .webp (класть в папку images/)\n"
            "• Рабочие листы: .pdf (класть в папку worksheets/)\n\n"
            "Структура архива:\n"
            "content.zip\n"
            "  ├── en/\n"
            "  │   ├── lessons.json\n"
            "  │   ├── audio/  (сюда .mp3/.ogg)\n"
            "  │   ├── images/ (сюда .png/.webp)\n"
            "  │   └── worksheets/ (сюда .pdf)\n"
            "  ├── ar/ (аналогично)\n"
            "  └── zh/ (аналогично)\n\n"
            "Примечание: файл lessons.json обязателен для каждого языка."
        )
        self.import_desc.setWordWrap(True)
        self.import_tab.layout().addWidget(self.import_desc)

        sites_group = QGroupBox("Быстрый переход на сайты с контентом")
        sites_layout = QGridLayout()
        sites_group.setLayout(sites_layout)

        btn_en_british = QPushButton("British Council (англ.)")
        btn_en_british.clicked.connect(lambda: webbrowser.open("https://learnenglishkids.britishcouncil.org/"))
        sites_layout.addWidget(btn_en_british, 0, 0)
        btn_en_kids = QPushButton("Kids-Pages (англ.)")
        btn_en_kids.clicked.connect(lambda: webbrowser.open("https://www.kids-pages.com/"))
        sites_layout.addWidget(btn_en_kids, 0, 1)

        btn_ar_playground = QPushButton("Arabic Playground (ар.)")
        btn_ar_playground.clicked.connect(lambda: webbrowser.open("https://arabicplayground.com/"))
        sites_layout.addWidget(btn_ar_playground, 1, 0)
        btn_ar_lingust = QPushButton("Lingust (ар.)")
        btn_ar_lingust.clicked.connect(lambda: webbrowser.open("https://lingust.ru/arabic"))
        sites_layout.addWidget(btn_ar_lingust, 1, 1)

        btn_zh_littlefox = QPushButton("Little Fox (кит.)")
        btn_zh_littlefox.clicked.connect(lambda: webbrowser.open("https://chinese.littlefox.com/"))
        sites_layout.addWidget(btn_zh_littlefox, 2, 0)
        btn_zh_mandarin = QPushButton("Mandarin Kids (кит.)")
        btn_zh_mandarin.clicked.connect(lambda: webbrowser.open("https://mandarinkids.com/"))
        sites_layout.addWidget(btn_zh_mandarin, 2, 1)

        self.import_tab.layout().addWidget(sites_group)

        self.import_btn = QPushButton("Импортировать контент из ZIP...")
        self.import_btn.clicked.connect(self.import_content)
        self.import_tab.layout().addWidget(self.import_btn)

        self.open_content_btn = QPushButton("Открыть папку контента")
        self.open_content_btn.clicked.connect(self.open_content_folder)
        self.import_tab.layout().addWidget(self.open_content_btn)

        self.open_worksheets_btn = QPushButton("Открыть папку рабочих листов (PDF)")
        self.open_worksheets_btn.clicked.connect(self.open_worksheets_folder)
        self.import_tab.layout().addWidget(self.open_worksheets_btn)

        self.control_panel.addTab(self.import_tab, "Импорт контента")

        # Офлайн-папка
        self.offline_tab = QWidget()
        self.offline_tab.setLayout(QVBoxLayout())
        offline_desc = QLabel(
            "📁 Офлайн-папка для скачанных книг и аудио.\n\n"
            "Структура:\n"
            "  content/offline/\n"
            "    ├── english/   — сюда EPUB/PDF/MP3\n"
            "    ├── arabic/    — книги с огласовками\n"
            "    ├── chinese/   — книги с пиньинем\n"
            "    └── print/     — что распечатать\n\n"
            "Как заниматься по методике:\n"
            "  1. Слушаем аудио без книги.\n"
            "  2. Слушаем и смотрим картинки/текст.\n"
            "  3. Читаем/повторяем вместе.\n"
            "  4. 5–7 слов на книгу — карточки.\n"
            "  5. Рисуем сцену и подписываем 3–5 слов.\n"
            "  6. Играем в роли (лев и мышь, заяц и черепаха).\n\n"
            "Ритм: 10–15 минут, 4–5 раз в неделю. Наклейки — да, экзамен — нет."
        )
        offline_desc.setWordWrap(True)
        self.offline_tab.layout().addWidget(offline_desc)

        self.open_offline_btn = QPushButton("📂 Открыть офлайн-папку")
        self.open_offline_btn.clicked.connect(self.open_offline_folder)
        self.offline_tab.layout().addWidget(self.open_offline_btn)

        self.control_panel.addTab(self.offline_tab, "Офлайн-папка")

        self.authenticated = False

    @debounce(200)
    def check_pin(self):
        now = time.time()
        if now < self._locked_until:
            remaining = int(self._locked_until - now) + 1
            QMessageBox.warning(self, "Заблокировано",
                                f"Слишком много неверных попыток.\n"
                                f"Подождите {remaining} сек.")
            return

        entered = self.pin_input.text()
        if entered == self.controller.get_pin():
            self._failed_attempts = 0
            self.authenticated = True
            self.control_panel.show()
            self.pin_input.clear()
            self.load_stats()
            self.update_internet_ui()
            self.update_url_display()
            QMessageBox.information(self, "Успех", "Доступ разрешён")
        else:
            self._failed_attempts += 1
            if self._failed_attempts >= MAX_PIN_ATTEMPTS:
                self._locked_until = time.time() + LOCKOUT_SECONDS
                self._failed_attempts = 0
                QMessageBox.warning(self, "Заблокировано",
                                    f"Неверный PIN.\n"
                                    f"Слишком много попыток. Подождите {LOCKOUT_SECONDS} сек.")
            else:
                left = MAX_PIN_ATTEMPTS - self._failed_attempts
                QMessageBox.warning(self, "Ошибка",
                                    f"Неверный PIN. Осталось попыток: {left}")

    def load_stats(self):
        users = self.controller.get_users()
        self.stats_table.setRowCount(len(users))
        for i, user in enumerate(users):
            stats = self.controller.get_user_stats(user.id)
            self.stats_table.setItem(i, 0, QTableWidgetItem(user.name))
            time_min = stats.get('total_time', 0) // 60
            self.stats_table.setItem(i, 1, QTableWidgetItem(str(time_min)))
            self.stats_table.setItem(i, 2, QTableWidgetItem(str(stats.get('lessons_completed', 0))))
            self.stats_table.setItem(i, 3, QTableWidgetItem(str(stats.get('total_mistakes', 0))))

    @debounce(200)
    def reset_progress(self):
        reply = QMessageBox.question(self, "Сброс", "Сбросить прогресс всех пользователей?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.db.reset_all_progress()
            QMessageBox.information(self, "Готово", "Прогресс сброшен")
            self.load_stats()

    @debounce(200)
    def change_pin(self):
        new_pin, ok = QInputDialog.getText(self, "Смена PIN", "Введите новый PIN (4 цифры):")
        if ok and new_pin.isdigit() and len(new_pin) == 4:
            self.controller.set_pin(new_pin)
            QMessageBox.information(self, "Готово", "PIN изменён")
        elif ok:
            QMessageBox.warning(self, "Ошибка", "PIN должен состоять из 4 цифр")

    def update_internet_ui(self):
        enabled = self.controller.is_internet_enabled()
        self.internet_status_label.setText(f"Интернет: {'включён' if enabled else 'отключён'}")
        self.toggle_internet_btn.setText("Выключить интернет" if enabled else "Включить интернет")
        self.check_updates_btn.setEnabled(enabled)
        self.download_content_btn.setEnabled(enabled)
        self.download_app_btn.setEnabled(enabled)

    def update_url_display(self):
        url = self.controller.get_update_url()
        self.url_display.setText(url if url else "не задан")

    def edit_url(self, event):
        current = self.controller.get_update_url()
        new_url, ok = QInputDialog.getText(self, "Настройка URL обновления",
                                           "Введите базовый URL для обновлений (например, https://server.com/update):",
                                           text=current)
        if ok and new_url.strip():
            self.controller.set_update_url(new_url.strip())
            self.update_url_display()
            QMessageBox.information(self, "Готово", "URL обновления сохранён.")

    @debounce(200)
    def toggle_internet(self):
        current = self.controller.is_internet_enabled()
        new_state = not current
        if new_state:
            updater = Updater(base_url=self.controller.get_update_url())
            if not updater.check_internet_available():
                QMessageBox.warning(self, "Ошибка",
                                    "Интернет-соединение недоступно.\n"
                                    "Проверьте подключение и URL обновления.")
                return
        self.controller.set_internet_enabled(new_state)
        self.update_internet_ui()
        QMessageBox.information(self, "Интернет",
                                f"Интернет {'включён' if new_state else 'выключен'}")

    @debounce(200)
    def check_updates(self):
        if not self.controller.is_internet_enabled():
            QMessageBox.warning(self, "Ошибка", "Интернет отключён. Включите интернет в настройках.")
            return
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Проверка...")
        try:
            info = self.controller.check_updates()
            if info:
                msg = f"Доступна новая версия:\nВерсия: {info.get('version')}\n"
                msg += f"Версия контента: {info.get('content_version')}\n"
                msg += f"Версия приложения: {info.get('app_version')}\n"
                msg += f"Что нового: {info.get('changelog', 'Нет описания')}"
                QMessageBox.information(self, "Обновления", msg)
            else:
                QMessageBox.information(self, "Обновления",
                                        "Нет доступных обновлений или ошибка соединения.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка проверки: {e}")
        finally:
            self.progress_bar.setVisible(False)

    @debounce(200)
    def download_content(self):
        if not self.controller.is_internet_enabled():
            QMessageBox.warning(self, "Ошибка", "Интернет отключён.")
            return
        reply = QMessageBox.question(self, "Подтверждение",
                                     "Будет загружен и установлен новый контент. Продолжить?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Скачивание...")
        success = self.controller.update_content(self.update_progress)
        if success:
            QMessageBox.information(self, "Готово",
                                    "Контент обновлён. Перезапустите приложение для применения.")
            self.controller.load_content()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось обновить контент.")
        self.progress_bar.setVisible(False)

    @debounce(200)
    def download_app(self):
        if not self.controller.is_internet_enabled():
            QMessageBox.warning(self, "Ошибка", "Интернет отключён.")
            return
        reply = QMessageBox.question(self, "Подтверждение",
                                     "Будет загружена новая версия приложения. Продолжить?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Скачивание...")
        success = self.controller.update_app(self.update_progress)
        if success:
            QMessageBox.information(self, "Готово",
                                    "Приложение обновлено. Перезапустите его вручную.")
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось обновить приложение.")
        self.progress_bar.setVisible(False)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    @debounce(200)
    def import_content(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите ZIP-архив с контентом", "", "ZIP файлы (*.zip)")
        if not file_path:
            return
        reply = QMessageBox.question(self, "Подтверждение",
                                     "Импорт заменит всю папку контента. Продолжить?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Импорт...")
        success = self.controller.import_content_from_zip(file_path, self.update_progress)
        self.progress_bar.setVisible(False)
        if success:
            QMessageBox.information(self, "Готово", "Контент успешно импортирован.")
            self.controller.load_content()
        else:
            QMessageBox.critical(self, "Ошибка",
                                 "Не удалось импортировать контент. Проверьте структуру архива "
                                 "(должна быть папка content с подпапками en/ar/zh).")

    @debounce(200)
    def open_content_folder(self):
        import subprocess
        import sys
        content_dir = self.controller.get_content_dir()
        if content_dir.exists():
            if sys.platform == 'win32':
                os.startfile(str(content_dir))
            else:
                subprocess.Popen(['xdg-open', str(content_dir)])
        else:
            QMessageBox.warning(self, "Ошибка", "Папка контента не существует.")

    @debounce(200)
    def open_worksheets_folder(self):
        import subprocess
        import sys
        content_dir = self.controller.get_content_dir()
        if content_dir.exists():
            worksheets_dir = content_dir / 'worksheets'
            worksheets_dir.mkdir(exist_ok=True)
            if sys.platform == 'win32':
                os.startfile(str(worksheets_dir))
            else:
                subprocess.Popen(['xdg-open', str(worksheets_dir)])
        else:
            QMessageBox.warning(self, "Ошибка", "Папка контента не существует.")

    @debounce(200)
    def open_offline_folder(self):
        import subprocess
        import sys
        content_dir = self.controller.get_content_dir()
        offline_dir = content_dir / 'offline'
        for sub in ('english', 'arabic', 'chinese', 'print'):
            (offline_dir / sub).mkdir(parents=True, exist_ok=True)
        if sys.platform == 'win32':
            os.startfile(str(offline_dir))
        else:
            subprocess.Popen(['xdg-open', str(offline_dir)])