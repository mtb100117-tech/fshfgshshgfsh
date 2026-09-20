from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QWidget, QLabel


# Для арабского с огласовками лучший шрифт — Noto Naskh Arabic:
# он позиционирует харакат (фатха, дамма, касра, сукун, шадда) точнее,
# чем Noto Sans Arabic. Поэтому он идёт первым в списке приоритетов.
ARABIC_FONT_CANDIDATES = [
    "Noto Naskh Arabic",
    "Noto Sans Arabic",
    "Noto Sans Arabic Light",
    "Segoe UI",
]

CHINESE_FONT_CANDIDATES = [
    "Noto Sans SC",
    "Noto Sans SC Thin",
    "Noto Sans SC Light",
    "Noto Sans SC Regular",
    "Microsoft YaHei",
    "SimSun",
]

DEFAULT_FONT_CANDIDATES = [
    "Comic Sans MS",
    "Arial",
    "Segoe UI",
]

_FAMILY_CACHE = {}


def _resolve_family(candidates):
    key = tuple(candidates)
    cached = _FAMILY_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        available = set(QFontDatabase.families())
    except Exception:
        available = set()
    resolved = candidates[-1]
    for name in candidates:
        if name in available:
            resolved = name
            break
    _FAMILY_CACHE[key] = resolved
    return resolved


def _apply_font_family(widget, family):
    font = widget.font()
    font.setFamily(family)
    widget.setFont(font)


def set_rtl_for_widget(widget: QWidget) -> None:
    widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    _apply_font_family(widget, _resolve_family(ARABIC_FONT_CANDIDATES))


def set_rtl_for_label(label: QLabel) -> None:
    label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    _apply_font_family(label, _resolve_family(ARABIC_FONT_CANDIDATES))


def set_ltr_for_label(label: QLabel) -> None:
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    label.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    _apply_font_family(label, _resolve_family(DEFAULT_FONT_CANDIDATES))


def set_cjk_for_label(label: QLabel) -> None:
    _apply_font_family(label, _resolve_family(CHINESE_FONT_CANDIDATES))