package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"time"

	"github.com/user/hhru-parser/go-scraper/internal/models"
	"github.com/user/hhru-parser/go-scraper/internal/parser"
)

func main() {
	query := flag.String("q", "Python", "поисковый запрос")
	area := flag.Int("area", 1, "регион (1 - Москва, 2 - СПб)")
	period := flag.Int("period", 30, "период в днях")
	pages := flag.Int("pages", 0, "максимум страниц (0 = все)")
	output := flag.String("o", "data/vacancies.json", "файл для сохранения")
	flag.Parse()

	client := parser.NewClient()
	fmt.Printf("HH.ru Parser — поиск: %s\n", *query)
	fmt.Printf("Запуск: %s\n", time.Now().Format(time.RFC3339))

	vacancies, err := client.ScrapeAll(*query, *area, *period, *pages)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Ошибка: %v\n", err)
		os.Exit(1)
	}

	data, err := json.MarshalIndent(vacancies, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Ошибка сериализации: %v\n", err)
		os.Exit(1)
	}

	outDir := "data"
	if dir := dirFromPath(*output); dir != "" {
		outDir = dir
	}
	if err := os.MkdirAll(outDir, 0755); err != nil {
		fmt.Fprintf(os.Stderr, "Ошибка создания %s: %v\n", outDir, err)
		os.Exit(1)
	}

	if err := os.WriteFile(*output, data, 0644); err != nil {
		fmt.Fprintf(os.Stderr, "Ошибка записи: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Сохранено %d вакансий в %s\n", len(vacancies), *output)

	_ = models.Vacancy{}
}

func dirFromPath(p string) string {
	for i := len(p) - 1; i >= 0; i-- {
		if p[i] == '\\' || p[i] == '/' {
			return p[:i]
		}
	}
	return ""
}
