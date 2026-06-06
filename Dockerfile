# syntax=docker/dockerfile:1
# Stage 1: build Go scraper
FROM golang:1.26-alpine AS go-builder
WORKDIR /build
COPY go-scraper/go.mod go-scraper/go.sum ./
RUN go mod download
COPY go-scraper/ .
RUN CGO_ENABLED=0 GOOS=linux go build -o /scraper ./cmd/scraper

# Stage 2: Python runtime with scraper binary
FROM python:3.12-slim
WORKDIR /app

ENV SCRAPER_BIN=/usr/local/bin/scraper

COPY --from=go-builder /scraper /usr/local/bin/scraper

COPY python-analyzer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY python-analyzer/ .

RUN mkdir -p /app/data

EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
