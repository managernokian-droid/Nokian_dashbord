"""
modules/filters.py
Каскадные фильтры: каждый следующий показывает только доступные варианты.
Порядок: Класс → Сезон → Год → Тип ТС → Бренд → Модель
"""

import pandas as pd
import streamlit as st
from modules.i18n import t

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


def _get_available(df: pd.DataFrame, col: str) -> list:
    """Уникальные значения колонки в отфильтрованном df."""
    return sorted([str(v) for v in df[col].dropna().unique() if str(v).strip()])


def render_sidebar(df_raw: pd.DataFrame) -> dict:
    """
    Каскадные фильтры с умным сохранением выбранных значений.
    При изменении верхнего фильтра, нижние автоматически корректируются.
    """
    with st.sidebar:
        st.image("assets/logo.png") if __import__("pathlib").Path("assets/logo.png").exists() else None
        st.markdown(f"## {t('sidebar.filters')}")
        
        # Проверяем загружены ли фильтры из сохранённого среза
        loaded_filters = None
        if "loaded_filters" in st.session_state and st.session_state.get("load_trigger"):
            loaded_filters = st.session_state["loaded_filters"]
            st.session_state["load_trigger"] = False
            st.info("✅ Срез загружен! Нажмите 'Применить фильтры'")

        # Инициализируем session_state для сохранения состояния фильтров
        if "filter_state" not in st.session_state:
            st.session_state["filter_state"] = {}

        # ────────────────────────────────────────────────────────────────────
        # Фильтр 1: КЛАСС
        # ────────────────────────────────────────────────────────────────────
        st.markdown(f"<div class='section-header'>{t('filters.class')}</div>", unsafe_allow_html=True)
        all_classes = ["Premium", "Mid", "Econom+"]
        
        default_classes = loaded_filters.get("classes", ["Premium"]) if loaded_filters else \
                         st.session_state["filter_state"].get("classes", ["Premium"])
        
        selected_classes = st.multiselect(
            "Класс",
            options=all_classes,
            default=default_classes,
            label_visibility="collapsed",
            key=f"classes_widget_{st.session_state.get('widget_refresh', 0)}"  # ← динамический key
        )
        
        df1 = df_raw[df_raw["Класс"].isin(selected_classes)] if selected_classes else df_raw
        st.divider()

        # ────────────────────────────────────────────────────────────────────
        # Фильтр 2: СЕЗОН
        # ────────────────────────────────────────────────────────────────────
        st.markdown(f"<div class='section-header'>{t('filters.season')}</div>", unsafe_allow_html=True)
        available_seasons = _get_available(df1, "Сезон")
        
        prev_seasons = st.session_state["filter_state"].get("seasons", [])
        default_seasons = [s for s in prev_seasons if s in available_seasons]
        if not default_seasons and available_seasons:
            default_seasons = available_seasons[:1]
        
        if loaded_filters:
            default_seasons = [s for s in loaded_filters.get("seasons", []) if s in available_seasons]
        
        selected_seasons = st.multiselect(
            "Сезон",
            options=available_seasons,
            default=default_seasons,
            label_visibility="collapsed",
            key=f"seasons_widget_{st.session_state.get('widget_refresh', 0)}"
        )
        
        df2 = df1[df1["Сезон"].isin(selected_seasons)] if selected_seasons else df1

        # ────────────────────────────────────────────────────────────────────
        # Фильтр 3: ГОД ИЗГОТОВЛЕНИЯ
        # ────────────────────────────────────────────────────────────────────
        st.markdown(f"<div class='section-header'>{t('filters.year')}</div>", unsafe_allow_html=True)
        
        years_with_value = sorted(
            [str(int(y)) for y in df2["Год изготовления шин"].dropna().unique() if y > 0],
            reverse=True,
        )
        has_empty_years = (df2["Год изготовления шин"].isna() | (df2["Год изготовления шин"] == 0)).any()
        available_years_options = years_with_value + (["Не указан"] if has_empty_years else [])
        
        prev_years = st.session_state["filter_state"].get("years", [])
        default_years = [y for y in prev_years if y in available_years_options]
        if not default_years and available_years_options:
            default_years = available_years_options[:1]
        
        if loaded_filters:
            default_years = [y for y in loaded_filters.get("years", []) if y in available_years_options]
        
        selected_years = st.multiselect(
            "Год",
            options=available_years_options,
            default=default_years,
            label_visibility="collapsed",
            key=f"years_widget_{st.session_state.get('widget_refresh', 0)}"
        )
        
        if selected_years:
            if "Не указан" in selected_years:
                other_years = [y for y in selected_years if y != "Не указан"]
                if other_years:
                    df3 = df2[
                        (df2["Год изготовления шин"].astype(str).isin(other_years)) |
                        (df2["Год изготовления шин"].isna()) |
                        (df2["Год изготовления шин"] == 0)
                    ]
                else:
                    df3 = df2[(df2["Год изготовления шин"].isna()) | (df2["Год изготовления шин"] == 0)]
            else:
                df3 = df2[df2["Год изготовления шин"].astype(str).isin(selected_years)]
        else:
            df3 = df2

        # ────────────────────────────────────────────────────────────────────
        # Фильтр 4: ТИП ТС
        # ────────────────────────────────────────────────────────────────────
        st.markdown(f"<div class='section-header'>{t('filters.vehicle_type')}</div>", unsafe_allow_html=True)
        available_vehicles = _get_available(df3, "Тип транспортного средства")
        
        prev_vehicles = st.session_state["filter_state"].get("vehicles", [])
        default_vehicles = [v for v in prev_vehicles if v in available_vehicles]
        if not default_vehicles:
            default_vehicles = available_vehicles
        
        if loaded_filters:
            default_vehicles = [v for v in loaded_filters.get("vehicles", []) if v in available_vehicles]
        
        selected_vehicles = st.multiselect(
            "Тип ТС",
            options=available_vehicles,
            default=default_vehicles,
            label_visibility="collapsed",
            key=f"vehicles_widget_{st.session_state.get('widget_refresh', 0)}"
        )
        
        df4 = df3[df3["Тип транспортного средства"].isin(selected_vehicles)] if selected_vehicles else df3

        # ────────────────────────────────────────────────────────────────────
        # Фильтр 5: РЕГИОН
        # ────────────────────────────────────────────────────────────────────
        st.markdown(f"<div class='section-header'>{t('filters.region')}</div>", unsafe_allow_html=True)
        available_regions = sorted([r for r in df4["Регион"].dropna().unique() if r != "Unknown"])
        
        prev_regions = st.session_state["filter_state"].get("regions", [])
        default_regions = [r for r in prev_regions if r in available_regions]
        if not default_regions:
            default_regions = available_regions
        
        if loaded_filters:
            default_regions = [r for r in loaded_filters.get("regions", []) if r in available_regions]
        
        selected_regions = st.multiselect(
            "Регион",
            options=available_regions,
            default=default_regions,
            label_visibility="collapsed",
            key=f"regions_widget_{st.session_state.get('widget_refresh', 0)}"
        )
        
        df5 = df4[df4["Регион"].isin(selected_regions)] if selected_regions else df4

        # ────────────────────────────────────────────────────────────────────
        # Фильтр 6: БРЕНД
        # ────────────────────────────────────────────────────────────────────
        st.markdown(f"<div class='section-header'>{t('filters.brand')}</div>", unsafe_allow_html=True)
        available_brands = _get_available(df5, "Бренд")
        
        prev_brands = st.session_state["filter_state"].get("brands", [])
        default_brands = [b for b in prev_brands if b in available_brands]
        if not default_brands and "Nokian" in available_brands:
            default_brands = ["Nokian"]
        elif not default_brands:
            default_brands = available_brands[:1]
        
        if loaded_filters:
            default_brands = [b for b in loaded_filters.get("brands", []) if b in available_brands]
        
        selected_brands = st.multiselect(
            "Бренд",
            options=available_brands,
            default=default_brands,
            label_visibility="collapsed",
            key=f"brands_widget_{st.session_state.get('widget_refresh', 0)}"
        )
        
        df6 = df5[df5["Бренд"].isin(selected_brands)] if selected_brands else df5

        # ────────────────────────────────────────────────────────────────────
        # Фильтр 7: ПОСТАВЩИК
        # ────────────────────────────────────────────────────────────────────
        st.markdown(f"<div class='section-header'>{t('filters.supplier')}</div>", unsafe_allow_html=True)
        available_suppliers = _get_available(df6, "Поставщик")
        
        prev_suppliers = st.session_state["filter_state"].get("suppliers", [])
        default_suppliers = [s for s in prev_suppliers if s in available_suppliers]
        if not default_suppliers and len(available_suppliers) <= 5:
            default_suppliers = available_suppliers
        
        if loaded_filters:
            default_suppliers = [s for s in loaded_filters.get("suppliers", []) if s in available_suppliers]
        
        selected_suppliers = st.multiselect(
            "Поставщик",
            options=available_suppliers,
            default=default_suppliers,
            label_visibility="collapsed",
            key=f"suppliers_widget_{st.session_state.get('widget_refresh', 0)}"
        )
        
        df7 = df6[df6["Поставщик"].isin(selected_suppliers)] if selected_suppliers else df6

        # ────────────────────────────────────────────────────────────────────
        # Фильтр 8: МОДЕЛЬ
        # ────────────────────────────────────────────────────────────────────
        st.markdown(f"<div class='section-header'>{t('filters.model')}</div>", unsafe_allow_html=True)
        available_models = _get_available(df7, "Модель")
        
        prev_models = st.session_state["filter_state"].get("models", [])
        default_models = [m for m in prev_models if m in available_models]
        if not default_models and len(available_models) <= 3:
            default_models = available_models
        
        if loaded_filters:
            default_models = [m for m in loaded_filters.get("models", []) if m in available_models]
        
        selected_models = st.multiselect(
            "Модель",
            options=available_models,
            default=default_models,
            label_visibility="collapsed",
            key=f"models_widget_{st.session_state.get('widget_refresh', 0)}"
        )

        st.divider()

        # ────────────────────────────────────────────────────────────────────
        # СТРАНА (опционально)
        # ────────────────────────────────────────────────────────────────────
        st.markdown(f"<div class='section-header'>{t('filters.country')}</div>", unsafe_allow_html=True)
        df_for_country = df7[df7["Модель"].isin(selected_models)] if selected_models else df7
        available_countries = _get_available(df_for_country, "Страна производитель")
        
        prev_countries = st.session_state["filter_state"].get("countries", [])
        default_countries = [c for c in prev_countries if c in available_countries]
        
        if loaded_filters:
            default_countries = [c for c in loaded_filters.get("countries", []) if c in available_countries]
        
        selected_countries = st.multiselect(
            "Страна",
            options=available_countries,
            default=default_countries,
            label_visibility="collapsed",
            key=f"countries_widget_{st.session_state.get('widget_refresh', 0)}"
        )

        st.divider()

        # ────────────────────────────────────────────────────────────────────
        # МЕТРИКА ЦЕНЫ
        # ────────────────────────────────────────────────────────────────────
        st.markdown(f"<div class='section-header'>{t('filters.metric')}</div>", unsafe_allow_html=True)
        
        default_metric = loaded_filters.get("metric", "Медиана") if loaded_filters else \
                        st.session_state["filter_state"].get("metric", "Медиана")
        
        metric = st.radio(
            "Метрика",
            options=["Медиана", "Мин от 4 шт"],
            index=0 if default_metric == "Медиана" else 1,
            help=(
                "**Медиана** — серединное значение всех цен бренда в размере.\n\n"
                "**Мин от 4 шт** — минимальная цена среди позиций с остатком ≥4 шт."
            ),
            label_visibility="collapsed",
            key=f"metric_widget_{st.session_state.get('widget_refresh', 0)}"
        )

        st.divider()

        # ────────────────────────────────────────────────────────────────────
        # КОНКУРЕНТЫ ДЛЯ СРАВНЕНИЯ
        # ────────────────────────────────────────────────────────────────────
        st.markdown(f"<div class='section-header'>{t('filters.competitors')}</div>", unsafe_allow_html=True)
        
        all_comp_brands = []
        for cls in selected_classes:
            all_comp_brands.extend([b for b in BRAND_CLASSES.get(cls, []) if b != "Nokian"])
        all_comp_brands = sorted(list(set(all_comp_brands)))
        
        prev_comps = st.session_state["filter_state"].get("comps", [])
        default_comps = [c for c in prev_comps if c in all_comp_brands]
        if not default_comps:
            default_comps = all_comp_brands[:5] if len(all_comp_brands) >= 5 else all_comp_brands
        
        if loaded_filters:
            default_comps = [c for c in loaded_filters.get("comps", []) if c in all_comp_brands]
        
        comps = st.multiselect(
            "Конкуренты",
            options=all_comp_brands,
            default=default_comps,
            label_visibility="collapsed",
            key=f"comps_widget_{st.session_state.get('widget_refresh', 0)}"
        )

        st.divider()

        # ────────────────────────────────────────────────────────────────────
        # КНОПКА ПРИМЕНИТЬ
        # ────────────────────────────────────────────────────────────────────
        apply_clicked = st.button(
            f"✅ {t('sidebar.apply')}",
            use_container_width=True,
            type="primary",
        )

        # Сохраняем текущее состояние фильтров
        st.session_state["filter_state"] = {
            "classes": selected_classes,
            "seasons": selected_seasons,
            "years": selected_years,
            "vehicles": selected_vehicles,
            "regions": selected_regions,
            "brands": selected_brands,
            "suppliers": selected_suppliers,
            "models": selected_models,
            "countries": selected_countries,
            "metric": metric,
            "comps": comps,
        }

        if apply_clicked and "current_slice_name" in st.session_state:
            del st.session_state["current_slice_name"]

        st.divider()

        # ────────────────────────────────────────────────────────────────────
        # СОХРАНЁННЫЕ СРЕЗЫ
        # ────────────────────────────────────────────────────────────────────
        from modules.saved_filters import (
            save_filter_set, load_filter_set, list_saved_filters,
            delete_filter_set, rename_filter_set
        )
        
        st.markdown("<div class='section-header'>📁 Сохранённые срезы</div>", unsafe_allow_html=True)
        
        saved_list = list_saved_filters()
        
        if saved_list:
            saved_names = [s["name"] for s in saved_list]
            
            selected_saved = st.selectbox(
                "Выберите срез",
                options=[""] + saved_names,
                format_func=lambda x: "— выберите срез —" if x == "" else x,
                label_visibility="collapsed",
            )

            # Показываем дату создания выбранного среза
            if selected_saved:
                saved_item = next((s for s in saved_list if s["name"] == selected_saved), None)
                if saved_item and saved_item.get("created_at"):
                    from datetime import datetime
                    created = datetime.fromisoformat(saved_item["created_at"])
                    st.caption(f"Создан: {created.strftime('%d.%m.%Y %H:%M')}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📥 Загрузить", disabled=not selected_saved, use_container_width=True):
                    loaded = load_filter_set(selected_saved)
                    if loaded:
                        st.session_state["loaded_filters"] = loaded
                        st.session_state["load_trigger"] = True
                        st.session_state["current_slice_name"] = selected_saved
                        
                        # КРИТИЧНО: Обновляем filter_state чтобы виджеты обновились
                        st.session_state["filter_state"] = loaded.copy()
                        
                        # Инкрементируем счётчик для форсированного обновления виджетов
                        if "widget_refresh" not in st.session_state:
                            st.session_state["widget_refresh"] = 0
                        st.session_state["widget_refresh"] += 1
                        
                        st.rerun()
            
            with col2:
                if st.button("✏️ Переим.", disabled=not selected_saved, use_container_width=True):
                    st.session_state["rename_mode"] = selected_saved
            
            with col3:
                if st.button("🗑️ Удалить", disabled=not selected_saved, use_container_width=True):
                    if delete_filter_set(selected_saved):
                        st.success(f"Удалено: {selected_saved}")
                        st.rerun()
            
            if "rename_mode" in st.session_state and st.session_state["rename_mode"]:
                new_name = st.text_input(
                    "Новое имя:",
                    value=st.session_state["rename_mode"],
                    key="rename_input"
                )
                col_ok, col_cancel = st.columns(2)
                with col_ok:
                    if st.button("✅ OK", use_container_width=True):
                        if rename_filter_set(st.session_state["rename_mode"], new_name):
                            st.success("Переименовано!")
                            del st.session_state["rename_mode"]
                            st.rerun()
                with col_cancel:
                    if st.button("❌ Отмена", use_container_width=True):
                        del st.session_state["rename_mode"]
                        st.rerun()
        
        st.divider()
        
        # Сохранение текущего среза
        st.markdown("<div class='section-header'>💾 Сохранить текущий срез</div>", unsafe_allow_html=True)
        
        save_name = st.text_input(
            "Название среза",
            placeholder="Например: Premium зима 2025",
            label_visibility="collapsed",
        )
        
        if st.button("💾 Сохранить срез", use_container_width=True, disabled=not save_name):
            current_filters = {
                "classes": selected_classes,
                "seasons": selected_seasons,
                "years": selected_years,
                "vehicles": selected_vehicles,
                "regions": selected_regions,
                "brands": selected_brands,
                "suppliers": selected_suppliers,
                "models": selected_models,
                "countries": selected_countries,
                "metric": metric,
                "comps": comps,
            }
            
            if save_filter_set(save_name, current_filters):
                st.success(f"✅ Срез '{save_name}' сохранён!")
                st.rerun()

        st.caption(
            "Данные обновляются 2 раза в месяц.\n"
            "При замене файла кэш сбрасывается автоматически."
        )

    return {
        "classes":        selected_classes,
        "seasons":        selected_seasons,
        "years":          selected_years,
        "vehicles":       selected_vehicles,
        "regions":        selected_regions,
        "brands":         selected_brands,
        "suppliers":      selected_suppliers,
        "models":         selected_models,
        "countries":      selected_countries,
        "metric":         metric,
        "comps":          comps,
        "apply_clicked":  apply_clicked,
    }