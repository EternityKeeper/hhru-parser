from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import HTMLResponse
from src.models import Vacancy

app = FastAPI(title="HH.ru Vacancy Analyzer", version="0.1.0")


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
    <head><title>HH.ru Analyzer</title></head>
    <body>
        <h1>HH.ru Vacancy Analyzer API</h1>
        <ul>
            <li><a href="/docs">Swagger</a></li>
            <li><a href="/redoc">ReDoc</a></li>
        </ul>
    </body>
    </html>
    """


@app.post("/analyze", summary="Загрузить и проанализировать вакансии")
async def analyze_vacancies(file: UploadFile = File(...)):
    content = await file.read()
    import json
    data = json.loads(content)
    vacancies = [Vacancy(**v) for v in data]
    return {
        "total": len(vacancies),
        "message": "Файл загружен. Анализ скоро будет реализован.",
    }


@app.get("/skills/top", summary="Топ навыков")
async def top_skills(limit: int = Query(20, ge=1, le=100)):
    return {"skills": [], "message": "Анализ навыков — в разработке"}


@app.get("/levels/distribution", summary="Распределение по уровням")
async def level_distribution():
    return {"distribution": {}, "message": "Классификация уровней — в разработке"}
