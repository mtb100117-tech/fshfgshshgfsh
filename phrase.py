from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Phrase:
    id: int
    language: str
    text: str
    translation: str
    audio_path: Optional[str] = None
    image_path: Optional[str] = None
    created_at: str = None
    last_practiced: Optional[str] = None
    practice_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()