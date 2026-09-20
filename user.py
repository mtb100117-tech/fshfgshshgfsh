from dataclasses import dataclass, field
from typing import Optional
import json
from datetime import datetime

@dataclass
class User:
    id: int
    name: str
    avatar: str  # путь к файлу аватара
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_login: Optional[str] = None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'avatar': self.avatar,
            'created_at': self.created_at,
            'last_login': self.last_login
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)