"""
modules/ukraine_map.py
Генерация интерактивной карты продаж по регионам Украины.
Полная адаптация оригинального HTML шаблона.
"""

import pandas as pd
import json
from modules.i18n import t


# Координаты всех городов
CITY_COORDS = {
    "Александровка": (48.51, 32.26), "Бедевля": (48.10, 23.62),
    "Белая Церковь": (49.80, 30.12), "Белогородка": (50.38, 30.28),
    "Борисполь": (50.35, 30.97), "Бровары": (50.52, 30.79),
    "Васильков": (50.18, 30.32), "Винница": (49.23, 28.48),
    "Владимир-Волынский": (50.85, 24.32), "Вышгород": (50.60, 30.42),
    "Глеваха": (50.05, 30.28), "Днепр": (48.46, 35.04),
    "Дрогобыч": (49.35, 23.51), "Жашков": (49.32, 29.55),
    "Житомир": (50.26, 28.67), "Запорожье": (47.84, 35.14),
    "Звенигородка": (49.10, 30.73), "Золотоноша": (49.67, 32.04),
    "Ивано-Франковск": (48.92, 24.71), "Измаил": (45.34, 28.84),
    "Ирпень": (50.52, 30.25), "Иршава": (48.32, 23.04),
    "Каменское": (48.52, 34.62), "Киев": (50.45, 30.52),
    "Ковель": (51.21, 24.70), "Коломыя": (48.53, 25.04),
    "Кременчуг": (49.07, 33.42), "Кривой Рог": (47.91, 33.38),
    "Кропивницкий": (48.51, 32.30), "Куты": (48.26, 25.08),
    "Луцк": (50.75, 25.35), "Львов": (49.84, 24.03),
    "Нежин": (51.04, 31.89), "Николаев": (46.97, 31.99),
    "Нововолынск": (50.73, 24.07), "Одесса": (46.48, 30.74),
    "Пасеки-Зубрицкие": (49.50, 23.50), "Полтава": (49.59, 34.55),
    "Прилуки": (50.59, 32.39), "Рава-Русская": (50.24, 23.62),
    "Ратно": (51.66, 24.53), "Ровно": (50.62, 26.25),
    "Самар": (48.63, 35.22), "Самбор": (49.52, 23.19),
    "Сарны": (51.34, 26.61), "Сербичаны": (48.10, 26.00),
    "Сокирница": (48.15, 23.42), "Сторожинец": (48.17, 25.72),
    "Сумы": (50.91, 34.80), "Тересва": (48.07, 23.52),
    "Тернополь": (49.55, 25.60), "Тячев": (48.01, 23.57),
    "Ужгород": (48.62, 22.30), "Украинка": (49.73, 30.74),
    "Умань": (48.75, 30.22), "Харьков": (50.00, 36.22),
    "Хмельницкий": (49.42, 27.00), "Царичанка": (48.98, 34.28),
    "Чабаны": (50.36, 30.47), "Черкассы": (49.44, 32.06),
    "Чернигов": (51.49, 31.30), "Черновцы": (48.29, 25.94),
    "Чугуев": (49.84, 36.68), "Шепетовка": (50.19, 27.06),
    "Шептицький": (50.40, 24.22),
}


