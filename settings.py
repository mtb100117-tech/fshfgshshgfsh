from dataclasses import dataclass


@dataclass
class Settings:
    pin: str = "1234"
    internet_enabled: bool = False
    update_url: str = "https://example.com/update"