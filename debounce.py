from functools import wraps
from PyQt6.QtCore import QTimer, QObject
from .logger import logger


def debounce(wait_time_ms: int = 300, name: str = None):
    """Защита от ДВОЙНОГО клика — когда два нажатия подряд должны выполнить
    функцию только один раз (открытие модалки, отправка формы).

    ВАЖНО: не используйте на методах, которые вызываются повторно осознанно:
    - клик по карте в игре («Найди пару»)
    - клик по букве при наборе слова
    - клик по слову в списке
    - кнопки «Новый вопрос / Новая игра / Новая фраза»

    Проблема: этот декоратор отменяет предыдущий вызов, если новый пришёл
    раньше, чем через wait_time_ms. Для набора слова это означает, что
    часть букв теряется.

    Особенности:
    - Игнорирует `checked: bool`, который Qt передаёт в clicked().
    - Хранит QTimer с родителем, чтобы его не собрал GC.
    - Не глотает исключения: логирует их с traceback.
    """

    def decorator(func):
        fn_name = name or func.__qualname__

        # Родитель нужен, чтобы QTimer не был собран GC.
        # Создаётся лениво при первом вызове, потому что на этапе
        # декоратора QApplication может ещё не существовать.
        holder = {'timer': None, 'parent': None}
        pending = {'args': (), 'kwargs': {}}

        def _execute():
            args = pending['args']
            kwargs = pending['kwargs']
            try:
                func(*args, **kwargs)
            except Exception as e:
                logger.error(f"debounce[{fn_name}]: исключение внутри вызова: {e}",
                             exc_info=True)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Отбрасываем `checked: bool`, который Qt передаёт в clicked(bool).
            filtered_args = tuple(a for a in args if not isinstance(a, bool))
            pending['args'] = filtered_args
            pending['kwargs'] = kwargs

            if holder['timer'] is None:
                parent = QObject()
                holder['parent'] = parent
                timer = QTimer(parent)
                timer.setSingleShot(True)
                timer.timeout.connect(_execute)
                holder['timer'] = timer

            logger.debug(f"debounce[{fn_name}]: отложен на {wait_time_ms} мс")
            holder['timer'].start(wait_time_ms)

        return wrapper

    return decorator


def skip_when_busy(func):
    """Защита от повторного входа: если функция уже выполняется, новый
    вызов игнорируется. Отличается от debounce тем, что НЕ откладывает
    и НЕ отменяет первый вызов.

    Полезно для длительных операций (загрузка, скачивание), где
    повторный запуск нежелателен, но отмена уже запущенного — вредна.
    """
    running = {'flag': False}

    @wraps(func)
    def wrapper(*args, **kwargs):
        if running['flag']:
            logger.debug(f"skip_when_busy[{func.__qualname__}]: вызов пропущен "
                         f"(функция уже выполняется)")
            return
        running['flag'] = True
        try:
            return func(*args, **kwargs)
        finally:
            running['flag'] = False

    return wrapper