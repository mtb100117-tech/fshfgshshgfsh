#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
download_fonts.py — автоматическая загрузка шрифтов Noto.

Скачивает TTF-файлы с официального репозитория notofonts.github.io
в папку app/resources/fonts/.
"""

import urllib.request
import sys
from pathlib import Path

# --- Настройки ---
PROJECT_ROOT = Path(__file__).resolve().parent
FONTS_DIR = PROJECT_ROOT / "app" / "resources" / "fonts"

# Словарь: {имя_файла: URL}
# URL-адреса ведут на raw-файлы с официального сайта Noto Fonts.
FONTS = {
    "NotoNaskhArabic-Regular.ttf": "https://notofonts.github.io/arabic/fonts/NotoNaskhArabic/hinted/ttf/NotoNaskhArabic-Regular.ttf",
    "NotoSansArabic-Regular.ttf": "https://notofonts.github.io/arabic/fonts/NotoSansArabic/hinted/ttf/NotoSansArabic-Regular.ttf",
    "NotoSansSC-Regular.otf": "https://notofonts.github.io/noto-cjk/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf",
}

def download_font(name: str, url: str) -> bool:
    """Скачивает один шрифт. Возвращает True при успехе."""
    dest = FONTS_DIR / name

    if dest.exists():
        print(f"  ⚪ Уже есть: {name}")
        return True

    print(f"  ⬇️  Скачиваю {name}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"  ✅ Готово: {name}")
        return True
    except Exception as e:
        print(f"  ❌ Ошибка загрузки {name}: {e}")
        return False

def main():
    print("=" * 60)
    print("🎨 Загрузка шрифтов Noto")
    print("=" * 60)

    FONTS_DIR.mkdir(parents=True, exist_ok=True)

    success = 0
    for name, url in FONTS.items():
        if download_font(name, url):
            success += 1

    print("\n" + "=" * 60)
    if success == len(FONTS):
        print("✅ Все шрифты загружены.")
    else:
        print(f"⚠️  Загружено {success} из {len(FONTS)} шрифтов.")
        print("   Проверьте подключение к интернету и повторите запуск.")
    print(f"   Папка: {FONTS_DIR}")
    print("=" * 60)

    return 0 if success == len(FONTS) else 1

if __name__ == '__main__':
    sys.exit(main())