"""
modules/transforms.py
Вся бизнес-логика: вычисление размера, дельт, ТОП-40, пивотов, истории цен.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

HISTORY_DIR = Path("data/history")

BRAND_CLASSES = {
    "Premium": [
        "Bridgestone", "Continental", "Dunlop", "Goodyear", "Hankook",
        "Michelin", "Nokian", "Pirelli", "Vredestein", "Yokohama",
    ],
    "Mid": [
        "BFGoodrich", "Cooper", "Falken", "Firestone", "Fulda", "Kleber",
        "Lassa", "Nexen", "Tigar", "Toyo", "Uniroyal", "Kumho",
    ],
    "Econom+": [
        "Debica", "Apollo", "Avon", "Barum", "Federal", "Gislaved",
        "Kormoran", "Laufenn", "Matador", "Orium", "Petlas", "Riken",
        "Sava", "Starmaxx",
    ],
}


# ── Базовые трансформации ────────────────────────────────────────────────────

def build_size_col(df: pd.DataFrame) -> pd.DataFrame:
    """Создаёт колонку Размер из трёх полей: 205/55 R16."""
    df = df.copy()
    df["Размер"] = (
        df["Ширина профиля"].astype(str).str.strip().str.replace(".0", "", regex=False)
        + "/"
        + df["Высота профиля"].astype(str).str.strip().str.replace(".0", "", regex=False)
        + " R"
        + df["Диаметр"].astype(str).str.strip().str.replace(".0", "", regex=False)
    )
    return df


def _best_price_per_size_brand(df: pd.DataFrame) -> pd.DataFrame:
    """
    Для каждой пары (Размер, Бренд) берёт минимальную розничную цену
    и суммарный остаток. Это убирает дубли от разных поставщиков.
    """
    return (
        df.groupby(["Размер", "Бренд"], as_index=False)
        .agg(
            Цена=("Исходная оптовая цена", "min"),
            Остаток=("В наличии", "sum"),
            Предложений=("ID товара", "count"),
        )
    )


# ── ТОП-40 размеров ──────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def compute_top40(df: pd.DataFrame, n: int = 40) -> list[str]:
    """
    ТОП-N размеров по суммарному остатку, но ТОЛЬКО где есть Nokian.
    Кэшируется по хэшу датафрейма.
    """
    if df.empty:
        return []
    
    # Сначала находим размеры где есть Nokian
    nokian_sizes = df[df["Бренд"] == "Nokian"]["Размер"].unique()
    
    if len(nokian_sizes) == 0:
        return []
    
    # Фильтруем df только по размерам Nokian
    df_nokian_sizes = df[df["Размер"].isin(nokian_sizes)]
    
    # Считаем суммарный остаток по этим размерам
    top = (
        df_nokian_sizes.groupby("Размер")["В наличии"]
        .sum()
        .nlargest(n)
        .index.tolist()
    )
    return top

# ── Блок 1: Waterfall ────────────────────────────────────────────────────────
def compute_waterfall(
    df: pd.DataFrame,
    models: list[str],
    comps: list[str],
    metric: str,
) -> pd.DataFrame:
    """
    Возвращает DataFrame для ценового водопада.
    Сравнивает бренды только по размерам где оба бренда присутствуют.
    """
    if not comps or df.empty:
        return pd.DataFrame()

    brands_needed = ["Nokian"] + comps
    
    # Фильтруем только нужные бренды
    agg = df[df["Бренд"].isin(brands_needed)].copy()
    
    if agg.empty:
        return pd.DataFrame()

    # Находим размеры где есть Nokian
    nokian_sizes = set(agg[agg["Бренд"] == "Nokian"]["Размер"].unique())
    
    if not nokian_sizes:
        return pd.DataFrame()

    rows = []
    
    for brand in brands_needed:
        brand_data = agg[agg["Бренд"] == brand]
        
        if brand_data.empty:
            continue
        
        if brand == "Nokian":
            # Nokian — берём все его размеры
            common_sizes = nokian_sizes
        else:
            # Конкурент — только размеры где есть И Nokian И конкурент
            competitor_sizes = set(brand_data["Размер"].unique())
            common_sizes = nokian_sizes & competitor_sizes
        
        if not common_sizes:
            continue
        
        # Фильтруем по общим размерам
        brand_common = brand_data[brand_data["Размер"].isin(common_sizes)]
        
        # Вычисляем цену по метрике
        if metric == "Медиана":
            price = brand_common["Исходная оптовая цена"].median()
        else:  # "Мин от 4 шт"
            brand_4plus = brand_common[brand_common["В наличии"] >= 4]
            if brand_4plus.empty:
                continue
            price = brand_4plus["Исходная оптовая цена"].min()
        
        rows.append({
            "Бренд": brand,
            "Цена": round(price, 2),
            "Размеров": len(common_sizes),
            "is_nokian": brand == "Nokian",
        })
    
    if not rows:
        return pd.DataFrame()
    
    result = pd.DataFrame(rows)
    
    # Находим цену Nokian
    nok_row = result[result["is_nokian"]]
    if nok_row.empty:
        return pd.DataFrame()
    
    nok_price = nok_row["Цена"].iloc[0]
    
    # Считаем дельты
    result["Δ%"] = result.apply(
        lambda r: None if r["is_nokian"] else round((nok_price / r["Цена"] - 1) * 100, 1),
        axis=1
    )
    result["Δ_грн"] = result.apply(
        lambda r: None if r["is_nokian"] else round(nok_price - r["Цена"], 0),
        axis=1
    )
    
    result = result.sort_values("Цена")
    return result

# ── Блок 2: Тепловая карта ───────────────────────────────────────────────────

# ── Блок 2: Тепловая карта ───────────────────────────────────────────────────

def compute_heatmap_pivot(
    df: pd.DataFrame,
    top40_sizes: list[str],
    comps: list[str],
    metric: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Pivot: строки = ТОП-40 размеров, столбцы = конкуренты.
    Возвращает 4 DataFrame: дельты, цены конкурента, модели, поставщики.
    """
    if not comps or not top40_sizes:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    brands_needed = ["Nokian"] + comps
    agg = df[df["Бренд"].isin(brands_needed) & df["Размер"].isin(top40_sizes)].copy()

    if agg.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    delta_rows = []
    price_rows = []
    model_rows = []
    supplier_rows = []
    
    for size in top40_sizes:
        size_data = agg[agg["Размер"] == size]
        
        nokian_in_size = size_data[size_data["Бренд"] == "Nokian"]
        if nokian_in_size.empty:
            continue
        
        # Цена Nokian
        if metric == "Медиана":
            nok_price = nokian_in_size["Исходная оптовая цена"].median()
        else:
            nok_price = nokian_in_size["Исходная оптовая цена"].min()
        
        delta_row = {"Размер": size, "Nokian ₴": round(nok_price)}
        price_row = {"Размер": size, "Nokian ₴": round(nok_price)}
        model_row = {"Размер": size, "Nokian ₴": ""}
        supplier_row = {"Размер": size, "Nokian ₴": ""}
        
        for comp in comps:
            comp_in_size = size_data[size_data["Бренд"] == comp]
            
            if comp_in_size.empty:
                delta_row[comp] = None
                price_row[comp] = None
                model_row[comp] = None
                supplier_row[comp] = None
            else:
                # Находим строку с минимальной/медианной ценой
                if metric == "Медиана":
                    comp_price = comp_in_size["Исходная оптовая цена"].median()
                    # Для медианы берём строку ближайшую к медиане
                    best_row = comp_in_size.iloc[(comp_in_size["Исходная оптовая цена"] - comp_price).abs().argsort()[:1]]
                else:
                    comp_price = comp_in_size["Исходная оптовая цена"].min()
                    # Для минимума берём строку с минимальной ценой
                    best_row = comp_in_size[comp_in_size["Исходная оптовая цена"] == comp_price].iloc[:1]
                
                delta = round((nok_price / comp_price - 1) * 100, 1) if comp_price else None
                
                delta_row[comp] = delta
                price_row[comp] = round(comp_price) if comp_price else None
                model_row[comp] = best_row["Модель"].iloc[0] if not best_row.empty else None
                supplier_row[comp] = best_row["Поставщик"].iloc[0] if not best_row.empty else None
        
        delta_rows.append(delta_row)
        price_rows.append(price_row)
        model_rows.append(model_row)
        supplier_rows.append(supplier_row)

    if not delta_rows:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    pivot_delta = pd.DataFrame(delta_rows).set_index("Размер")
    pivot_price = pd.DataFrame(price_rows).set_index("Размер")
    pivot_model = pd.DataFrame(model_rows).set_index("Размер")
    pivot_supplier = pd.DataFrame(supplier_rows).set_index("Размер")
    
    return pivot_delta, pivot_price, pivot_model, pivot_supplier


