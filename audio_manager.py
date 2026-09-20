import os
import numpy as np
import sounddevice as sd
import soundfile as sf
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from ..utils.logger import logger


class AudioManager(QObject):
    """Менеджер аудио: воспроизведение и запись."""
    volume_updated = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        self.is_recording = False
        self.recorded_data = None
        self.recorded_file = None
        self._record_stream = None
        self._record_buffer = []

        logger.debug("AudioManager инициализирован")

    def play_audio(self, file_path: str):
        """Воспроизводит аудиофайл. Во время записи воспроизведение
        блокируется, чтобы микрофон не писал эхо."""
        if self.is_recording:
            logger.warning("Воспроизведение заблокировано: идёт запись")
            return
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"Аудиофайл не найден: {file_path}")
            return
        try:
            url = QUrl.fromLocalFile(file_path)
            self.player.setSource(url)
            self.player.play()
            logger.debug(f"Воспроизведение аудио: {file_path}")
        except Exception as e:
            logger.error(f"Ошибка воспроизведения аудио: {e}", exc_info=True)

    def stop_audio(self):
        try:
            self.player.stop()
            logger.debug("Воспроизведение остановлено")
        except Exception as e:
            logger.error(f"Ошибка остановки аудио: {e}", exc_info=True)

    def is_microphone_available(self) -> bool:
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            available = len(input_devices) > 0
            logger.info(f"Микрофон {'доступен' if available else 'недоступен'}")
            return available
        except Exception as e:
            logger.error(f"Ошибка проверки микрофона: {e}", exc_info=True)
            return False

    def start_recording(self):
        if self.is_recording:
            return
        self.stop_audio()

        self._record_buffer = []
        self.is_recording = True

        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Статус записи: {status}")
            self._record_buffer.append(indata.copy())
            volume = np.abs(indata).mean()
            self.volume_updated.emit(float(volume))

        try:
            self._record_stream = sd.InputStream(
                samplerate=44100,
                channels=1,
                dtype='float32',
                callback=audio_callback
            )
            self._record_stream.start()
            logger.info("Запись начата")
        except Exception as e:
            self.is_recording = False
            logger.error(f"Ошибка начала записи: {e}", exc_info=True)
            raise

    def stop_recording(self):
        if not self.is_recording:
            return
        try:
            if self._record_stream:
                self._record_stream.stop()
                self._record_stream.close()
                self._record_stream = None

            if self._record_buffer:
                self.recorded_data = np.concatenate(self._record_buffer, axis=0)
            else:
                self.recorded_data = None

            self.is_recording = False
            self._record_buffer = []
            logger.info("Запись остановлена")
        except Exception as e:
            logger.error(f"Ошибка остановки записи: {e}", exc_info=True)
            self.is_recording = False

    def play_recorded(self):
        if self.recorded_data is None:
            logger.warning("Нет записанных данных")
            return
        if self.is_recording:
            logger.warning("Воспроизведение заблокировано: идёт запись")
            return
        try:
            import tempfile
            temp_file = os.path.join(tempfile.gettempdir(), "last_recording.wav")
            sf.write(temp_file, self.recorded_data, 44100)
            self.play_audio(temp_file)
            self.recorded_file = temp_file
            logger.debug(f"Воспроизведение записи: {temp_file}")
        except Exception as e:
            logger.error(f"Ошибка воспроизведения записи: {e}", exc_info=True)

    def cleanup(self):
        try:
            self.stop_audio()
            if self.is_recording:
                self.stop_recording()
            logger.debug("AudioManager очищен")
        except Exception as e:
            logger.error(f"Ошибка очистки AudioManager: {e}", exc_info=True)