import sys
import os
import faulthandler
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, qInstallMessageHandler
from PyQt6.QtGui import QFontDatabase

from .utils.logger import logger
from .views.main_window import MainWindow
from .utils.config import get_app_data_dir
from .controllers.app_controller import AppController

os.environ['QT_LOGGING_RULES'] = 'qt.multimedia.ffmpeg=false'

# ---------------------------------------------------------------------------
# ДИАГНОСТИКА
# ---------------------------------------------------------------------------

try:
    faulthandler.enable()
except Exception:
    pass


def _qt_message_handler(mode, context, message):
    try:
        mode_name = {
            0: 'QtDebug',
            1: 'QtWarning',
            2: 'QtCritical',
            3: 'QtFatal',
            4: 'QtInfo',
        }.get(int(mode), f'QtMode{int(mode)}')

        location = ''
        if context is not None and getattr(context, 'file', None):
            location = f" [{context.file}:{context.line}]"

        logger.info(f"[{mode_name}]{location} {message}")
    except Exception:
        pass


def _load_application_fonts() -> None:
    """Загружает .ttf-шрифты из resources/ и resources/fonts/."""
    resources_dir = Path(__file__).parent / 'resources'
    candidate_dirs = [resources_dir / 'fonts', resources_dir]

    loaded = set()
    for fonts_dir in candidate_dirs:
        if not fonts_dir.exists():
            continue
        for font_file in fonts_dir.glob('*.ttf'):
            if font_file.name in loaded:
                continue
            font_id = QFontDatabase.addApplicationFont(str(font_file))
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                logger.info(f"Шрифт загружен: {font_file.name} -> {families}")
                loaded.add(font_file.name)
            else:
                logger.warning(f"Не удалось загрузить шрифт: {font_file.name}")


def main():
    logger.info("=" * 60)
    logger.info("ЗАПУСК ПРИЛОЖЕНИЯ")
    logger.info("=" * 60)

    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
            logger.info("Кодировка консоли настроена на UTF-8")
        except AttributeError as e:
            logger.warning(f"Не удалось настроить кодировку консоли: {e}")

    qInstallMessageHandler(_qt_message_handler)

    logger.info("=== Запуск приложения ===")
    print("=== Запуск приложения ===")

    try:
        app_data_dir = get_app_data_dir()
        logger.info(f"Папка данных приложения: {app_data_dir}")
        logger.info("Папка данных приложения создана/проверена")
        print("Папка данных приложения создана/проверена")

        app = QApplication(sys.argv)
        logger.info("QApplication создан")

        _load_application_fonts()

        styles_path = Path(__file__).parent / 'resources' / 'styles.qss'
        logger.info(f"Путь к файлу стилей: {styles_path}")

        if styles_path.exists():
            try:
                with open(styles_path, 'r', encoding='utf-8') as f:
                    app.setStyleSheet(f.read())
                logger.info(f"Стили успешно загружены из {styles_path}")
                print(f"Стили загружены из {styles_path}")
            except Exception as e:
                logger.error(f"Не удалось загрузить стили: {e}", exc_info=True)
        else:
            logger.warning(f"Файл стилей не найден: {styles_path}")
            styles_path.parent.mkdir(parents=True, exist_ok=True)
            default_styles = """
                QPushButton {
                    background-color: #4CAF50; color: white; border: none;
                    padding: 12px 24px; border-radius: 15px;
                    font-size: 18px; font-weight: bold;
                }
                QPushButton:hover { background-color: #45a049; }
                QLabel { font-size: 18px; }
            """
            try:
                with open(styles_path, 'w', encoding='utf-8') as f:
                    f.write(default_styles)
                app.setStyleSheet(default_styles)
                logger.info(f"Создан файл стилей по умолчанию: {styles_path}")
                print(f"Создан файл стилей по умолчанию: {styles_path}")
            except Exception as e:
                logger.error(f"Не удалось создать файл стилей: {e}", exc_info=True)

        logger.info("Создаю AppController...")
        controller = AppController()
        logger.info("Контроллер создан")
        print("Контроллер создан")

        logger.info("Создаю MainWindow...")
        window = MainWindow(controller)
        logger.info("Главное окно создано")
        print("Главное окно создано")

        window.show()
        logger.info("Окно отображено, вход в цикл событий Qt")
        print("Приложение запущено, вход в цикл событий")

        exit_code = app.exec()
        logger.info(f"Приложение завершено штатно с кодом {exit_code}")
        print(f"Приложение завершено с кодом {exit_code}")

        sys.exit(exit_code)

    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        print(f"Критическая ошибка: {e}")
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Критическая ошибка",
                                 f"Произошла ошибка:\n{str(e)}\n\n"
                                 "Подробности записаны в лог-файл.")
        except Exception as msg_error:
            logger.error(f"Не удалось показать QMessageBox: {msg_error}")
        sys.exit(1)


if __name__ == '__main__':
    main()