# ── Блок 3: Таблица продавцов ────────────────────────────────────────────────

def compute_sellers_pivot(df: pd.DataFrame, top40_sizes: list, show_classes: list) -> pd.DataFrame:
    """
    Вычисляет количество УНИКАЛЬНЫХ ПОСТАВЩИКОВ по размерам (из TOP-40) и брендам.
    
    Изменено: теперь считаем количество уникальных ID поставщиков,
    а не количество строк (предложений).
    
    Args:
        df: отфильтрованная таблица (с учётом глобальных фильтров)
        top40_sizes: список размеров из TOP-40
        show_classes: список выбранных классов брендов
    
    Returns:
        DataFrame с размерами в строках, брендами в колонках,
        значения = количество уникальных поставщиков
    """
    from modules.filters import BRAND_CLASSES
    
    # Собираем все бренды из выбранных классов
    all_brands = []
    for cls in show_classes:
        all_brands.extend(BRAND_CLASSES.get(cls, []))
    
    if not all_brands or df.empty:
        return pd.DataFrame()
    
    # Фильтруем: только нужные бренды и размеры из TOP-40
    sub = df[
        (df["Бренд"].isin(all_brands)) & 
        (df["Размер"].isin(top40_sizes))
    ].copy()
    
    if sub.empty:
        return pd.DataFrame()
    
    # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: считаем уникальные ID поставщиков
    # Группируем по (Размер, Бренд) и считаем количество уникальных "ID Поставщика"
    pivot = (
        sub.groupby(["Размер", "Бренд"])["ID Поставщика"]
        .nunique()  # ← nunique() вместо size()
        .unstack("Бренд", fill_value=0)
        .astype(int)
    )
    
    # Упорядочиваем колонки по классам
    ordered_cols = []
    for cls in show_classes:
        cls_brands = [b for b in BRAND_CLASSES.get(cls, []) if b in pivot.columns]
        ordered_cols.extend(cls_brands)
    
    pivot = pivot[[c for c in ordered_cols if c in pivot.columns]]
    
    # Добавляем итоговые колонки по классам
    for cls in show_classes:
        cls_brands = [b for b in BRAND_CLASSES.get(cls, []) if b in pivot.columns]
        if cls_brands:
            pivot[f"∑ {cls}"] = pivot[cls_brands].sum(axis=1)
    
    # Сортируем размеры по порядку из top40_sizes
    size_order = {s: i for i, s in enumerate(top40_sizes)}
    pivot["_sort"] = pivot.index.map(lambda x: size_order.get(x, 999))
    pivot = pivot.sort_values("_sort").drop(columns=["_sort"])
    
    return pivot


# ── Блок 4: История цен ──────────────────────────────────────────────────────

def compute_price_history() -> pd.DataFrame:
    """
    Читает все снапшоты из data/history/*.parquet и собирает длинный DataFrame:
    [Дата, Бренд, Модель, Размер, Цена]
    """
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(HISTORY_DIR.glob("*.parquet"))

    if not files:
        return pd.DataFrame()

    dfs = []
    for f in files:
        try:
            snap = pd.read_parquet(f)
            # Имя файла = дата YYYY-MM-DD.parquet
            snap["Дата"] = pd.to_datetime(f.stem)
            dfs.append(snap)
        except Exception:
            pass

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)


def compute_delta(row: pd.Series, nok_price: float) -> dict:
    """Утилита: дельта одной строки относительно цены Nokian."""
    p = row["Цена"]
    if not p or p == 0:
        return {"Δ%": None, "Δ_грн": None}
    return {
        "Δ%":    round((nok_price / p - 1) * 100, 1),
        "Δ_грн": round(nok_price - p),
    }
