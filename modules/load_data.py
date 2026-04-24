from pathlib import Path
import pandas as pd
import streamlit as st

DATA_DIR     = Path("data")
XLSX_PATH    = DATA_DIR / "tires.xlsx"
PARQUET_PATH = DATA_DIR / "tires.parquet"

COLUMN_MAP = {
    "ID товара": "ID товара", "ID Поставщика": "ID Поставщика",
    "Бренд": "Бренд", "Класс": "Класс", "Модель": "Модель",
    "Полное название": "Полное название", "Сезон": "Сезон",
    "Ширина профиля": "Ширина профиля", "Высота профиля": "Высота профиля",
    "Диаметр": "Диаметр", "Индекс нагрузки": "Индекс нагрузки",
    "Индекс скорости": "Индекс скорости", "Усиление": "Усиление",
    "Шип/не шип": "Шип/не шип", "Страна производитель": "Страна производитель",
    "Дата обновления": "Дата обновления", "Поставщик": "Поставщик",
    "Город": "Город", "В наличии": "В наличии",
    "Исходная оптовая цена": "Исходная оптовая цена",
    "Исходная розничная цена": "Исходная розничная цена",
    "Моя розничная цена": "Моя розничная цена",
    "Моя оптовая цена": "Моя оптовая цена",
    "Тип транспортного средства": "Тип транспортного средства",
    "Год изготовления шин": "Год изготовления шин",
    "Оммологация": "Оммологация",
}

NUMERIC_COLS = [
    "Ширина профиля", "Высота профиля", "Диаметр",
    "Индекс нагрузки", "В наличии",
    "Исходная оптовая цена", "Исходная розничная цена",
    "Моя розничная цена", "Моя оптовая цена",
]


def _xlsx_mtime() -> float:
    return XLSX_PATH.stat().st_mtime if XLSX_PATH.exists() else 0.0


def _parquet_mtime() -> float:
    return PARQUET_PATH.stat().st_mtime if PARQUET_PATH.exists() else 0.0


def _rebuild_parquet() -> pd.DataFrame:
    df = pd.read_excel(XLSX_PATH, engine="openpyxl", dtype=str)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={c: COLUMN_MAP.get(c, c) for c in df.columns})

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce")

    if "Дата обновления" in df.columns:
        df["Дата обновления"] = pd.to_datetime(df["Дата обновления"], errors="coerce")

    if "Год изготовления шин" in df.columns:
        df["Год изготовления шин"] = (
            pd.to_numeric(df["Год изготовления шин"], errors="coerce")
            .fillna(0).astype(int)
        )

    df = df.dropna(subset=["Бренд", "Моя розничная цена"])
    df = df[df["Моя розничная цена"] > 0]
    DATA_DIR.mkdir(exist_ok=True)
    df.to_parquet(PARQUET_PATH, index=False)
    return df


@st.cache_data(ttl=1800)
def load_data() -> pd.DataFrame:
    if not XLSX_PATH.exists():
        st.error(f"Файл не найден: {XLSX_PATH.resolve()}")
        st.stop()
    if PARQUET_PATH.exists() and _parquet_mtime() >= _xlsx_mtime():
        return pd.read_parquet(PARQUET_PATH)
    return _rebuild_parquet()


def invalidate_cache():
    load_data.clear()
    if PARQUET_PATH.exists():
        PARQUET_PATH.unlink()