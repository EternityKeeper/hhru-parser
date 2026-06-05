import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Query, UploadFile, HTTPException
from fastapi.responses import HTMLResponse

from src.analyzer import analyze_vacancies
from src.models import Vacancy

app = FastAPI(title="HH.ru Vacancy Analyzer", version="0.1.0")

_data: list[Vacancy] = []


@app.on_event("startup")
async def startup():
    global _data
    json_path = Path("data/vacancies.json")
    if json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            raw = json.load(f)
        _data = [Vacancy(**v) for v in raw]
        print(f"Loaded {len(_data)} vacancies from {json_path}")


@app.get("/", response_class=HTMLResponse)
async def root():
    total = len(_data)
    return f"""
    <html>
    <head><title>HH.ru Analyzer</title></head>
    <body>
        <h1>HH.ru Vacancy Analyzer API</h1>
        <p>Loaded {total} vacancies</p>
        <ul>
            <li><a href="/docs">Swagger</a></li>
            <li><a href="/redoc">ReDoc</a></li>
            <li><a href="/analyze">POST /analyze — upload & analyze JSON</a></li>
            <li><a href="/skills/top">GET /skills/top — top skills</a></li>
            <li><a href="/levels/distribution">GET /levels/distribution — level distribution</a></li>
        </ul>
    </body>
    </html>
    """


@app.get("/stats", summary="Полная статистика")
async def stats():
    if not _data:
        raise HTTPException(404, "No data loaded. POST /analyze or place data/vacancies.json")
    return analyze_vacancies(_data)


@app.post("/analyze", summary="Загрузить и проанализировать вакансии")
async def upload_and_analyze(file: Optional[UploadFile] = File(None)):
    global _data
    if file:
        content = await file.read()
        raw = json.loads(content)
        _data = [Vacancy(**v) for v in raw]
    if not _data:
        raise HTTPException(400, "No data provided and no data loaded")
    return analyze_vacancies(_data)


@app.get("/skills/top", summary="Топ навыков")
async def top_skills(limit: int = Query(30, ge=1, le=100)):
    if not _data:
        raise HTTPException(404, "No data loaded")
    result = analyze_vacancies(_data)
    return {"skills": result["top_skills"][:limit], "total_vacancies": result["total"]}


@app.get("/levels/distribution", summary="Распределение по уровням")
async def level_distribution():
    if not _data:
        raise HTTPException(404, "No data loaded")
    result = analyze_vacancies(_data)
    return {"distribution": result["level_distribution"], "total_vacancies": result["total"]}


@app.get("/areas", summary="Распределение по городам")
async def area_distribution():
    if not _data:
        raise HTTPException(404, "No data loaded")
    result = analyze_vacancies(_data)
    return {"distribution": result["area_distribution"], "total_vacancies": result["total"]}


@app.get("/salary", summary="Статистика по зарплатам")
async def salary_stats():
    if not _data:
        raise HTTPException(404, "No data loaded")
    result = analyze_vacancies(_data)
    return result.get("salary", {"error": "No salary data available"})
