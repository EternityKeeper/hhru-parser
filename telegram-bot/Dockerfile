FROM golang:1.26-alpine AS go-builder
WORKDIR /build
COPY go-scraper/go.mod go-scraper/go.sum ./
RUN go mod download
COPY go-scraper/ .
RUN CGO_ENABLED=0 GOOS=linux go build -o /scraper ./cmd/scraper

FROM python:3.12-slim
WORKDIR /app

ENV SCRAPER_BIN=/usr/local/bin/scraper
ENV DATA_DIR=/app/data

COPY --from=go-builder /scraper /usr/local/bin/scraper

COPY python-analyzer/src/ ./src/
COPY telegram-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY telegram-bot/ .

RUN mkdir -p /app/data

CMD ["python", "bot.py"]
