import json
import os
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, Query, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse

from src.analyzer import analyze_vacancies
from src.models import Vacancy
from src.nlp.skills import classify_level

app = FastAPI(title="HH.ru Vacancy Analyzer", version="0.1.0")

_data: list[Vacancy] = []
_meta: dict = {}

SCRAPER_DIR = Path(__file__).resolve().parents[3] / "go-scraper"
DATA_DIR = (Path(__file__).resolve().parent.parent.parent.parent / "data").resolve()
DATA_FILE = DATA_DIR / "vacancies.json"

CITIES = [
    ("1", "Москва"),
    ("2", "Санкт-Петербург"),
    ("92", "Тула"),
    ("88", "Казань"),
    ("4", "Новосибирск"),
    ("53", "Краснодар"),
    ("3", "Екатеринбург"),
]


def _load_data():
    global _data, _meta
    if DATA_FILE.exists():
        with open(DATA_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict) and "vacancies" in raw:
            _meta = raw.get("meta", {})
            _data = [Vacancy(**v) for v in raw["vacancies"]]
        elif isinstance(raw, list):
            _meta = {}
            _data = [Vacancy(**v) for v in raw]
        print(f"Loaded {len(_data)} vacancies from {DATA_FILE}")


@app.on_event("startup")
async def startup():
    _load_data()


def _form_html() -> str:
    city_checkboxes = "".join(
        f'<label><input type="checkbox" name="areas" value="{id}" checked> {name}</label>'
        for id, name in CITIES
    )
    return f"""<details class="search-form" {"open" if not _data else ""}>
  <summary>🔍 Параметры поиска</summary>
  <form action="/scrape" method="post">
    <div class="form-row">
      <label>Запрос: <input type="text" name="query" value="{_meta.get("query", "Golang")}" required></label>
    </div>
    <div class="form-row">
      <label>Регионы:</label>
      <div class="city-grid">{city_checkboxes}</div>
    </div>
    <div class="form-row-inline">
      <label>Период: <input type="number" name="period" value="{_meta.get("period", 3)}" min="1" max="7" size="4"> дн. (макс 7)</label>
      <label>Страниц: <input type="number" name="pages" value="{_meta.get("max_pages", 0)}" min="0" size="4"> (0 = все)</label>
    </div>
    <div class="form-row">
      <button type="submit" class="btn" onclick="this.disabled=true;this.textContent='⏳ Парсинг...';">🚀 Запустить парсинг</button>
    </div>
  </form>
</details>"""


def _meta_html() -> str:
    if not _meta:
        return ""
    parts = []
    parts.append(f"<span>Запрос: <strong>{_meta.get('query', '?')}</strong></span>")
    parts.append(f"<span>Регионы: <strong>{', '.join(_meta.get('area_names', [])) or '?'}</strong></span>")
    parts.append(f"<span>Период: <strong>{_meta.get('period', '?')} дн.</strong></span>")
    parts.append(f"<span>Собрано: <strong>{_meta.get('scraped_at', '?')[:10]}</strong></span>")
    return '<div class="meta-bar">' + " · ".join(parts) + "</div>"


def _skills_badge(skills: list[str]) -> str:
    if not skills:
        return '<span style="color:#aaa">—</span>'
    shown = skills[:5]
    rest = len(skills) - 5
    tags = "".join(f'<span class="skill-tag">{s}</span>' for s in shown)
    if rest > 0:
        tags += f' <span class="skill-tag skill-tag-more">+{rest}</span>'
    return tags


