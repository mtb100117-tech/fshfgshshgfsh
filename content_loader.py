import json
from pathlib import Path
from typing import Dict, List
from ..models.lesson import Lesson, LessonItem
from ..utils.config import CONTENT_DIR
from ..utils.logger import logger


class ContentLoader:
    """Загрузчик контента уроков из lessons.json."""

    def __init__(self):
        self.lessons: Dict[str, List[Lesson]] = {'en': [], 'ar': [], 'zh': []}
        logger.debug("ContentLoader инициализирован")

    def load_all_lessons(self) -> None:
        logger.info("Начало загрузки уроков")
        for lang in ['en', 'ar', 'zh']:
            lessons_file = CONTENT_DIR / lang / 'lessons.json'
            if lessons_file.exists():
                try:
                    self.lessons[lang] = self._load_lessons_from_file(lessons_file, lang)
                    logger.info(f"Загружено {len(self.lessons[lang])} уроков для языка {lang}")
                except Exception as e:
                    logger.error(f"Ошибка загрузки уроков для {lang}: {e}", exc_info=True)
                    self.lessons[lang] = []
            else:
                logger.warning(f"Файл lessons.json не найден для языка {lang}: {lessons_file}")
                self.lessons[lang] = []
        logger.info("Загрузка уроков завершена")

    def reload_lessons(self) -> None:
        logger.info("Перезагрузка уроков")
        self.load_all_lessons()

    def _load_lessons_from_file(self, file_path: Path, language: str) -> List[Lesson]:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        lessons: List[Lesson] = []

        if isinstance(data, list):
            raw_lessons = data
        elif isinstance(data, dict) and 'topics' in data:
            raw_lessons = []
            for topic in data['topics']:
                raw_lessons.append({
                    'id': topic.get('id', ''),
                    'title': topic.get('name', ''),
                    'language': language,
                    'level': 1,
                    'is_dialog': False,
                    'items': [
                        {
                            'id': card.get('id', ''),
                            'text': card.get('word', ''),
                            'translation': card.get('translation', ''),
                            'audio': card.get('audio', ''),
                            'image': card.get('image', ''),
                            'pinyin': card.get('pinyin', '') if language == 'zh' else None,
                        }
                        for card in topic.get('cards', [])
                    ],
                })
        else:
            return []

        for lesson_data in raw_lessons:
            lesson = self._parse_lesson(lesson_data, language)
            if lesson:
                lessons.append(lesson)
        return lessons

    @staticmethod
    def _derive_image_path(item_id: str) -> str:
        """`en_animals_cat` → `images/animals/cat.png`.

        Возвращает '' для:
          - id не подходящего по формату (< 3 частей);
          - реплик диалога (`*_dialog_*`);
          - случая, когда файла по вычисленному пути нет.
        """
        if not item_id:
            return ''
        parts = item_id.split('_')
        if len(parts) < 3:
            return ''
        topic = parts[1]
        if topic == 'dialog':
            return ''
        word = '_'.join(parts[2:])
        candidate = f"images/{topic}/{word}.png"
        if (CONTENT_DIR / candidate).is_file():
            return candidate
        return ''

    @staticmethod
    def _resolve_audio(audio_rel: str) -> str:
        if not audio_rel:
            return ''
        if Path(audio_rel).is_absolute():
            return audio_rel
        full = CONTENT_DIR / audio_rel
        return str(full) if full.exists() else ''

    def _parse_item(self, item_data: dict, language: str) -> LessonItem:
        item_id = item_data.get('id', '')
        image_rel = item_data.get('image', '') or self._derive_image_path(item_id)
        return LessonItem(
            id=item_id,
            text=item_data.get('text', ''),
            audio=self._resolve_audio(item_data.get('audio', '')),
            translation=item_data.get('translation', ''),
            pinyin=item_data.get('pinyin'),
            speaker=item_data.get('speaker'),
            image=image_rel,
        )

    def _parse_lesson(self, data: dict, language: str) -> Lesson:
        try:
            items = [self._parse_item(d, language) for d in data.get('items', [])]
            dialog = [self._parse_item(d, language) for d in data.get('dialog', [])]
            return Lesson(
                id=data.get('id', ''),
                title=data.get('title', ''),
                language=language,
                items=items,
                dialog=dialog,
                parent_id=data.get('parent_id'),
                level=data.get('level', 1),
                stars_required=data.get('stars_required', 1),
                is_dialog=data.get('is_dialog', False),
            )
        except Exception as e:
            logger.error(f"Ошибка парсинга урока: {e}", exc_info=True)
            return None