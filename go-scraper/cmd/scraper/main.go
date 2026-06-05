package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/user/hhru-parser/go-scraper/internal/models"
	"github.com/user/hhru-parser/go-scraper/internal/parser"
)

var areaNames = map[int]string{
	1:    "Москва",
	2:    "Санкт-Петербург",
	3:    "Екатеринбург",
	4:    "Новосибирск",
	53:   "Краснодар",
	88:   "Казань",
	92:   "Тула",
	113:  "Россия",
	1913: "Тульская область",
}

func areaName(id int) string {
	if name, ok := areaNames[id]; ok {
		return name
	}
	return fmt.Sprintf("id=%d", id)
}

type outputJSON struct {
	Meta      outputMeta        `json:"meta"`
	Vacancies []models.Vacancy  `json:"vacancies"`
}

type outputMeta struct {
	Query     string   `json:"query"`
	Areas     []int    `json:"areas"`
	AreaNames []string `json:"area_names"`
	Period    int      `json:"period"`
	Pages     int      `json:"max_pages"`
	ScrapedAt string   `json:"scraped_at"`
	Total     int      `json:"total"`
}

func main() {
	query := flag.String("q", "Python", "поисковый запрос")
	areasRaw := flag.String("areas", "1,2,92", "регионы через запятую (1=Москва, 2=СПб, 92=Тула)")
	period := flag.Int("period", 30, "период в днях")
	pages := flag.Int("pages", 0, "максимум страниц (0 = все)")
	output := flag.String("o", "data/vacancies.json", "файл для сохранения")
	flag.Parse()

	areas := parseAreas(*areasRaw)
	if len(areas) == 0 {
		fmt.Fprintf(os.Stderr, "Некорректный список регионов: %s\n", *areasRaw)
		os.Exit(1)
	}

	client := parser.NewClient()
	fmt.Printf("HH.ru Parser — поиск: %s\n", *query)
	fmt.Printf("Регионы: %s\n", formatAreas(areas))
	fmt.Printf("Запуск: %s\n", time.Now().Format(time.RFC3339))

	vacancies, err := client.ScrapeAll(*query, areas, *period, *pages)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Ошибка: %v\n", err)
		os.Exit(1)
	}

	out := outputJSON{
		Meta: outputMeta{
			Query:     *query,
			Areas:     areas,
			AreaNames: mapAreasToNames(areas),
			Period:    *period,
			Pages:     *pages,
			ScrapedAt: time.Now().Format(time.RFC3339),
			Total:     len(vacancies),
		},
		Vacancies: vacancies,
	}

	data, err := json.MarshalIndent(out, "", "  ")
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
}

func parseAreas(raw string) []int {
	parts := strings.Split(raw, ",")
	var ids []int
	for _, p := range parts {
		id, err := strconv.Atoi(strings.TrimSpace(p))
		if err != nil {
			continue
		}
		ids = append(ids, id)
	}
	return ids
}

func formatAreas(ids []int) string {
	var names []string
	for _, id := range ids {
		names = append(names, areaName(id))
	}
	return strings.Join(names, ", ")
}

func mapAreasToNames(ids []int) []string {
	var names []string
	for _, id := range ids {
		names = append(names, areaName(id))
	}
	return names
}

func dirFromPath(p string) string {
	for i := len(p) - 1; i >= 0; i-- {
		if p[i] == '\\' || p[i] == '/' {
			return p[:i]
		}
	}
	return ""
}
