# HH.ru Intelligent Vacancy Parser

Интеллектуальный парсинг вакансий с hh.ru: **Go-сборщик** + **Python-аналитик** (NLP).

## Архитектура

```
┌─────────────┐     JSON      ┌──────────────┐     HTTP      ┌────────┐
│ Go-Scraper  │ ────────────> │ Python-NLP    │ ────────────> │ Client │
│ (парсинг)   │   vacancies   │ (аналитика)   │    REST API  │        │
└─────────────┘               └──────────────┘               └────────┘
```

## Быстрый старт

```bash
# Go-сборщик
cd go-scraper
go run ./cmd/scraper -q "Golang" -period 7 -o ../data/vacancies.json

# Python-аналитик
cd python-analyzer
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

## Docker

```bash
docker-compose up --build
```

## Технологии

- **Go** — параллельный сбор вакансий через hh.ru API
- **Python** — FastAPI, Pandas, NLP-анализ навыков
- **Docker** — контейнеризация
