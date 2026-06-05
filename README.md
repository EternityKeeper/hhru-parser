# HH.ru Intelligent Vacancy Parser

Интеллектуальный парсинг вакансий с hh.ru: **Go-сборщик** (HTML-парсинг) + **Python-аналитик** (NLP, FastAPI REST API).

Курсовая работа, вариант 21.

## Архитектура

```
┌─────────────┐    data/         ┌──────────────────┐     HTTP      ┌─────────┐
│ Go-Scraper  │ ──vacancies.json─>│ Python-Analyzer  │ <──────────> │ Clients │
│ (HTML parse)│                  │ FastAPI + NLP     │   REST API   │ (curl/  │
└─────────────┘                  └──────────────────┘              │  browser)│
                                                                   └─────────┘
```

## Структура проекта

```
.
├── go-scraper/                    # Go-сборщик (HTML-парсинг hh.ru)
│   ├── cmd/scraper/main.go        # Точка входа (флаги: -q, -area, -period, -pages, -o)
│   └── internal/
│       ├── parser/parser.go       # Парсер hh.ru (goquery, colly-стиль)
│       └── models/vacancy.go      # Модель вакансии
├── python-analyzer/               # Python-аналитик
│   ├── src/
│   │   ├── api/main.py           # FastAPI сервер
│   │   ├── analyzer.py           # Сводная аналитика
│   │   ├── models.py             # Pydantic модель
│   │   └── nlp/skills.py         # Извлечение навыков, классификация уровней
│   └── tests/test_all.py         # Тесты pytest
├── data/                          # JSON-файлы вакансий
├── docker-compose.yml             # Docker Compose (scraper + analyzer)
├── docs/                          # Документация
└── README.md
```

## Быстрый старт

### 1. Go-сборщик

```bash
cd go-scraper
go run ./cmd/scraper -q "Golang" -area 1 -period 7 -pages 1 -o ../data/vacancies.json
```

Флаги:
- `-q` — поисковый запрос (по умолч. "Python")
- `-area` — регион: 1=Москва, 2=СПб (по умолч. 1)
- `-period` — период в днях (по умолч. 30, 0 = все)
- `-pages` — страниц для сбора (0 = все доступные)
- `-o` — куда сохранить JSON (по умолч. data/vacancies.json)

### 2. Python-аналитик

```bash
cd python-analyzer
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

Эндпоинты:
- `GET /stats` — полная статистика
- `POST /analyze` — загрузить JSON с вакансиями
- `GET /skills/top?limit=30` — топ навыков
- `GET /levels/distribution` — распределение по уровням
- `GET /areas` — распределение по городам
- `GET /salary` — зарплатная статистика
- `GET /docs` — Swagger UI

### 3. Docker

```bash
docker-compose up --build
```

Сборщик запускается, сохраняет данные в `data/`, аналитик доступен на `http://localhost:8000`.

## Пример работы

```bash
# Сбор Golang-вакансий в Москве за 7 дней
go run ./go-scraper/cmd/scraper -q "Golang" -area 1 -period 7 -pages 1

# Анализ
curl -s http://localhost:8000/skills/top?limit=10
# {"skills":[["go",17],["sql",12],["postgresql",11]...], "total_vacancies": 17}
```

## Тестирование

```bash
# Go
cd go-scraper && go test ./internal/... -v

# Python
cd python-analyzer && pytest tests/ -v
```

## Технологии

- **Go 1.26** — goquery (HTML-парсинг), конкурентный сбор (3 workers), rate-limited
- **Python 3.10** — FastAPI, Pydantic, Pandas
- **NLP** — извлечение навыков (60+ keywords), классификация junior/middle/senior
- **Docker** — Docker Compose, multi-stage build
- **Git** — semantic commits, Git flow

## Как это работает

Сборщик использует **HTML-парсинг** `https://hh.ru/search/vacancy` (без OAuth2, без регистрации приложения):
1. Парсит страницу поиска — извлекает URL, названия, компании
2. Конкурентно (3 workers) обходит каждую вакансию — достаёт описание, навыки, зарплату, дату
3. Сохраняет в JSON

Аналитик:
1. Извлекает навыки из описания (keyword matching)
2. Классифицирует уровень (junior/middle/senior) по опыту и названию
3. Считает статистику по зарплатам, городам, навыкам
