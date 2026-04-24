# Nokian Price Intelligence Dashboard

Дашборд позиционирования Nokian относительно конкурентов.
Стек: Python · Streamlit · Plotly · Pandas · XLSX/Parquet

---

## Структура проекта

```
tire_dashboard/
├── app.py                  ← главный файл, точка входа
├── requirements.txt        ← зависимости
├── .streamlit/
│   └── config.toml         ← настройки Streamlit (порт, тема)
├── modules/
│   ├── __init__.py
│   ├── load_data.py        ← загрузка XLSX + кэш Parquet
│   ├── filters.py          ← сайдбар с фильтрами
│   ├── transforms.py       ← бизнес-логика: Δ%, ТОП-40, пивоты, история
│   └── charts.py           ← все Plotly-графики
├── scripts/
│   └── snapshot.py         ← снапшот цен при обновлении данных
├── data/
│   ├── tires.xlsx          ← ← ← СЮДА кладёте ваш файл
│   ├── tires.parquet       ← создаётся автоматически (кэш)
│   └── history/
│       ├── 2025-01-15.parquet
│       ├── 2025-02-01.parquet
│       └── ...             ← история снапшотов (для блока динамики)
└── assets/
    └── logo.png            ← опционально: логотип в сайдбаре
```

---

## Быстрый старт (первый запуск)

### 1. Требования
- Python 3.10 или новее
- pip

### 2. Установка

```bash
# Клонируйте / скопируйте папку проекта
cd tire_dashboard

# Создайте виртуальное окружение
python -m venv venv

# Активируйте (Windows)
venv\Scripts\activate

# Активируйте (Mac / Linux)
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### 3. Положите файл данных

Скопируйте ваш `tires.xlsx` в папку `data/`:
```
tire_dashboard/data/tires.xlsx
```

### 4. Запуск

```bash
streamlit run app.py
```

Откроется браузер: `http://localhost:8501`

---

## Обновление данных (2 раза в месяц)

Каждый раз когда обновляется база:

### Шаг 1 — Замените файл
Скопируйте новый `tires.xlsx` в папку `data/`, заменив старый.

### Шаг 2 — Сохраните снапшот истории цен
```bash
python scripts/snapshot.py
```

Скрипт:
- Сохранит снапшот цен в `data/history/YYYY-MM-DD.parquet`
- Удалит старый кэш `data/tires.parquet`
- При следующем открытии дашборда данные автоматически пересоберутся

### Шаг 3 — Перезапустите дашборд (если он был открыт)
Нажмите **R** в браузере или кнопку "Rerun" — кэш пересоберётся автоматически за ~15–20 сек.

---

## Расширение и доработка

### Добавить новый блок визуализации

1. В `modules/transforms.py` добавьте функцию `compute_новый_блок(df, ...) -> pd.DataFrame`
2. В `modules/charts.py` добавьте функцию `chart_новый_блок(data) -> go.Figure`
3. В `app.py` добавьте новый таб:
```python
tab5, = st.tabs(["🆕 Новый блок"])
with tab5:
    data = compute_новый_блок(df_filtered, ...)
    st.plotly_chart(chart_новый_блок(data), use_container_width=True)
```

### Добавить новый фильтр

В `modules/filters.py` добавьте виджет в функцию `render_sidebar()` и верните значение в словаре `filters`. В `app.py` примените его к маске `mask`.

### Изменить список брендов по классам

В `modules/filters.py` отредактируйте словарь `BRAND_CLASSES`.
Тот же словарь продублирован в `modules/transforms.py` — обновите оба.

---

## Производительность

| Ситуация | Время загрузки |
|---|---|
| Первый запуск (XLSX → Parquet) | ~15–20 сек |
| Повторные открытия (из Parquet) | ~2–4 сек |
| Переключение фильтров | мгновенно |

**Важно:** При 160k строк держите `@st.cache_data(ttl=1800)` на `load_data()`.
Если дашборд открыт несколько часов — TTL сбросит кэш и перечитает Parquet (~2 сек).

---

## Сетевой доступ (несколько пользователей)

Чтобы дашборд был доступен другим сотрудникам по сети:

1. В `.streamlit/config.toml` измените:
```toml
address = "0.0.0.0"
```

2. Запустите:
```bash
streamlit run app.py
```

3. Сообщите коллегам адрес: `http://ВАШ_IP:8501`

Найти ваш IP: Windows → `ipconfig`, Mac/Linux → `ifconfig`

---

## Возможные проблемы

**`ModuleNotFoundError`** — не активировано виртуальное окружение.
Выполните `venv\Scripts\activate` (Windows) или `source venv/bin/activate` (Mac/Linux).

**`FileNotFoundError: data/tires.xlsx`** — файл не в папке `data/`. Проверьте путь.

**Дашборд медленно загружается повторно** — увеличьте TTL в `load_data.py`:
```python
@st.cache_data(ttl=7200)  # 2 часа
```

**Колонки не находятся** — в вашем XLSX могут быть лишние пробелы в заголовках.
`load_data.py` делает `str.strip()` автоматически, но если проблема остаётся —
откройте файл и вручную проверьте заголовки первой строки.

**Блок динамики пустой** — это нормально при первом запуске. Запустите
`python scripts/snapshot.py` после следующего обновления данных.
