from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LessonItem:
    """Элемент урока: буква, слог, слово, предложение или реплика диалога."""
    id: str
    text: str
    audio: Optional[str] = None
    translation: Optional[str] = None
    pinyin: Optional[str] = None
    speaker: Optional[str] = None
    image: Optional[str] = None


@dataclass
class Lesson:
    id: str
    title: str
    language: str
    items: List[LessonItem] = field(default_factory=list)
    dialog: List[LessonItem] = field(default_factory=list)
    parent_id: Optional[str] = None
    level: int = 1
    stars_required: int = 1
    is_dialog: bool = False

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'language': self.language,
            'items': [i.__dict__ for i in self.items],
            'dialog': [i.__dict__ for i in self.dialog],
            'parent_id': self.parent_id,
            'level': self.level,
            'stars_required': self.stars_required,
            'is_dialog': self.is_dialog,
        }