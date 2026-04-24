"""
Tire Price Intelligence Dashboard
Nokian vs конкуренты | Price positioning + ТОП-40 + продавцы + динамика цен
"""

import streamlit as st
import pandas as pd

# ── Initialize translations ──────────────────────────────────────────────────
from modules.i18n import t, t_format, render_language_selector, get_language

st.set_page_config(
    page_title="Nokian Price Intelligence",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS overrides ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    [data-testid="stMetricValue"] { font-size: 1.6rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 6px 16px; }
    div[data-testid="stSidebarContent"] { padding-top: 1rem; }
    .section-header {
        font-size: 0.75rem; font-weight: 600; letter-spacing: 0.06em;
        text-transform: uppercase; color: #888; margin: 1rem 0 0.4rem;
    }
</style>
""", unsafe_allow_html=True)

from modules.load_data import load_data
from modules.filters   import render_sidebar
from modules.transforms import (
    build_size_col, compute_top40, compute_delta,
    compute_waterfall, compute_heatmap_pivot, compute_sellers_pivot,
    compute_price_history,
)
from modules.charts import (
    chart_waterfall, chart_kpi_row,
    chart_heatmap, chart_sellers,
    chart_price_trend, chart_price_distribution,
)

# ── Load data ────────────────────────────────────────────────────────────────
df_raw = load_data()
df     = build_size_col(df_raw)

# Добавляем колонку Регион
from modules.regions import get_region
df["Регион"] = df["Город"].apply(get_region)

# Убираем позиции с остатком 1, 2, 3 штуки
df = df[df["В наличии"] >= 4].copy()

# ── Sidebar language selector ───────────────────────────────────────────────
with st.sidebar:
    render_language_selector()
    st.divider()

# ── Sidebar filters ──────────────────────────────────────────────────────────
filters = render_sidebar(df)

# Показываем какой срез загружен (если есть)
if "current_slice_name" in st.session_state:
    st.info(f"📁 {t('sidebar.active_slice')}: **{st.session_state['current_slice_name']}**")

# Временная отладка
if filters["apply_clicked"]:
    st.sidebar.write("DEBUG:")
    st.sidebar.write(f"Поставщики выбрано: {len(filters['suppliers'])}")
    st.sidebar.write(f"Бренды выбрано: {len(filters['brands'])}")

# ── Apply filters ────────────────────────────────────────────────────────────
if filters["apply_clicked"]:
    mask = df["Класс"].isin(filters["classes"])
    
    if filters["seasons"]:
        mask &= df["Сезон"].isin(filters["seasons"])
    
    if filters["years"]:
        mask &= df["Год изготовления шин"].astype(str).isin(filters["years"])
    
    if filters["vehicles"]:
        mask &= df["Тип транспортного средства"].isin(filters["vehicles"])
    
    if filters["regions"]:
        mask &= df["Регион"].isin(filters["regions"])
    
    if filters["brands"]:
        mask &= df["Бренд"].isin(filters["brands"])

    if filters["suppliers"]:
        mask &= df["Поставщик"].isin(filters["suppliers"])
    
    if filters["models"]:
        mask &= df["Модель"].isin(filters["models"])
    
    if filters["countries"]:
        mask &= df["Страна производитель"].isin(filters["countries"])
    
    df_filtered = df[mask].copy()
else:
    # До первого нажатия кнопки показываем пустой результат или всё
    df_filtered = df.head(0)  # или df.copy() если хотите показать всё сразу


# ── Nokian slice ─────────────────────────────────────────────────────────────
df_nokian = df_filtered[df_filtered["Бренд"] == "Nokian"]
active_comps = filters["comps"]        # list of selected competitor brands

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    t("tabs.position"),
    t("tabs.heatmap"),
    t("tabs.sellers"),
    t("tabs.dynamics"),
    t("tabs.map"),
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Позиция модели (Block 1)
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    wf_data = compute_waterfall(df_filtered, filters["models"], active_comps, filters["metric"])

    if wf_data.empty:
        st.warning(t("tab1.no_data"))
    else:
        chart_kpi_row(wf_data)
        st.plotly_chart(
            chart_waterfall(wf_data, filters["models"]),
            use_container_width=True,
        )

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Тепловая карта ТОП-40 (Block 2)
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    top40_sizes = compute_top40(df_filtered)
    pivot_delta, pivot_price, pivot_model, pivot_supplier = compute_heatmap_pivot(
        df_filtered, top40_sizes, active_comps, filters["metric"]
    )

    if pivot_delta.empty:
        st.warning(t("tab2.no_data"))
    else:
        col1, col2 = st.columns([5, 1])

        with col1:
            st.caption(
                t_format("tab2.caption", count=len(top40_sizes), comps=len(active_comps))
            )

        with col2:
            from modules.export_excel import export_heatmap_to_excel
            from datetime import datetime

            excel_file = export_heatmap_to_excel(
                pivot_delta, pivot_price, pivot_model, pivot_supplier
            )

            st.download_button(
                label=t("tab2.download_excel"),
                data=excel_file,
                file_name=f"heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        st.plotly_chart(
            chart_heatmap(pivot_delta, pivot_price, pivot_model, pivot_supplier),
            use_container_width=True,
        )

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Продавцы по размеру (Block 3)
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    show_classes = filters["classes"]
    top40_sizes  = compute_top40(df_filtered)
    sellers_df   = compute_sellers_pivot(df, top40_sizes, show_classes)

    if sellers_df.empty:
        st.warning(t("tab3.no_data"))
    else:
        st.caption(t("tab3.caption"))
        chart_sellers(sellers_df)

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — Динамика цен (Block 4)
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown(
        f"<div class='section-header'>{t('tab4.subtitle')}</div>",
        unsafe_allow_html=True,
    )
    st.caption(t("tab4.description"))

    history_df = compute_price_history()

    if history_df.empty:
        st.info(
            f"📂 {t('tab4.empty_title')}. "
            f"{t('tab4.empty_desc')}"
        )
        with st.expander(t("tab4.how_it_works")):
            st.markdown(t("tab4.how_it_works_text"))
    else:
        col1, col2 = st.columns([3, 1])
        with col2:
            trend_brand = st.selectbox(t("tab4.brand"), history_df["Бренд"].unique())
            trend_size  = st.selectbox(
                t("tab4.size"),
                history_df[history_df["Бренд"] == trend_brand]["Размер"].unique(),
            )
        with col1:
            st.plotly_chart(
                chart_price_trend(history_df, trend_brand, trend_size),
                use_container_width=True,
            )

        st.plotly_chart(
            chart_price_distribution(history_df),
            use_container_width=True,
        )

# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — Карта Украины (Block 5)
# ════════════════════════════════════════════════════════════════════════════
with tab5:
    from modules.ukraine_map import generate_ukraine_map_html

    st.markdown(
        f"<div class='section-header'>{t('tab5.subtitle')}</div>",
        unsafe_allow_html=True,
    )

    st.caption(t("tab5.caption"))

    map_html = generate_ukraine_map_html(df_filtered)

    # Авто-подбор высоты: даём запас, но разрешаем прокрутку если потребуется.
    st.html(map_html)
