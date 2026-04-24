"""
scripts/snapshot.py
──────────────────────────────────────────────────────────────────────────────
Запускайте ПОСЛЕ каждого обновления tires.xlsx (2 раза в месяц):

    python scripts/snapshot.py

Что делает:
1. Читает свежий tires.xlsx
2. Сохраняет снапшот текущих цен в data/history/YYYY-MM-DD.parquet
3. Сбрасывает кэш Parquet (data/tires.parquet) → следующий запуск дашборда
   перечитает xlsx и пересоберёт кэш

Файл истории содержит только нужные поля для блока динамики цен.
──────────────────────────────────────────────────────────────────────────────
"""

import sys
from datetime import date
from pathlib import Path

import pandas as pd

# Корень проекта
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

XLSX_PATH    = ROOT / "data" / "tires.xlsx"
PARQUET_PATH = ROOT / "data" / "tires.parquet"
HISTORY_DIR  = ROOT / "data" / "history"

KEEP_COLS = [
    "Бренд", "Класс", "Модель", "Сезон",
    "Ширина профиля", "Высота профиля", "Диаметр",
    "Моя розничная цена", "Моя оптовая цена",
    "Исходная розничная цена",
    "В наличии", "Страна производитель",
    "Год изготовления шин",
]

NUMERIC_COLS = [
    "Ширина профиля", "Высота профиля", "Диаметр",
    "Моя розничная цена", "Моя оптовая цена",
    "Исходная розничная цена", "В наличии",
]


def run():
    if not XLSX_PATH.exists():
        print(f"[ERROR] Файл не найден: {XLSX_PATH}")
        sys.exit(1)

    print(f"[1/4] Читаем {XLSX_PATH.name} ...")
    df = pd.read_excel(XLSX_PATH, engine="openpyxl", dtype=str)
    df.columns = df.columns.str.strip()
    print(f"      Строк: {len(df):,}")

    # Числовые колонки
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce")

    # Составной размер
    df["Размер"] = (
        df["Ширина профиля"].astype(str).str.replace(".0", "", regex=False)
        + "/"
        + df["Высота профиля"].astype(str).str.replace(".0", "", regex=False)
        + " R"
        + df["Диаметр"].astype(str).str.replace(".0", "", regex=False)
    )

    # Оставляем только нужные колонки
    available = [c for c in KEEP_COLS + ["Размер"] if c in df.columns]
    snap = df[available].dropna(subset=["Бренд", "Моя розничная цена"])
    snap = snap[snap["Моя розничная цена"] > 0]

    # Сохраняем снапшот
    today = date.today().isoformat()
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    out_path = HISTORY_DIR / f"{today}.parquet"

    print(f"[2/4] Сохраняем снапшот → {out_path.name}  ({len(snap):,} строк) ...")
    snap.to_parquet(out_path, index=False)

    # Сбрасываем основной Parquet-кэш
    print("[3/4] Сбрасываем кэш data/tires.parquet ...")
    if PARQUET_PATH.exists():
        PARQUET_PATH.unlink()
        print("      Кэш удалён — при следующем запуске дашборда пересоберётся автоматически.")
    else:
        print("      Кэш не найден — ничего не делаем.")

    # Список снапшотов
    snapshots = sorted(HISTORY_DIR.glob("*.parquet"))
    print(f"[4/4] Готово! Всего снапшотов в истории: {len(snapshots)}")
    for s in snapshots:
        size_kb = s.stat().st_size // 1024
        print(f"      {s.name}  ({size_kb} KB)")


if __name__ == "__main__":
    run()
