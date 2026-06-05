package main

import (
	"flag"
	"fmt"
	"os"
	"time"

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

	data, err := parser.MarshalVacancies(vacancies)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Ошибка сериализации: %v\n", err)
		os.Exit(1)
	}

	if err := os.MkdirAll("data", 0755); err != nil {
		fmt.Fprintf(os.Stderr, "Ошибка создания data/: %v\n", err)
		os.Exit(1)
	}

	if err := os.WriteFile(*output, data, 0644); err != nil {
		fmt.Fprintf(os.Stderr, "Ошибка записи: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Сохранено %d вакансий в %s\n", len(vacancies), *output)
}
