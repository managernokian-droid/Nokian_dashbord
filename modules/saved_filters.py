"""
modules/saved_filters.py
Управление сохранёнными наборами фильтров.
"""

import json
from pathlib import Path
from datetime import datetime

SAVED_FILTERS_DIR = Path("data/saved_filters")
SAVED_FILTERS_DIR.mkdir(parents=True, exist_ok=True)


def save_filter_set(name: str, filters: dict) -> bool:
    """Сохраняет набор фильтров под указанным именем."""
    try:
        # Убираем служебные ключи которые не нужно сохранять
        filters_to_save = {k: v for k, v in filters.items() if k != "apply_clicked"}
        
        # Добавляем метаданные
        data = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "filters": filters_to_save
        }
        
        # Безопасное имя файла
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        filepath = SAVED_FILTERS_DIR / f"{safe_name}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving filter set: {e}")
        return False


def load_filter_set(name: str) -> dict | None:
    """Загружает набор фильтров по имени."""
    try:
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        filepath = SAVED_FILTERS_DIR / f"{safe_name}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data["filters"]
    except Exception as e:
        print(f"Error loading filter set: {e}")
        return None


def list_saved_filters() -> list[dict]:
    """Возвращает список всех сохранённых наборов с метаданными."""
    saved = []
    
    for filepath in SAVED_FILTERS_DIR.glob("*.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            saved.append({
                "name": data["name"],
                "created_at": data.get("created_at", ""),
                "filepath": filepath,
            })
        except Exception:
            continue
    
    return sorted(saved, key=lambda x: x.get("created_at", ""), reverse=True)


def delete_filter_set(name: str) -> bool:
    """Удаляет сохранённый набор фильтров."""
    try:
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        filepath = SAVED_FILTERS_DIR / f"{safe_name}.json"
        
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    except Exception as e:
        print(f"Error deleting filter set: {e}")
        return False


def rename_filter_set(old_name: str, new_name: str) -> bool:
    """Переименовывает сохранённый набор."""
    try:
        # Загружаем старый
        filters = load_filter_set(old_name)
        if filters is None:
            return False
        
        # Сохраняем под новым именем
        if not save_filter_set(new_name, filters):
            return False
        
        # Удаляем старый
        delete_filter_set(old_name)
        return True
    except Exception as e:
        print(f"Error renaming filter set: {e}")
        return False
