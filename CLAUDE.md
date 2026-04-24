# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Nokian Price Intelligence Dashboard** — a Streamlit-based analytical tool for competitive pricing analysis of Nokian tires against competitors. The dashboard processes XLSX tire catalog data, caches it as Parquet, and provides interactive filtering, price comparison visualizations, and regional sales mapping.

### Core Stack
- **Framework:** Streamlit (web UI)
- **Data:** Pandas + Parquet (caching) + XLSX (source)
- **Viz:** Plotly (charts)
- **Languages:** Python 3.10+

---

## Development Setup

### First Run
```bash
python -m venv venv
source venv/bin/activate          # Linux/Mac
# or: venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### Running the Dashboard
```bash
source venv/bin/activate
streamlit run app.py
```
Launches on `http://localhost:8501`

### Data Updates (bi-monthly)
```bash
# 1. Replace tires.xlsx in Data/ folder
# 2. Save a snapshot for price history:
python scripts/snapshot.py

# 3. Refresh dashboard (press R in browser or restart)
```

---

## Architecture & Data Flow

### High-Level Design
```
Data Input (tires.xlsx)
    ↓
load_data.py [XLSX → Parquet cache]
    ↓
app.py [Main UI orchestration]
    ├─ filters.py [Sidebar filters + cascading logic]
    ├─ transforms.py [Business calculations]
    ├─ charts.py [Plotly visualizations]
    ├─ regions.py [City → Region mapping]
    ├─ ukraine_map.py [Interactive regional map]
    ├─ saved_filters.py [Filter state persistence]
    └─ export_excel.py [Excel export for Tab 2]
```

### Key Components

#### `modules/load_data.py`
- **Purpose:** Data loading and intelligent caching
- **Key Logic:**
  - Reads XLSX on first run, converts to Parquet for speed (~15-20s first, ~2-4s cached)
  - Renames columns, converts numeric types, handles dates
  - Validates: removes rows without Brand or Price, filters stock ≥ 1
  - `load_data()` uses `@st.cache_data(ttl=1800)` — refreshes every 30 min if dashboard runs long
  - `invalidate_cache()` — called by snapshot.py to force reload
- **Data Path:** `Data/tires.xlsx` → `Data/tires.parquet`

#### `modules/filters.py`
- **Purpose:** Sidebar UI and cascading filter logic
- **Behavior:**
  - Filters cascade: Class → Season → Year → Vehicle Type → Brand → Model → Country → Suppliers
  - Each lower filter shows only available options given higher selections
  - `BRAND_CLASSES` dict maps 3 class tiers (Premium/Mid/Econom+) to brands
  - Saves selected filters to session state and optionally to JSON files (`Data/saved_filters/`)
  - Returns dict with keys: `classes`, `seasons`, `years`, `vehicles`, `brands`, `models`, `countries`, `suppliers`, `regions`, `comps` (competitor brands), `metric`, `apply_clicked`

#### `modules/transforms.py`
- **Purpose:** All data transformations and business logic
- **Key Functions:**
  - `build_size_col()` — combines Width/Height/Diameter into "205/55 R16" format
  - `compute_waterfall()` — Nokian vs competitors price comparison (for Tab 1)
  - `compute_top40()` — ranks tire sizes by total stock (for Tab 2)
  - `compute_heatmap_pivot()` — creates pivot tables for price delta heatmap (Tab 2)
  - `compute_sellers_pivot()` — supplier distribution by size/brand (Tab 3)
  - `compute_price_history()` — reads historical snapshots from `Data/history/` (Tab 4)
- **Note:** `BRAND_CLASSES` dict duplicated here — must stay in sync with `filters.py`

#### `modules/charts.py`
- **Purpose:** All Plotly visualizations
- **Key Functions:**
  - `chart_waterfall()` — horizontal bar comparison chart
  - `chart_kpi_row()` — 4 metrics (our price, cheaper/more expensive count, avg Δ%)
  - `chart_heatmap()` — color-coded price deltas (green = cheaper, red = more expensive)
  - `chart_sellers()` — supplier count distribution
  - `chart_price_trend()` — line chart of price over time
  - `chart_price_distribution()` — histogram of price changes between snapshots
- **Color Scheme:** `NOKIAN_COLOR = "#185FA5"`, heatmap uses green→white→red scale

#### `modules/regions.py`
- **Purpose:** Maps Ukrainian cities to regions
- **Key Function:** `get_region(city)` — lookup table for geographic grouping

#### `modules/ukraine_map.py`
- **Purpose:** Interactive Folium map showing stock by city/region
- **Key Function:** `generate_ukraine_map_html()` — returns HTML string for `st.components.v1.html()`

#### `modules/saved_filters.py`
- **Purpose:** Persistence of filter presets
- **Files Saved:** `Data/saved_filters/*.json`

#### `modules/export_excel.py`
- **Purpose:** Export heatmap data to Excel for Tab 2
- **Key Function:** `export_heatmap_to_excel()` — returns bytes for download button

#### `app.py` (Main Entry Point)
- **Structure:** 5 tabs in the dashboard
  1. **Tab 1 (📍 Позиция модели):** Waterfall chart + KPI metrics
  2. **Tab 2 (🗺️ ТОП-40 тепловая карта):** Heatmap + Excel export
  3. **Tab 3 (🏪 Продавцы):** Supplier distribution
  4. **Tab 4 (📈 Динамика цен):** Price trends & history
  5. **Tab 5 (🗺️ Карта):** Ukraine map