def generate_ukraine_map_html(df: pd.DataFrame) -> str:
    """
    Генерирует полный HTML код карты на основе отфильтрованных данных.
    Использует оригинальный шаблон с D3.js и TopoJSON.
    """
    
    if df.empty:
        return f"<div style='padding:2rem;text-align:center;color:#94a3b8'>{t('map.no_data')}</div>"
    
    # Группируем по городам
    city_sales = (
        df.groupby("Город")
        .agg({
            "В наличии": "sum",
            "Регион": "first"
        })
        .reset_index()
        .rename(columns={"В наличии": "amount"})
    )
    
    # Формируем JS массив городов
    cities_data = []
    for _, row in city_sales.iterrows():
        city = row["Город"]
        coords = CITY_COORDS.get(city)
        if not coords:
            continue
        
        cities_data.append({
            "name": city,
            "amount": int(row["amount"]),
            "region": row["Регион"],
            "lat": coords[0],
            "lon": coords[1]
        })
    
    cities_json = json.dumps(cities_data, ensure_ascii=False)
    
    # HTML шаблон — полностью адаптивный
    html = f"""
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: 100%; min-height: 100%; background: #0f1117; }}
  body {{ margin: 0; padding: 0; }}
  .map-body {{ font-family: Arial, sans-serif; background: #0f1117; color: #e2e8f0; padding: 0; max-width: 100%; overflow: visible; }}
  .map-title {{ font-size: 20px; font-weight: 600; margin-bottom: 1rem; color: #f1f5f9; }}
  #stat-cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 1rem; }}
  .stat-card {{ background: #1e2433; border-radius: 10px; padding: 0.85rem 1rem; cursor: pointer; transition: opacity 0.15s, transform 0.1s; border: 1px solid #2d3748; }}
  .stat-card:hover {{ transform: translateY(-1px); border-color: #4a5568; }}
  .stat-label {{ display: flex; align-items: center; gap: 6px; margin-bottom: 5px; font-size: 12px; color: #94a3b8; }}
  .stat-dot {{ width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }}
  .stat-value {{ font-size: 20px; font-weight: 600; }}
  .stat-meta {{ font-size: 11px; color: #64748b; margin-top: 2px; }}
  #filter-bar {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 0.35rem; }}
  #filter-bar span {{ font-size: 12px; color: #64748b; }}
  button {{ background: #1e2433; border: 1px solid #2d3748; color: #94a3b8; padding: 5px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; transition: all 0.15s; }}
  button:hover {{ background: #2d3748; color: #e2e8f0; }}
  button.active {{ background: #2d3748; color: #f1f5f9; font-weight: 600; }}
  #map-wrap {{ width: 100%; min-height: 560px; height: auto; background: #141824; border-radius: 12px; border: 1px solid #2d3748; overflow: visible; position: relative; box-sizing: border-box; padding: 0 10px 0; margin-top: 0; }}
  #map-wrap svg {{ width: 100%; height: auto; display: block; margin-top: 0; }}
  #tooltip {{ position: fixed; display: none; pointer-events: none; background: #1e2433; border: 1px solid #374151; border-radius: 8px; padding: 9px 13px; font-size: 13px; z-index: 999; box-shadow: 0 4px 16px rgba(0,0,0,0.4); }}
  .legend {{ display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-top: 0.75rem; }}
  .legend-item {{ display: flex; align-items: center; gap: 5px; font-size: 12px; color: #64748b; }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}
  .total-bar {{ background: #1e2433; border: 1px solid #2d3748; border-radius: 8px; padding: 10px 16px; margin-bottom: 0.75rem; font-size: 13px; color: #94a3b8; display: flex; align-items: center; gap: 10px; }}
  .total-bar strong {{ color: #f1f5f9; font-size: 16px; }}
</style>
<div class="map-body">
<h1 class="map-title">Карта продаж по регионам Украины</h1>
<div class="total-bar">Общий объём остатков: <strong id="grand-total">—</strong> ед. · <span id="city-count">—</span> городов</div>
<div id="stat-cards"></div>
<div id="filter-bar"><span>Фильтр:</span></div>
<div id="map-wrap"></div>
<div class="legend">
  <span style="font-size:12px;color:#64748b">Размер пузыря = объём остатков</span>
  <span class="legend-item"><span class="legend-dot" style="background:#6366f1"></span>Запад</span>
  <span class="legend-item"><span class="legend-dot" style="background:#10b981"></span>Центр</span>
  <span class="legend-item"><span class="legend-dot" style="background:#f59e0b"></span>Восток</span>
  <span class="legend-item"><span class="legend-dot" style="background:#ef4444"></span>Юг</span>
  <span class="legend-item"><span class="legend-dot" style="background:#dc2626"></span>Оккупировано</span>
</div>
<div id="tooltip"></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js"></script>
<script>
const CITIES = {cities_json};

const REGION_CFG = {{
  West: {{label:"Запад", color:"#6366f1", fill:"#6366f140", dim:"#6366f115"}},
  Center: {{label:"Центр", color:"#10b981", fill:"#10b98140", dim:"#10b98115"}},
  East: {{label:"Восток", color:"#f59e0b", fill:"#f59e0b40", dim:"#f59e0b15"}},
  South: {{label:"Юг", color:"#ef4444", fill:"#ef444440", dim:"#ef444415"}}
}};

function getOblastRegion(rawName) {{
  const n = (rawName || '').toLowerCase()
    .replace(/['\u2019\u02bc\u0060\u00b4]/g, '')
    .replace(/oblast|area|province/gi, '')
    .trim();
  
  if (n.includes('crimea') || n.includes('krym') || n.includes('sevastopol')) return 'Occupied';
  if (n.includes('luhansk') || n.includes('lugansk')) return 'Occupied';
  if (n.includes('donetsk')) return 'PartialEast';
  if (n.includes('zapori') || n.includes('zaporiz')) return 'PartialEast';
  if (n.includes('kherson') || n.includes('herson')) return 'PartialSouth';
  
  if (n.includes('kyiv') || n.includes('kiev')) return 'Center';
  if (n.includes('cherkas')) return 'Center';
  if (n.includes('chernihiv') || n.includes('chernigov')) return 'Center';
  if (n.includes('poltava')) return 'Center';
  if (n.includes('sumy')) return 'Center';
  if (n.includes('zhytomyr') || n.includes('zhitomir')) return 'Center';
  
  if (n.includes('lviv') || n.includes('lvov')) return 'West';
  if (n.includes('chernivtsi') || n.includes('chernivet') || n.includes('bukovyn')) return 'West';
  if (n.includes('ivano') || n.includes('frankivsk')) return 'West';
  if (n.includes('ternopil')) return 'West';
  if (n.includes('khmeln')) return 'West';
  if (n.includes('rivne') || n.includes('rovno')) return 'West';
  if (n.includes('volyn')) return 'West';
  if (n.includes('zakarpa') || n.includes('transcarp')) return 'West';
  if (n.includes('vinnyt')) return 'West';
  
  if (n.includes('kharkiv') || n.includes('kharkov')) return 'East';
  if (n.includes('dnipro') || n.includes('dniepro') || n.includes('dnepro')) return 'East';
  if (n.includes('kirovograd') || n.includes('kirovohrad')) return 'East';
  
  if (n.includes('odesa') || n.includes('odess')) return 'South';
  if (n.includes('mykolai') || n.includes('mykolay') || n.includes('nikolaev')) return 'South';
  
  return null;
}}

const OBLAST_CFG = {{
  West: {{fill:"#6366f155", stroke:"#6366f199", dim:"#6366f115"}},
  Center: {{fill:"#10b98155", stroke:"#10b98199", dim:"#10b98115"}},
  East: {{fill:"#f59e0b55", stroke:"#f59e0b99", dim:"#f59e0b15"}},
  South: {{fill:"#ef444455", stroke:"#ef444499", dim:"#ef444415"}},
  Occupied: {{fill:"#dc262655", stroke:"#dc2626", dim:"#dc262615"}},
  PartialEast: {{fill:"url(#pat-east)", stroke:"#dc262680", dimFill:"#f59e0b15", dimStroke:"#33333320"}},
  PartialSouth: {{fill:"url(#pat-south)", stroke:"#dc262680", dimFill:"#ef444415", dimStroke:"#33333320"}}
}};

const regionStats = {{}};
CITIES.forEach(c => {{
  if (!regionStats[c.region]) regionStats[c.region] = {{total: 0, count: 0}};
  regionStats[c.region].total += c.amount;
  regionStats[c.region].count++;
}});
const grandTotal = Object.values(regionStats).reduce((s, r) => s + r.total, 0);
document.getElementById('grand-total').textContent = grandTotal.toLocaleString('ru-RU');
document.getElementById('city-count').textContent = CITIES.length;

const statsEl = document.getElementById('stat-cards');
Object.entries(REGION_CFG).forEach(([k, cfg]) => {{
  const s = regionStats[k] || {{total: 0, count: 0}};
  const pct = ((s.total / grandTotal) * 100).toFixed(1);
  const div = document.createElement('div');
  div.className = 'stat-card';
  div.dataset.region = k;
  div.innerHTML = `<div class="stat-label"><span class="stat-dot" style="background:${{cfg.color}}"></span>${{cfg.label}}</div><div class="stat-value" style="color:${{cfg.color}}">${{s.total.toLocaleString('ru-RU')}}</div><div class="stat-meta">${{pct}}% · ${{s.count}} городов</div>`;
  div.addEventListener('click', () => filterRegion(k));
  statsEl.appendChild(div);
}});

const filterBar = document.getElementById('filter-bar');
const allBtn = document.createElement('button');
allBtn.textContent = 'Все';
allBtn.dataset.r = '';
allBtn.className = 'active';
allBtn.addEventListener('click', () => filterRegion(null));
filterBar.appendChild(allBtn);
Object.entries(REGION_CFG).forEach(([k, cfg]) => {{
  const btn = document.createElement('button');
  btn.textContent = cfg.label;
  btn.dataset.r = k;
  btn.style.borderColor = cfg.color + '60';
  btn.addEventListener('click', () => filterRegion(k));
  filterBar.appendChild(btn);
}});

let activeRegion = null;
const tip = document.getElementById('tooltip');
const maxAmt = Math.max(...CITIES.map(c => c.amount));

const svg = d3.select('#map-wrap').append('svg')
  .attr('viewBox', '0 0 800 600')
  .attr('width', '100%')
  .attr('height', '100%')
  .attr('preserveAspectRatio', 'xMidYMid meet')
  .style('display', 'block');

svg.append('defs').html(`
  <pattern id="pat-east" patternUnits="userSpaceOnUse" width="10" height="10" patternTransform="rotate(45)">
    <rect width="10" height="10" fill="#f59e0b50"/>
    <rect width="5" height="10" fill="#dc262668"/>
  </pattern>
  <pattern id="pat-south" patternUnits="userSpaceOnUse" width="10" height="10" patternTransform="rotate(45)">
    <rect width="10" height="10" fill="#ef444450"/>
    <rect width="5" height="10" fill="#dc262668"/>
  </pattern>
`);

const projection = d3.geoMercator().center([31.5, 49]).scale(1600).translate([400, 250]);
const pathGen = d3.geoPath(projection);
let cachedFeatures = [];

function oblastStyle(name, active) {{
  const r = getOblastRegion(name);
  if (!r) return {{fill: '#1a2035', stroke: '#2d3748'}};
  
  const cfg = OBLAST_CFG[r];
  const isPartial = r === 'PartialEast' || r === 'PartialSouth';
  const isOcc = r === 'Occupied';
  const show = !active || isOcc || isPartial || active === r;
  
  if (isPartial) {{
    return show ? {{fill: cfg.fill, stroke: cfg.stroke}} : {{fill: cfg.dimFill, stroke: cfg.dimStroke}};
  }}
  
  return {{fill: show ? cfg.fill : cfg.dim, stroke: show ? cfg.stroke : '#2d3748'}};
}}

function drawMap() {{
  svg.select('#oblasts').remove();
  svg.insert('g', '#bubbles').attr('id', 'oblasts')
    .selectAll('path').data(cachedFeatures).join('path')
    .attr('d', pathGen)
    .attr('fill', d => oblastStyle(d.properties.name, activeRegion).fill)
    .attr('stroke', d => oblastStyle(d.properties.name, activeRegion).stroke)
    .attr('stroke-width', d => {{
      const r = getOblastRegion(d.properties.name);
      return (r === 'Occupied' || r === 'PartialEast' || r === 'PartialSouth') ? 1.5 : 0.7;
    }})
    .attr('stroke-dasharray', d => {{
      const r = getOblastRegion(d.properties.name);
      return (r === 'Occupied') ? '4,4' : '0';
    }});
}}

function drawBubbles() {{
  svg.select('#bubbles').remove();
  const list = (activeRegion ? CITIES.filter(c => c.region === activeRegion) : CITIES)
    .slice().sort((a, b) => b.amount - a.amount);
  svg.append('g').attr('id', 'bubbles')
    .selectAll('circle').data(list).join('circle')
    .attr('cx', d => projection([d.lon, d.lat])[0])
    .attr('cy', d => projection([d.lon, d.lat])[1])
    .attr('r', d => Math.min(Math.sqrt(d.amount / maxAmt) * 20 + 3, 25))
    .attr('fill', d => REGION_CFG[d.region].color)
    .attr('fill-opacity', 0.75)
    .attr('stroke', '#0f1117')
    .attr('stroke-width', 0.5)
    .style('cursor', 'pointer')
    .on('mouseover', (ev, d) => {{
      const cfg = REGION_CFG[d.region];
      tip.style.display = 'block';
      tip.innerHTML = `<strong style="color:#f1f5f9">${{d.name}}</strong><br>
        <span style="color:#94a3b8;font-size:12px">${{cfg.label}}</span> &nbsp;
        <span style="color:${{cfg.color}};font-weight:600">${{d.amount.toLocaleString('ru-RU')}}</span> ед.<br>
        <span style="color:#64748b;font-size:11px">${{((d.amount/grandTotal)*100).toFixed(2)}}% от общего</span>`;
    }})
    .on('mousemove', (ev) => {{
      let x = ev.clientX + 14, y = ev.clientY - 10;
      if (x + 200 > window.innerWidth) x = ev.clientX - 210;
      tip.style.left = x + 'px';
      tip.style.top = y + 'px';
    }})
    .on('mouseout', () => tip.style.display = 'none');
}}

function filterRegion(r) {{
  activeRegion = r;
  document.querySelectorAll('#filter-bar button').forEach(b => {{
    const on = (b.dataset.r === r) || (b.dataset.r === '' && !r);
    b.className = on ? 'active' : '';
  }});
  document.querySelectorAll('.stat-card').forEach(d => {{
    d.style.opacity = (!r || d.dataset.region === r) ? '1' : '0.35';
  }});
  drawMap();
  drawBubbles();
}}

d3.json('https://cdn.jsdelivr.net/npm/datamaps@0.5.10/src/js/data/ukr.topo.json').then(topo => {{
  const key = Object.keys(topo.objects)[0];
  cachedFeatures = topojson.feature(topo, topo.objects[key]).features;
  drawMap();
  drawBubbles();
}}).catch(() => {{
  svg.append('text')
    .attr('x', 400).attr('y', 300)
    .attr('text-anchor', 'middle')
    .style('fill', '#64748b')
    .style('font-size', '14px')
    .text('Нет подключения — карта областей недоступна');
  drawBubbles();
}});

function adjustIframeHeight() {{
  const body = document.body;
  const html = document.documentElement;
  const height = Math.max(body.scrollHeight, body.offsetHeight, html.clientHeight, html.scrollHeight, html.offsetHeight);
  if (window.frameElement) {{
    window.frameElement.style.height = height + 'px';
  }}
}}

window.addEventListener('load', adjustIframeHeight);
window.addEventListener('resize', adjustIframeHeight);
setTimeout(adjustIframeHeight, 250);
</script>
"""
    
    return html