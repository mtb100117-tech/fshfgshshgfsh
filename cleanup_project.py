#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cleanup_project.py — удаление мусорных файлов проекта «Языки детям».

Удаляет:
  1. *.py.bak во всех папках проекта (кроме venv).
  2. __pycache__/ во всех папках (кроме venv, если --no-venv).
  3. views/flashcards_module.py (корневой дубликат) — если есть.
  4. venv/Lib/site-packages/numpy-*.whl — аномалия (если есть).

Запуск:
    python cleanup_project.py                # показать
    python cleanup_project.py --apply        # удалить с подтверждением
    python cleanup_project.py --apply --yes  # удалить без вопроса
    python cleanup_project.py --no-venv      # не трогать __pycache__ в venv

Корень проекта — папка с app/main.py. Ищется автоматически вверх от
папки скрипта и от текущей директории.
"""

import argparse
import shutil
import sys
from pathlib import Path


SKIP_DIRS = {'.git', '.idea', '.vscode', 'node_modules'}
VENV_NAMES = {'venv', '.venv', 'env', '.env'}


def is_project_root(path: Path) -> bool:
    return (path / 'app' / 'main.py').is_file()


def find_project_root() -> Path:
    starts = []
    try:
        starts.append(Path(__file__).resolve().parent)
    except NameError:
        pass
    starts.append(Path.cwd().resolve())

    for start in starts:
        cur = start
        for _ in range(15):
            if is_project_root(cur):
                return cur
            if cur.parent == cur:
                break
            cur = cur.parent

    print("❌ Не удалось найти корень проекта.")
    print("   Искал папку с файлом `app/main.py`.")
    sys.exit(2)


def human_size(num_bytes: int) -> str:
    for unit in ('B', 'KB', 'MB', 'GB'):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def dir_size(path: Path) -> int:
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total


def collect_targets(root: Path, include_venv: bool):
    files, dirs = [], []

    for f in root.rglob('*.bak'):
        if not f.is_file():
            continue
        parts = f.relative_to(root).parts
        if any(p in SKIP_DIRS for p in parts):
            continue
        if not include_venv and any(p in VENV_NAMES for p in parts):
            continue
        files.append(f)

    for d in root.rglob('__pycache__'):
        if not d.is_dir():
            continue
        parts = d.relative_to(root).parts
        if any(p in SKIP_DIRS for p in parts):
            continue
        if not include_venv and any(p in VENV_NAMES for p in parts):
            continue
        dirs.append(d)

    root_dup = root / 'views' / 'flashcards_module.py'
    if root_dup.is_file():
        files.append(root_dup)

    whl_dir = root / 'venv' / 'Lib' / 'site-packages'
    if whl_dir.is_dir():
        for whl in whl_dir.glob('numpy-*.whl'):
            if whl.is_file():
                files.append(whl)

    dirs = sorted(set(dirs), key=lambda p: len(p.parts))
    top_dirs = []
    for d in dirs:
        if not any(d.is_relative_to(parent) for parent in top_dirs):
            top_dirs.append(d)

    return files, top_dirs


def main():
    parser = argparse.ArgumentParser(description="Удаление мусора проекта.")
    parser.add_argument('--apply', action='store_true',
                        help='реально удалить (по умолчанию dry-run)')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='не спрашивать подтверждение')
    parser.add_argument('--no-venv', action='store_true',
                        help='не удалять __pycache__ внутри venv')
    args = parser.parse_args()

    root = find_project_root()
    print(f"✅ Корень проекта: {root}")

    files, dirs = collect_targets(root, include_venv=not args.no_venv)

    total = 0
    for f in files:
        try:
            total += f.stat().st_size
        except OSError:
            pass
    for d in dirs:
        total += dir_size(d)

    print()
    print("=" * 70)
    print("ФАЙЛЫ К УДАЛЕНИЮ")
    print("=" * 70)
    if files:
        for f in files:
            try:
                s = human_size(f.stat().st_size)
            except OSError:
                s = '?'
            print(f"  [F] {f.relative_to(root)}  ({s})")
    else:
        print("  (нет)")

    print()
    print("=" * 70)
    print("ПАПКИ К УДАЛЕНИЮ")
    print("=" * 70)
    if dirs:
        for d in dirs:
            print(f"  [D] {d.relative_to(root)}/  ({human_size(dir_size(d))})")
    else:
        print("  (нет)")

    print()
    print("=" * 70)
    print(f"ИТОГО: {len(files)} файлов, {len(dirs)} папок, {human_size(total)}")
    print("=" * 70)

    if not files and not dirs:
        print("\n✅ Проект уже чистый.")
        return 0

    if not args.apply:
        print("\n⚠️  Режим DRY-RUN. Ничего не удалено.")
        print("    Для удаления:  python cleanup_project.py --apply")
        return 0

    if not args.yes:
        try:
            ans = input("\nУдалить всё перечисленное? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nОтменено.")
            return 1
        if ans not in ('y', 'yes', 'д', 'да'):
            print("Отменено.")
            return 1

    print()
    errors = []
    for f in files:
        try:
            f.unlink()
            print(f"  ✓ файл:  {f.relative_to(root)}")
        except Exception as e:
            errors.append(f"{f.relative_to(root)}: {e}")
            print(f"  ✗ ошибка: {f.relative_to(root)}: {e}")
    for d in dirs:
        try:
            shutil.rmtree(d)
            print(f"  ✓ папка: {d.relative_to(root)}/")
        except Exception as e:
            errors.append(f"{d.relative_to(root)}/: {e}")
            print(f"  ✗ ошибка: {d.relative_to(root)}/: {e}")

    print()
    print("=" * 70)
    if errors:
        print(f"Удалено с ошибками ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        return 2
    print("✅ Готово. Всё лишнее удалено.")
    return 0


if __name__ == '__main__':
    sys.exit(main())