# Руководство по добавлению переводов

Когда вы добавляете новые функции, блоки или сообщения, нужно добавить переводы. Вот пошаговый процесс:

---

## 📋 Процесс добавления переводов

### Шаг 1: Определите текст, который нужно переводить

Для каждого пользовательского текста в коде нужен перевод. Примеры:
- ✅ Названия табов, заголовки, лейблы фильтров
- ✅ Сообщения об ошибках, предупреждения, подсказки
- ✅ Подписи графиков, оси диаграмм
- ❌ Технические имена столбцов (они остаются на русском)
- ❌ Комментарии в коде

### Шаг 2: Добавьте ключи в JSON файлы переводов

**Файлы переводов:**
- `locales/ru.json` - Русский
- `locales/en.json` - Английский
- `locales/uk.json` - Украинский

**Структура JSON (используйте логичную иерархию):**

```json
{
  "section_name": {
    "key_name": "Текст на русском"
  }
}
```

**Примеры секций:**
- `"app"` - приложение в целом
- `"tabs"` - названия табов
- `"filters"` - фильтры
- `"charts"` - графики
- `"messages"` - сообщения (ошибки, предупреждения)
- `"export"` - экспорт
- `"map"` - карта

### Шаг 3: Обновите все три файла одновременно

**Важно!** Ключи должны быть идентичны во всех трех файлах, различаться должны только значения:

```json
// locales/ru.json
{
  "my_new_feature": {
    "title": "Мой новый блок"
  }
}

// locales/en.json
{
  "my_new_feature": {
    "title": "My New Block"
  }
}

// locales/uk.json
{
  "my_new_feature": {
    "title": "Мій новий блок"
  }
}
```

### Шаг 4: Используйте переводы в коде

В вашем Python коде импортируйте и используйте функцию `t()`:

```python
from modules.i18n import t

# Простой перевод
st.title(t("my_new_feature.title"))

# Перевод с переменными
st.write(t_format("my_new_feature.caption", count=42))

# В Plotly графиках
fig.update_layout(
    title=t("charts.my_new_chart.title"),
    xaxis=dict(title=t("chart_labels.price"))
)
```

---

## 🎯 Примеры: от простого к сложному

### Пример 1: Добавить новый таб

**Шаг 1: Обновить JSON**
```json
// Добавить в каждый файл locales/*.json:
"tabs": {
  "my_new_tab": "🆕 Мой новый таб"  // ru.json
  "my_new_tab": "🆕 My New Tab"      // en.json
  "my_new_tab": "🆕 Мій новий таб"   // uk.json
}
```

**Шаг 2: Использовать в app.py**
```python
from modules.i18n import t

tab1, tab2, tab3, tab_new = st.tabs([
    t("tabs.position"),
    t("tabs.heatmap"),
    t("tabs.sellers"),
    t("tabs.my_new_tab"),  # ← вот так
])
```

---

### Пример 2: Добавить новый фильтр

**Шаг 1: Обновить JSON**
```json
// locales/*.json
"filters": {
  "my_filter": "12. Мой фильтр"  // ru.json
  "my_filter": "12. My Filter"    // en.json
  "my_filter": "12. Мій фільтр"   // uk.json
}
```

**Шаг 2: Использовать в modules/filters.py**
```python
from modules.i18n import t

st.markdown(f"<div class='section-header'>{t('filters.my_filter')}</div>", 
            unsafe_allow_html=True)

selected_values = st.multiselect(
    t("filters.my_filter"),  # ← лейбл
    options=available_options,
    label_visibility="collapsed",
)
```

---

### Пример 3: Добавить новый график с KPI

**Шаг 1: Обновить JSON**
```json
// locales/*.json
"charts": {
  "my_new_chart": {
    "title": "Мой новый график",
    "metric1": "Метрика 1",
    "metric2": "Метрика 2"
  }
}
```

**Шаг 2: Использовать в modules/charts.py**
```python
from modules.i18n import t

def chart_my_new(data):
    # KPI метрики
    c1, c2 = st.columns(2)
    c1.metric(t("charts.my_new_chart.metric1"), value1)
    c2.metric(t("charts.my_new_chart.metric2"), value2)
    
    # График
    fig = px.bar(data)
    fig.update_layout(
        title=t("charts.my_new_chart.title"),
        xaxis_title=t("chart_labels.price"),
        yaxis_title=t("chart_labels.stock")
    )
    return fig
```

---

### Пример 4: Сообщения об ошибке

