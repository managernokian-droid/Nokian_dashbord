"""
modules/charts.py
Все Plotly-визуализации. Каждая функция принимает DataFrame и возвращает go.Figure.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from modules.i18n import t

# Цветовая схема
NOKIAN_COLOR    = "#185FA5"
GREEN_DARK      = "#3B6D11"
GREEN_LIGHT     = "#C0DD97"
RED_DARK        = "#A32D2D"
RED_MID         = "#E24B4A"
RED_LIGHT       = "#F09595"
AMBER           = "#EF9F27"
GRAY            = "#888780"

# Тепловая карта: зелёный (мы дешевле) → белый → красный (мы дороже)
HEATMAP_COLORSCALE = [
    [0.0,  "#3B6D11"],
    [0.35, "#C0DD97"],
    [0.50, "#F5F5F0"],
    [0.65, "#F09595"],
    [1.0,  "#A32D2D"],
]


# ── KPI row ──────────────────────────────────────────────────────────────────

def chart_kpi_row(wf: pd.DataFrame) -> None:
    """4 st.metric карточки из waterfall DataFrame."""
    nok_row  = wf[wf["is_nokian"]]
    comp_rows = wf[~wf["is_nokian"]]

    if nok_row.empty:
        return

    nok_price    = nok_row["Цена"].iloc[0]
    
    # Конкуренты ДОРОЖЕ нас = их цена > нашей цены
    cheaper_cnt  = (comp_rows["Цена"] > nok_price).sum()
    total_comps  = len(comp_rows)
    
    # Средняя дельта
    avg_delta = comp_rows["Δ%"].dropna().mean() if not comp_rows.empty else 0

    # Перцентиль: какой % конкурентов ДЕШЕВЛЕ нас
    prices = wf["Цена"].dropna().sort_values().tolist()
    if nok_price in prices and len(prices) > 1:
        rank = prices.index(nok_price)
        pct = round(rank / (len(prices) - 1) * 100)
    else:
        pct = 50

    c1, c2, c3, c4 = st.columns(4)
    
    c1.metric(
        t("charts.kpi.nokian_price"),
        f"{int(nok_price):,} ₴".replace(",", " "),
    )

    c2.metric(
        t("charts.kpi.percentile"),
        f"{pct}%",
        delta=t("charts.kpi.cheaper_majority") if pct < 50 else t("charts.kpi.expensive_majority"),
        delta_color="normal" if pct < 50 else "inverse",
    )

    c3.metric(
        t("charts.kpi.cheaper_than_us"),
        f"{cheaper_cnt} / {total_comps}",
        delta=t("charts.kpi.majority_expensive") if cheaper_cnt > total_comps / 2 else t("charts.kpi.majority_cheap"),
        delta_color="normal" if cheaper_cnt > total_comps / 2 else "inverse",
    )

    c4.metric(
        t("charts.kpi.avg_delta"),
        f"{avg_delta:+.1f}%" if pd.notna(avg_delta) else "—",
        delta=t("charts.kpi.we_expensive") if avg_delta > 0 else t("charts.kpi.we_cheap") if avg_delta < 0 else t("charts.kpi.equal"),
        delta_color="inverse" if avg_delta > 0 else "normal" if avg_delta < 0 else "off",
    )


# ── Блок 1: Waterfall ────────────────────────────────────────────────────────

def chart_waterfall(wf: pd.DataFrame, models: list[str]) -> go.Figure:
    """Горизонтальный bar chart — все бренды по одному размеру."""
    wf = wf.sort_values("Цена")

    colors = []
    for _, row in wf.iterrows():
        if row["is_nokian"]:
            colors.append(NOKIAN_COLOR)
        elif row["Δ%"] is None:
            colors.append(GRAY)
        elif row["Δ%"] > 10:
            colors.append(GREEN_DARK)
        elif row["Δ%"] > 0:
            colors.append(GREEN_LIGHT)
        elif row["Δ%"] > -10:
            colors.append(RED_LIGHT)
        else:
            colors.append(RED_DARK)

    # Текст на барах
    texts = []
    for _, row in wf.iterrows():
        price_str = f"{int(row['Цена']):,} ₴".replace(",", " ")
        if row["is_nokian"]:
            texts.append(f"<b>{price_str}</b>  ← наша цена")
        elif pd.notna(row["Δ%"]):
            sign = "–" if row["Δ%"] > 0 else "+"
            # Добавляем количество размеров
            sizes_info = f" ({int(row['Размеров'])} размеров)" if 'Размеров' in row else ""
            texts.append(f"{price_str}  {sign}{abs(row['Δ%'])}%{sizes_info}")
        else:
            texts.append(price_str)

    fig = go.Figure(go.Bar(
        x=wf["Цена"],
        y=wf["Бренд"],
        orientation="h",
        marker_color=colors,
        text=texts,
        textposition="outside",
        textfont=dict(size=12),
        customdata=wf[["Размеров"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Цена: %{x:,.0f} ₴<br>"
            "Пересечений: %{customdata[0]} размеров<br>"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        title=dict(text=f"<b>{t('charts.waterfall.title')}</b>", font=dict(size=14)),
        xaxis=dict(
            title="Исходная оптовая цена, ₴",
            tickformat=",",
            gridcolor="rgba(128,128,128,0.15)",
        ),
        yaxis=dict(title=t("charts.waterfall.y_axis")),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=100, r=160, t=50, b=40),
        height=max(300, len(wf) * 52 + 80),
        showlegend=False,
        font=dict(family="sans-serif", size=12),
    )

    # Вертикальная линия на цене Nokian
    nok_price = wf[wf["is_nokian"]]["Цена"].iloc[0] if not wf[wf["is_nokian"]].empty else None
    if nok_price:
        fig.add_vline(
            x=nok_price,
            line_dash="dash",
            line_color=NOKIAN_COLOR,
            opacity=0.6,
            annotation_text="Nokian",
            annotation_position="top",
        )

    return fig


# ── Блок 2: Тепловая карта ───────────────────────────────────────────────────

def chart_heatmap(
    pivot_delta: pd.DataFrame,
    pivot_price: pd.DataFrame, 
    pivot_model: pd.DataFrame,
    pivot_supplier: pd.DataFrame
) -> go.Figure:
    """
    Тепловая карта: строки = размеры, столбцы = конкуренты.
    Значения = Δ% (положительное = мы дороже конкурента).
    Аннотации = значение в каждой ячейке.
    """
    comp_cols = [c for c in pivot_delta.columns if c != "Nokian ₴"]
    z_data    = pivot_delta[comp_cols].values.astype(float)

    # Аннотации
    annotations = []
    for i in range(len(pivot_delta)):
        for j, col in enumerate(comp_cols):
            val = z_data[i, j]
            if np.isnan(val):
                text = "—"
                color = "#aaa"
            else:
                text  = f"{val:+.0f}%"
                color = "white" if abs(val) > 8 else "#333"
            annotations.append(dict(
                x=col, y=pivot_delta.index[i],
                text=text,
                font=dict(size=10, color=color),
                showarrow=False,
            ))

    # Симметричная шкала вокруг 0
    abs_max = np.nanmax(np.abs(z_data)) if not np.all(np.isnan(z_data)) else 20
    zmin, zmax = -abs_max, abs_max

    # Customdata для hover: [цена, модель, поставщик]
    customdata = []
    for i in range(len(pivot_delta)):
        row_data = []
        for j, col in enumerate(comp_cols):
            price = pivot_price.loc[pivot_delta.index[i], col]
            model = pivot_model.loc[pivot_delta.index[i], col]
            supplier = pivot_supplier.loc[pivot_delta.index[i], col]
            row_data.append([price, model, supplier])
        customdata.append(row_data)

    fig = go.Figure(go.Heatmap(
        z=z_data,
        x=comp_cols,
        y=pivot_delta.index.tolist(),
        zmin=zmin,
        zmax=zmax,
        colorscale=HEATMAP_COLORSCALE,
        showscale=True,
        colorbar=dict(
            title=t("charts.heatmap.title"),
            ticksuffix="%",
            len=0.8,
        ),
        customdata=customdata,
        hovertemplate=(
            "<b>%{y}</b> vs <b>%{x}</b><br>"
            "Δ: %{z:+.1f}%<br>"
            "Цена конкурента: %{customdata[0]:,.0f} ₴<br>"
            "Модель: %{customdata[1]}<br>"
            "Поставщик: %{customdata[2]}<br>"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        annotations=annotations,
        xaxis=dict(side="top", tickangle=0),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=100, r=80, t=80, b=20),
        height=max(500, len(pivot_delta) * 26 + 120),
        font=dict(family="sans-serif", size=11),
    )

    return fig


# ── Блок 3: Таблица продавцов ────────────────────────────────────────────────

def chart_sellers(pivot: pd.DataFrame) -> None:
    """
    Рендерит DataFrame через st.dataframe со Styler:
    - колонка Nokian подсвечена синим
    - итоговые колонки ∑ жирным
    - 0 → прозрачный
    """
    def style_sellers(df: pd.DataFrame):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        for col in df.columns:
            if col == "Nokian":
                styles[col] = "background-color: #E6F1FB; color: #185FA5; font-weight: 500"
            elif col.startswith("∑"):
                styles[col] = "font-weight: 600; background-color: #F1EFE8"
        return styles

    def color_cells(val):
        if pd.isna(val) or val == 0:
            return "color: #ccc"
        elif val >= 10:
            return "color: #3B6D11; font-weight: 500"
        elif val >= 5:
            return "color: #185FA5"
        return "color: #444"

    styled = (
        pivot.style
        .apply(style_sellers, axis=None)
        .map(color_cells)
        .format(lambda v: "—" if (pd.isna(v) or v == 0) else str(int(v)))
    )

    st.dataframe(
        styled,
        use_container_width=True,
        height=min(800, len(pivot) * 35 + 60),
    )


# ── Блок 4: Динамика цен ─────────────────────────────────────────────────────

def chart_price_trend(
    history: pd.DataFrame,
    brand: str,
    size: str,
) -> go.Figure:
    """Линейный тренд цены конкретного бренда/размера по датам снапшотов."""
    sub = history[
        (history["Бренд"] == brand) &
        (history["Размер"] == size)
    ].sort_values("Дата")

    if sub.empty:
        return go.Figure().update_layout(title=t("charts.price_trend.no_data"))

    # Агрегируем по дате (min цена = лучшее предложение на дату)
    trend = sub.groupby("Дата")["Моя розничная цена"].min().reset_index()

    # Δ% от первой точки
    first_price = trend["Моя розничная цена"].iloc[0]
    trend["Δ% от старта"] = ((trend["Моя розничная цена"] / first_price) - 1) * 100

    fig = go.Figure()

    # Основная линия цены
    fig.add_trace(go.Scatter(
        x=trend["Дата"],
        y=trend["Моя розничная цена"],
        mode="lines+markers",
        name=f"{brand} · {size}",
        line=dict(color=NOKIAN_COLOR if brand == "Nokian" else AMBER, width=2.5),
        marker=dict(size=7),
        hovertemplate="%{x|%d.%m.%Y}<br><b>%{y:,.0f} ₴</b><extra></extra>",
    ))

    # Аннотации на первой и последней точке
    for idx in [0, -1]:
        row = trend.iloc[idx]
        fig.add_annotation(
            x=row["Дата"],
            y=row["Моя розничная цена"],
            text=f"<b>{int(row['Моя розничная цена']):,} ₴</b>".replace(",", " "),
            showarrow=True,
            arrowhead=2,
            ax=0, ay=-30,
            font=dict(size=11),
        )

    fig.update_layout(
        title=f"Динамика цены: <b>{brand}</b> · {size}",
        xaxis=dict(title="Дата обновления", gridcolor="rgba(128,128,128,0.15)"),
        yaxis=dict(title="Мин. розничная цена, ₴", tickformat=",", gridcolor="rgba(128,128,128,0.15)"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=40, t=60, b=40),
        height=350,
        font=dict(family="sans-serif", size=12),
        hovermode="x unified",
    )

    return fig


def chart_price_distribution(history: pd.DataFrame) -> go.Figure:
    """
    Распределение изменений цен между двумя последними снапшотами.
    Показывает что подорожало / подешевело / не изменилось.
    """
    dates = sorted(history["Дата"].unique())
    if len(dates) < 2:
        return go.Figure().update_layout(title=t("messages.error"))

    d1, d2 = dates[-2], dates[-1]
    snap1 = history[history["Дата"] == d1].groupby(["Бренд", "Размер"])["Моя розничная цена"].min()
    snap2 = history[history["Дата"] == d2].groupby(["Бренд", "Размер"])["Моя розничная цена"].min()

    merged = pd.DataFrame({"Цена_до": snap1, "Цена_после": snap2}).dropna()
    merged["Δ%"] = ((merged["Цена_после"] / merged["Цена_до"]) - 1) * 100

    fig = px.histogram(
        merged,
        x="Δ%",
        nbins=40,
        color_discrete_sequence=[NOKIAN_COLOR],
        labels={"Δ%": t("charts.price_distribution.change")},
        title=f"{t('charts.price_distribution.title')}: {d1.strftime('%d.%m.%Y')} → {d2.strftime('%d.%m.%Y')}",
    )

    fig.add_vline(x=0, line_dash="dash", line_color=RED_MID, opacity=0.7)

    # Аннотации
    up   = (merged["Δ%"] > 0.5).sum()
    down = (merged["Δ%"] < -0.5).sum()
    same = len(merged) - up - down

    fig.add_annotation(
        text=f"↑ Подорожало: {up} поз.", x=0.98, xref="paper",
        y=0.98, yref="paper", showarrow=False,
        font=dict(color=RED_DARK, size=12), align="right",
    )
    fig.add_annotation(
        text=f"↓ Подешевело: {down} поз.", x=0.98, xref="paper",
        y=0.90, yref="paper", showarrow=False,
        font=dict(color=GREEN_DARK, size=12), align="right",
    )
    fig.add_annotation(
        text=f"= Без изменений: {same} поз.", x=0.98, xref="paper",
        y=0.82, yref="paper", showarrow=False,
        font=dict(color=GRAY, size=12), align="right",
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=40, t=60, b=40),
        height=300,
        xaxis=dict(ticksuffix="%", gridcolor="rgba(128,128,128,0.15)"),
        yaxis=dict(gridcolor="rgba(128,128,128,0.15)"),
        font=dict(family="sans-serif", size=12),
    )

    return fig
