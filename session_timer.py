from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from .logger import logger


class SessionTimer(QObject):
    """Считает время активной сессии и напоминает о перерыве.

    По методике: 10–15 минут, 4–5 раз в неделю. Мягкое напоминание —
    только сигнал, ничего не блокируем.
    """

    tick = pyqtSignal(int, bool)   # (прошло_секунд, пора_ли_отдыхать)

    TICK_MS = 1000
    RECOMMENDED_LIMIT_SEC = 15 * 60
    REPEAT_LIMIT_SEC = 5 * 60

    def __init__(self, parent=None):
        super().__init__(parent)
        self._elapsed = 0
        self._last_reminder = 0
        self._timer = QTimer(self)
        self._timer.setInterval(self.TICK_MS)
        self._timer.timeout.connect(self._on_tick)
        self._running = False

    def start(self):
        if self._running:
            return
        self._elapsed = 0
        self._last_reminder = 0
        self._timer.start()
        self._running = True
        logger.info("SessionTimer запущен")

    def stop(self):
        if not self._running:
            return
        self._timer.stop()
        self._running = False
        logger.info(f"SessionTimer остановлен, прошло {self._elapsed} сек")

    def reset(self):
        self._elapsed = 0
        self._last_reminder = 0

    def elapsed_text(self) -> str:
        m, s = divmod(self._elapsed, 60)
        return f"{m:02d}:{s:02d}"

    def _on_tick(self):
        self._elapsed += 1
        need_reminder = False
        if (self._elapsed >= self.RECOMMENDED_LIMIT_SEC
                and self._elapsed - self._last_reminder >= self.REPEAT_LIMIT_SEC):
            need_reminder = True
            self._last_reminder = self._elapsed
        self.tick.emit(self._elapsed, need_reminder)