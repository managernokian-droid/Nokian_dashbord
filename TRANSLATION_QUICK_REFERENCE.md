# 🌍 Шпаргалка по переводам (быстрый старт)

## Когда добавляете новую функцию, следуйте этому шаблону:

---

## 1️⃣ Обновить JSON файлы (одновременно все три!)

### Добавить в `locales/ru.json`:
```json
"my_new_feature": {
  "title": "Название блока",
  "subtitle": "Подзаголовок",
  "button": "Кнопка",
  "error": "Ошибка"
}
```

### Добавить в `locales/en.json`:
```json
"my_new_feature": {
  "title": "Block Title",
  "subtitle": "Subtitle",
  "button": "Button",
  "error": "Error"
}
```

### Добавить в `locales/uk.json`:
```json
"my_new_feature": {
  "title": "Назва блоку",
  "subtitle": "Підзаголовок",
  "button": "Кнопка",
  "error": "Помилка"
}
```

---

## 2️⃣ Используйте в коде

```python
from modules.i18n import t, t_format

# Простые переводы
st.title(t("my_new_feature.title"))
st.caption(t("my_new_feature.subtitle"))
st.button(t("my_new_feature.button"))

if error:
    st.error(t("my_new_feature.error"))

# С переменными
st.write(t_format("my_new_feature.message", count=42))
# JSON: "message": "Найдено {count} элементов"
# Результат: "Найдено 42 элемента"
```

---

## 3️⃣ Примеры реальных случаев

### Случай 1: Новая вкладка
```json
// locales/*.json
"tabs": {
  "analytics": "📊 Аналитика"  // ru
  "analytics": "📊 Analytics"   // en
  "analytics": "📊 Аналітика"   // uk
}
```
```python
# app.py
tab_new = st.tabs([t("tabs.analytics")])
```

### Случай 2: Новый фильтр
```json
// locales/*.json
"filters": {
  "my_filter": "13. Мой фильтр"
}
```
```python
# modules/filters.py
st.markdown(f"<div class='section-header'>{t('filters.my_filter')}</div>", 
            unsafe_allow_html=True)
```

### Случай 3: Новая метрика
```json
// locales/*.json
"charts": {
  "metrics": {
    "my_metric": "Моя метрика"
  }
}
```
```python
# modules/charts.py
st.metric(t("charts.metrics.my_metric"), value=123)
```

### Случай 4: Сообщение об ошибке
```json
// locales/*.json
"messages": {
  "custom_error": "Что-то пошло не так"
}
```
```python
st.error(t("messages.custom_error"))
```

---

## ⚡ Самые распространённые ошибки

❌ **Ошибка 1: Разные ключи в разных файлах**
```json
// ru.json
"feature": { "title": "..." }

// en.json  
"feature": { "label": "..." }  // ← НЕПРАВИЛЬНО! key должен быть "title"
```

❌ **Ошибка 2: Забыли обновить один из файлов**
```json
// ru.json - обновлён ✅
// en.json - обновлён ✅
// uk.json - ЗАБЫЛИ! ❌
```

❌ **Ошибка 3: Синтаксис JSON неправильный**
```json
"feature": {
  "title": "Текст",  // ← запятая здесь нужна
  "desc": "Описание"
}
```

---

## ✅ Проверка перед коммитом

```bash
# 1. Проверить синтаксис JSON
python -m json.tool locales/ru.json > /dev/null && echo "ru.json ✅"
python -m json.tool locales/en.json > /dev/null && echo "en.json ✅"
python -m json.tool locales/uk.json > /dev/null && echo "uk.json ✅"

# 2. Проверить что приложение запускается
streamlit run app.py

# 3. Переключить язык в сайдбаре и проверить что новый текст показывается
```

---

## 📊 Структура JSON (рекомендуемая)

```json
{
  "app": {},           // Общие настройки приложения
  "tabs": {},          // Названия вкладок
  "filters": {},       // Фильтры (12+ фильтров)
  "charts": {          // Графики
    "kpi": {},           // KPI метрики
    "waterfall": {},     // Waterfall chart
    "heatmap": {},       // Тепловая карта
    // ... другие графики
  },
  "export": {},        // Экспорт (Excel листы)
  "map": {},           // Карта
  "messages": {},      // Ошибки и предупреждения
  "chart_labels": {},  // Общие лейблы для графиков
  "sidebar": {}        // Элементы сайдбара
}
```

---

## 🎯 Минимальный чек-лист (30 секунд)

- [ ] Добавлен в ru.json ✅
- [ ] Добавлен в en.json ✅
- [ ] Добавлен в uk.json ✅
- [ ] JSON синтаксис правильный (`python -m json.tool`)
- [ ] В коде: `from modules.i18n import t`
- [ ] Все строки заменены на `t("ключ")`
- [ ] Протестировано в браузере (все 3 языка)

---

## 💬 Как найти нужный ключ?

**Ищите где текст используется:**
```bash
grep -r "Мой текст" locales/
```

**Ищите похожие блоки:**
```bash
grep -r "filters" locales/ru.json
```

**Проверьте структуру в JSON:**
```bash
python -c "import json; f=open('locales/ru.json'); print(json.dumps(json.load(f), ensure_ascii=False, indent=2))" | grep -A 5 "charts"
```

---

## 🚀 Готовый шаблон для копирования

```python
# В начало файла
from modules.i18n import t, t_format

# Заголовок
st.title(t("my_section.title"))

# Фильтр
st.markdown(f"<div class='section-header'>{t('my_section.label')}</div>", unsafe_allow_html=True)
selected = st.multiselect(t("my_section.label"), options=[...])

# Метрика  
st.metric(t("my_section.metric"), value=123)

# Сообщение
if error:
    st.error(t("my_section.error"))

# График
fig.update_layout(title=t("charts.my_chart.title"))
```

---

## 📞 Нужна помощь?

1. **JSON не валидируется?** → Используйте https://jsonlint.com/
2. **Ключ не работает?** → Проверьте: `grep "ключ" locales/*.json`
3. **Приложение не запускается?** → Проверьте синтаксис JSON
4. **Не знаете какой ключ использовать?** → Посмотрите в TRANSLATION_GUIDE.md

---

**Всегда помните:** Структурированный JSON + простая функция t() = легко масштабируется! 🎉