- **Filter Application:** Builds mask with cascading conditions, filters df_raw → df_filtered
- **Data Cleaning:** Removes stock < 4 units, adds Region column via `get_region()`

---

## Multi-Language Support

The dashboard supports full internationalization (i18n) with translations for three languages:

### Supported Languages
- 🇷🇺 **Русский** (Russian)
- 🇬🇧 **English**
- 🇺🇦 **Українська** (Ukrainian)

### How It Works
- **Translation files:** `locales/ru.json`, `locales/en.json`, `locales/uk.json`
- **i18n module:** `modules/i18n.py` provides `t(key)` and `t_format(key, **kwargs)` functions
- **Language selector:** Available in sidebar, automatically triggers `st.rerun()` to refresh UI
- **Session storage:** Selected language saved in `st.session_state['language']`

### Adding New Translations
1. Add your text to all three JSON files in `locales/`:
   ```json
   {
     "section": {
       "key": "Your text here"
     }
   }
   ```
2. In Python code, use:
   ```python
   from modules.i18n import t
   st.write(t("section.key"))
   # Or with variables:
   st.write(t_format("section.key_with_vars", count=10))
   ```

### Translated Components
- ✅ App titles and descriptions
- ✅ Tab names
- ✅ All filter labels (11 filters)
- ✅ KPI metrics (4 metrics with 11 different labels)
- ✅ Chart titles and axis labels
- ✅ Excel export sheet names
- ✅ Error and warning messages
- ✅ Map display messages

---

## Common Development Tasks

### Add a New Filter
1. Add UI widget in `modules/filters.py` → `render_sidebar()`
2. Append key to returned filter dict
3. In `app.py`, add condition to the `mask` logic (lines 70-94)

### Add a New Visualization Tab
1. In `modules/transforms.py`: add `compute_newtab(df, ...) → pd.DataFrame`
2. In `modules/charts.py`: add `chart_newtab(data) → go.Figure`
3. In `app.py`: add tab in `st.tabs()` list and render:
   ```python
   with tabn:
       data = compute_newtab(df_filtered, ...)
       st.plotly_chart(chart_newtab(data), use_container_width=True)
   ```

### Update Brand Classes
Edit `BRAND_CLASSES` dict in **both** `modules/filters.py` AND `modules/transforms.py` (currently lines 10-24 in each).

### Fix Data Column Names
If XLSX has whitespace or renamed columns:
1. Check the error message for the column name
2. Update `COLUMN_MAP` in `modules/load_data.py` (lines 9-26)
3. Run `invalidate_cache()` or delete `Data/tires.parquet` to rebuild

### Cache & Performance
- First load (XLSX → Parquet): ~15–20s
- Cached loads (Parquet): ~2–4s
- Filter switching: instant
- TTL: 1800s (30 min) — if dashboard open >30 min, cache auto-refreshes
- To force rebuild: `python scripts/snapshot.py` (also saves historical snapshot)

---

## Testing & Validation

**No formal test suite exists.** Manual testing approach:

1. **Data Load:** Verify Parquet is created and same row count as XLSX
2. **Filters:** Select each class/season/brand, ensure cascading logic works
3. **Charts:** Spot-check Tab 1–5 for correct aggregation and visual clarity
4. **Excel Export (Tab 2):** Download and verify pivot data matches heatmap
5. **Price History (Tab 4):** Run `python scripts/snapshot.py`, verify new date appears

---

## Important Notes

### Column Naming
- XLSX column names are case-sensitive and must match `COLUMN_MAP` in `load_data.py`
- Automatic `str.strip()` removes whitespace from headers
- If a column is missing, the dashboard will silently skip related features (e.g., no "Регион" → no regional filtering)

### Data Validation
- Rows with no Brand or Price = 0 are dropped in `load_data.py`
- Rows with stock < 4 are dropped in `app.py` (line 53)
- These are business rules; change them if requirements evolve

### Regional Mapping
- `regions.py` has a hardcoded lookup table of Ukrainian cities → regions
- Cities not in the map will get region = "Невідомий"
- To add new cities, edit the `REGION_MAP` dict in `modules/regions.py`

### Performance Limits
- Dashboard tested with ~160k rows (tires.xlsx)
- Parquet caching essential for responsiveness
- Heatmap computation (Tab 2) is the slowest operation
- If >1MB xlsx, consider pre-filtering in the source file

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: modules` | venv not activated | `source venv/bin/activate` |
| `FileNotFoundError: Data/tires.xlsx` | Wrong file path or missing file | Check file exists in `Data/` folder |
| Filters show "no data" | Mask filters too restrictively | Check cascading logic in filters.py |
| Heatmap (Tab 2) blank | No competitor brands selected | Select competitors in "Конкуренты" widget |
| Price history (Tab 4) empty | No snapshots saved | Run `python scripts/snapshot.py` after data update |
| Slow reload after 30 min | TTL cache expiration | Normal; increases to ~2-4s; adjust `ttl=7200` in load_data.py if needed |