**Шаг 1: Обновить JSON**
```json
// locales/*.json
"messages": {
  "no_data": "Нет данных"  // ru.json
  "no_data": "No data"      // en.json
  "no_data": "Немає даних"  // uk.json
}
```

**Шаг 2: Использовать в коде**
```python
if df.empty:
    st.warning(t("messages.no_data"))
```

---

## 🔧 Полезные советы

### Совет 1: Структурируйте иерархию ключей

❌ Плохо:
```json
{
  "text1": "Мой новый блок",
  "text2": "Мой новый таб"
}
```

✅ Хорошо:
```json
{
  "my_new_feature": {
    "title": "Мой новый блок",
    "tab": "Мой новый таб"
  }
}
```

### Совет 2: Используйте переменные в переводах

Если нужна подстановка значений, используйте `t_format()`:

```json
// locales/ru.json
"charts": {
  "heatmap": {
    "caption": "ТОП-{count} размеров · {comps} конкурентов"
  }
}
```

```python
# В коде
st.caption(t_format("charts.heatmap.caption", count=40, comps=5))
# Результат: "ТОП-40 размеров · 5 конкурентов"
```

### Совет 3: Проверьте все три языка

Перед коммитом убедитесь:
- ✅ Все три файла (ru.json, en.json, uk.json) обновлены
- ✅ Ключи идентичны во всех файлах
- ✅ Нет пропущенных языков
- ✅ Синтаксис JSON корректен

```bash
# Проверить синтаксис JSON
python -m json.tool locales/ru.json > /dev/null && echo "OK"
python -m json.tool locales/en.json > /dev/null && echo "OK"
python -m json.tool locales/uk.json > /dev/null && echo "OK"
```

### Совет 4: Комментируйте контекст в коде

```python
# KPI для сравнения цен Nokian vs конкуренты
c1.metric(
    t("charts.kpi.nokian_price"),  # "Цена Nokian"
    f"{price:,} ₴"
)
```

---

## 📝 Чек-лист для добавления новой функции

- [ ] **1. Определены все текстовые строки** для перевода
- [ ] **2. Добавлены ключи в locales/ru.json**
- [ ] **3. Добавлены ключи в locales/en.json** (идентичные ключи)
- [ ] **4. Добавлены ключи в locales/uk.json** (идентичные ключи)
- [ ] **5. Синтаксис JSON проверен** (используйте python -m json.tool)
- [ ] **6. В коде импортирована функция t()**:
  ```python
  from modules.i18n import t
  ```
- [ ] **7. Все строки заменены на t("key")**
- [ ] **8. Протестирована смена языков** (все три языка работают)
- [ ] **9. Коммит выполнен** с описанием переводов

---

## 🚀 Быстрый старт для новой функции

### Шаблон для добавления нового блока:

**1. Добавьте в locales/ru.json:**
```json
"my_feature": {
  "title": "Название",
  "subtitle": "Подзаголовок",
  "label": "Лейбл",
  "error": "Сообщение об ошибке"
}
```

**2. Скопируйте структуру в en.json и uk.json**, переведите значения

**3. В Python коде:**
```python
from modules.i18n import t

st.title(t("my_feature.title"))
st.caption(t("my_feature.subtitle"))
st.write(t("my_feature.label"))

if error:
    st.error(t("my_feature.error"))
```

**4. Готово!** Язык будет меняться автоматически из селектора в сайдбаре

---

## 💡 Часто задаваемые вопросы

**Q: Что если я забыл добавить перевод?**
A: Будет показан ключ в квадратных скобках: `[my_feature.title]`. Исправьте в JSON файлах.

**Q: Можно ли добавить новый язык?**
A: Да! Создайте `locales/fr.json`, добавьте все ключи, обновите `modules/i18n.py`:
```python
SUPPORTED_LANGUAGES = {
    "Русский": "ru",
    "English": "en",
    "Українська": "uk",
    "Français": "fr",  # ← новый язык
}
```

**Q: Как организовать большое количество переводов?**
A: Используйте логичную иерархию:
```json
{
  "tab1": { ... },
  "tab2": { ... },
  "tab3": { ... },
  "common": {
    "yes": "Да",
    "no": "Нет"
  }
}
```

**Q: Нужно ли переводить названия переменных?**
A: Нет! Только пользовательский текст. Переменные, SQL, технические имена остаются как есть.

---

## 📚 Ссылки

- Модуль i18n: `modules/i18n.py`
- Файлы переводов: `locales/*.json`
- Функции: `t(key)` и `t_format(key, **kwargs)`
- CLAUDE.md: раздел "Multi-Language Support"