def _vacancies_table(vacancies: list[Vacancy]) -> str:
    if not vacancies:
        return '<p style="color:#888">Нет вакансий</p>'
    level_colors = {"junior": "#fbbf24", "middle": "#3b82f6", "senior": "#ef4444"}
    rows = ""
    for v in vacancies[:100]:
        name = v.name or "—"
        employer = v.employer or "—"
        area = v.area or "—"
        sal = v.salary_raw or "—"
        level = classify_level(v.name, v.description or "", v.experience)
        color = level_colors.get(level, "#888")
        rows += f"""<tr><td>{name}</td><td>{employer}</td><td>{area}</td><td>{sal}</td><td><span class="level-badge" style="background:{color}">{level}</span></td><td>{_skills_badge(v.key_skills)}</td></tr>"""
    return f"""<table class="vacancy-table">
      <tr><th>Вакансия</th><th>Работодатель</th><th>Адрес</th><th>Зарплата</th><th>Уровень</th><th>Ключевые навыки</th></tr>
      {rows}
    </table>"""


def _build_html(result: dict) -> str:
    total = result["total"]

    skills_rows = ""
    for skill, count in result.get("top_skills", [])[:20]:
        bar = "█" * count
        skills_rows += f"""
        <tr>
          <td>{skill}</td>
          <td>{count}</td>
          <td><span class="bar">{bar}</span></td>
        </tr>"""

    levels_rows = ""
    level_colors = {"junior": "#fbbf24", "middle": "#3b82f6", "senior": "#ef4444"}
    total_levels = sum(result.get("level_distribution", {}).values()) or 1
    for level, count in sorted(result.get("level_distribution", {}).items()):
        pct = count / total_levels * 100
        color = level_colors.get(level, "#888")
        levels_rows += f"""
        <div class="level-bar">
          <span class="level-label">{level.title()}</span>
          <div class="level-track">
            <div class="level-fill" style="width:{pct:.0f}%;background:{color}">{count}</div>
          </div>
        </div>"""

    salary_block = ""
    if result.get("salary"):
        s = result["salary"]
        no_sal = total - s['count']
        salary_block = f"""
        <div class="card-row">
          <div class="card"><span class="num">{s['avg']:,}</span>₽ средняя</div>
          <div class="card"><span class="num">{s['min']:,}</span>₽ мин</div>
          <div class="card"><span class="num">{s['max']:,}</span>₽ макс</div>
          <div class="card"><span class="num">{s['count']}</span> с з/п{f' ({no_sal} без)' if no_sal else ''}</div>
        </div>"""

    areas_rows = ""
    for area, count in sorted(result.get("area_distribution", {}).items(), key=lambda x: -x[1]):
        areas_rows += f"<tr><td>{area}</td><td>{count}</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>HH.ru Vacancy Analyzer</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ font-family:-apple-system,system-ui,sans-serif; background:#f5f5f5; color:#222; padding:20px; }}
    .container {{ max-width:960px; margin:auto; }}
    h1 {{ font-size:1.5rem; margin-bottom:4px; }}
    .subtitle {{ color:#666; margin-bottom:20px; }}
    .total {{ font-size:2rem; font-weight:700; color:#2563eb; }}
    .meta-bar {{ background:#e8f4fd; border-radius:8px; padding:12px 16px; margin-bottom:16px; font-size:.9rem; color:#333; }}
    .meta-bar span {{ margin-right:4px; }}
    section {{ background:white; border-radius:12px; padding:20px; margin-bottom:16px; box-shadow:0 1px 3px #0001; }}
    h2 {{ font-size:1.1rem; margin-bottom:12px; color:#333; }}
    .card-row {{ display:flex; gap:12px; flex-wrap:wrap; }}
    .card {{ flex:1; min-width:120px; background:#f8fafc; border-radius:8px; padding:16px; text-align:center; }}
    .num {{ font-size:1.4rem; font-weight:700; }}
    table {{ width:100%; border-collapse:collapse; }}
    td, th {{ padding:6px 8px; text-align:left; border-bottom:1px solid #eee; font-size:.85rem; }}
    th {{ font-weight:600; color:#555; font-size:.8rem; }}
    .bar {{ color:#2563eb; font-size:.75rem; letter-spacing:-1px; }}
    .level-bar {{ display:flex; align-items:center; gap:12px; margin-bottom:8px; }}
    .level-label {{ width:80px; font-weight:600; }}
    .level-track {{ flex:1; height:24px; background:#e5e7eb; border-radius:12px; overflow:hidden; }}
    .level-fill {{ height:100%; border-radius:12px; display:flex; align-items:center; justify-content:center; color:white; font-size:.8rem; font-weight:600; }}
    .chart-wrap {{ height:250px; }}
    .links {{ margin-top:16px; font-size:.85rem; }}
    .links a {{ color:#2563eb; text-decoration:none; margin-right:12px; }}
    .links a:hover {{ text-decoration:underline; }}
    .search-form {{ background:#fff; border:1px solid #ddd; border-radius:8px; padding:12px 16px; margin-bottom:16px; }}
    .search-form[open] {{ background:#f0f7ff; border-color:#93c5fd; }}
    .search-form summary {{ cursor:pointer; font-weight:600; font-size:.95rem; color:#2563eb; }}
    .form-row {{ margin:10px 0; }}
    .form-row-inline {{ display:flex; gap:16px; flex-wrap:wrap; margin:10px 0; }}
    .form-row input[type=text] {{ width:100%; padding:8px; border:1px solid #ccc; border-radius:6px; font-size:.95rem; }}
    .form-row input[type=number] {{ padding:6px; border:1px solid #ccc; border-radius:6px; width:70px; }}
    .form-row-inline input[type=number] {{ padding:6px; border:1px solid #ccc; border-radius:6px; width:70px; }}
    .city-grid {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:4px; }}
    .city-grid label {{ display:inline-flex; align-items:center; gap:4px; background:#e5e7eb; padding:4px 10px; border-radius:6px; font-size:.85rem; cursor:pointer; }}
    .city-grid input[type=checkbox] {{ accent-color:#2563eb; }}
    .btn {{ background:#2563eb; color:white; border:none; padding:10px 24px; border-radius:8px; font-size:.95rem; font-weight:600; cursor:pointer; }}
    .btn:hover {{ background:#1d4ed8; }}
    .loading {{ text-align:center; padding:40px; font-size:1.1rem; color:#555; }}
    .level-badge {{ display:inline-block; padding:2px 8px; border-radius:4px; color:white; font-size:.75rem; font-weight:600; text-transform:uppercase; }}
    .skill-tag {{ display:inline-block; background:#e0e7ff; color:#3730a3; padding:1px 5px; border-radius:4px; font-size:.7rem; margin:1px; }}
    .skill-tag-more {{ background:#e5e7eb; color:#555; }}
    .vacancy-table {{ table-layout:fixed; }}
    .vacancy-table td, .vacancy-table th {{ overflow:hidden; text-overflow:ellipsis; }}
    .vacancy-table th:last-child {{ width:240px; }}
    .vacancy-table td:last-child {{ width:240px; word-break:break-word; }}
  </style>
</head>
<body>
<div class="container">
  <h1>HH.ru Vacancy Analyzer</h1>
  <p class="subtitle">Анализ рынка вакансий · <span class="total">{total}</span> вакансий</p>

  {_form_html()}

  {_meta_html()}

  <section>
    <h2>Зарплаты</h2>
    {salary_block or '<p style="color:#888">Нет данных о зарплатах</p>'}
  </section>

  <section>
    <h2>Уровни</h2>
    {levels_rows}
  </section>

  <section>
    <h2>Топ навыков</h2>
    <div class="chart-wrap">
      <canvas id="skillsChart"></canvas>
    </div>
    <table>
      <tr><th>Навык</th><th>Кол-во</th><th></th></tr>
      {skills_rows}
    </table>
  </section>

  <section>
    <h2>Города</h2>
    <table>
      <tr><th>Город</th><th>Вакансий</th></tr>
      {areas_rows}
    </table>
  </section>

  <section>
    <h2>Вакансии ({min(total, 100)} из {total})</h2>
    {_vacancies_table(_data)}
  </section>

  <div class="links">
    <a href="/docs">Swagger UI</a>
    <a href="/stats">JSON статистика</a>
    <a href="/skills/top">JSON навыки</a>
    <a href="/analyze">GET /analyze</a>
  </div>
</div>

<script>
const labels = {json.dumps([s for s, _ in result.get("top_skills", [])[:10]])};
const values = {json.dumps([c for _, c in result.get("top_skills", [])[:10]])};
new Chart(document.getElementById('skillsChart'), {{
  type: 'bar',
  data: {{ labels, datasets: [{{ label: 'Вакансий', data: values, backgroundColor: '#3b82f6' }}] }},
  options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
}});
</script>
</body>
</html>"""


@app.post("/scrape", response_class=HTMLResponse)
async def scrape(
    query: str = Form(...),
    areas: list[str] = Form(...),
    period: int = Form(3),
    pages: int = Form(0),
):
    period = max(1, min(period, 7))
    pages = max(0, pages)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = str(DATA_FILE.resolve())
    areas_str = ",".join(areas)
    cmd = [
        "go", "run", "./cmd/scraper/",
        "-q", query,
        "-areas", areas_str,
        "-period", str(period),
        "-pages", str(pages),
        "-o", out_path,
    ]
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, cwd=str(SCRAPER_DIR), capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Парсинг превысил лимит 120 секунд")
    except Exception as e:
        raise HTTPException(500, f"Ошибка запуска парсера: {e}")

    _load_data()
    if not _data:
        raise HTTPException(502, "Парсер завершился, но данные не найдены")
    return HTMLResponse(content=_build_html(analyze_vacancies(_data)))


@app.get("/", response_class=HTMLResponse)
async def root():
    if not _data:
        return HTMLResponse("""
        <html><body style="font-family:sans-serif;padding:40px">
        <h1>HH.ru Vacancy Analyzer</h1>
        <p>Нет данных. Загрузите JSON через <a href="/analyze">POST /analyze</a>
        или поместите <code>data/vacancies.json</code></p>
        </body></html>""")
    return _build_html(analyze_vacancies(_data))


@app.get("/stats", summary="Полная статистика (JSON)")
async def stats():
    if not _data:
        raise HTTPException(404, "No data loaded")
    return analyze_vacancies(_data)


@app.get("/analyze", response_class=HTMLResponse, summary="Показать аналитику")
async def analyze_get():
    global _data
    if not _data:
        raise HTTPException(400, "Нет данных. Отправьте JSON через POST или поместите data/vacancies.json")
    return _build_html(analyze_vacancies(_data))


@app.post("/analyze", response_class=HTMLResponse, summary="Загрузить и проанализировать вакансии")
async def analyze_post(file: Optional[UploadFile] = File(None)):
    global _data
    if file:
        content = await file.read()
        raw = json.loads(content)
        _data = [Vacancy(**v) for v in raw]
    if not _data:
        raise HTTPException(400, "Нет данных. Отправьте JSON через POST или поместите data/vacancies.json")
    return HTMLResponse(content=_build_html(analyze_vacancies(_data)))


@app.get("/skills/top", summary="Топ навыков (JSON)")
async def top_skills(limit: int = Query(30, ge=1, le=100)):
    if not _data:
        raise HTTPException(404, "No data loaded")
    result = analyze_vacancies(_data)
    return {"skills": result["top_skills"][:limit], "total_vacancies": result["total"]}


@app.get("/levels/distribution", summary="Распределение по уровням (JSON)")
async def level_distribution():
    if not _data:
        raise HTTPException(404, "No data loaded")
    result = analyze_vacancies(_data)
    return {"distribution": result["level_distribution"], "total_vacancies": result["total"]}


@app.get("/areas", summary="Распределение по городам (JSON)")
async def area_distribution():
    if not _data:
        raise HTTPException(404, "No data loaded")
    result = analyze_vacancies(_data)
    return {"distribution": result["area_distribution"], "total_vacancies": result["total"]}


@app.get("/salary", summary="Статистика по зарплатам (JSON)")
async def salary_stats():
    if not _data:
        raise HTTPException(404, "No data loaded")
    result = analyze_vacancies(_data)
    return result.get("salary", {"error": "No salary data available"})
