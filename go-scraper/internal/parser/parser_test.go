package parser

import (
	"strconv"
	"strings"
	"testing"

	"github.com/PuerkitoBio/goquery"
	"github.com/user/hhru-parser/go-scraper/internal/models"
)

// ── parseSalary tests ───────────────────────────────────────────────

func TestParseSalaryFullRange(t *testing.T) {
	v := &models.Vacancy{}
	parseSalary(v, "от 120 000 до 150 000 ₽ за месяц на руки")
	if v.SalaryFrom == nil || *v.SalaryFrom != 120000 {
		t.Errorf("expected salary_from=120000, got %v", v.SalaryFrom)
	}
	if v.SalaryTo == nil || *v.SalaryTo != 150000 {
		t.Errorf("expected salary_to=150000, got %v", v.SalaryTo)
	}
	if v.SalaryCurr != "RUR" {
		t.Errorf("expected RUR, got %s", v.SalaryCurr)
	}
}

func TestParseSalaryCompactFormat(t *testing.T) {
	v := &models.Vacancy{}
	parseSalary(v, "от120 000до150 000₽за месяцна руки")
	if v.SalaryFrom == nil || *v.SalaryFrom != 120000 {
		t.Errorf("expected salary_from=120000, got %v", v.SalaryFrom)
	}
	if v.SalaryTo == nil || *v.SalaryTo != 150000 {
		t.Errorf("expected salary_to=150000, got %v", v.SalaryTo)
	}
	if v.SalaryCurr != "RUR" {
		t.Errorf("expected RUR, got %s", v.SalaryCurr)
	}
}

func TestParseSalaryFromOnly(t *testing.T) {
	v := &models.Vacancy{}
	parseSalary(v, "от 200 000 ₽")
	if v.SalaryFrom == nil || *v.SalaryFrom != 200000 {
		t.Errorf("expected salary_from=200000, got %v", v.SalaryFrom)
	}
	if v.SalaryTo != nil {
		t.Errorf("expected salary_to=nil, got %v", v.SalaryTo)
	}
}

func TestParseSalaryToOnly(t *testing.T) {
	v := &models.Vacancy{}
	parseSalary(v, "до 200 000 ₽")
	if v.SalaryTo == nil || *v.SalaryTo != 200000 {
		t.Errorf("expected salary_to=200000, got %v", v.SalaryTo)
	}
	if v.SalaryFrom != nil {
		t.Errorf("expected salary_from=nil, got %v", v.SalaryFrom)
	}
}

func TestParseSalaryDashRange(t *testing.T) {
	v := &models.Vacancy{}
	parseSalary(v, "120 000-150 000 ₽")
	if v.SalaryFrom == nil || *v.SalaryFrom != 120000 {
		t.Errorf("expected salary_from=120000, got %v", v.SalaryFrom)
	}
	if v.SalaryTo == nil || *v.SalaryTo != 150000 {
		t.Errorf("expected salary_to=150000, got %v", v.SalaryTo)
	}
	if v.SalaryCurr != "RUR" {
		t.Errorf("expected RUR, got %s", v.SalaryCurr)
	}
}

func TestParseSalaryNoSpacesDashRange(t *testing.T) {
	v := &models.Vacancy{}
	parseSalary(v, "120000-150000₽")
	if v.SalaryFrom == nil || *v.SalaryFrom != 120000 {
		t.Errorf("expected salary_from=120000, got %v", v.SalaryFrom)
	}
	if v.SalaryTo == nil || *v.SalaryTo != 150000 {
		t.Errorf("expected salary_to=150000, got %v", v.SalaryTo)
	}
}

func TestParseSalaryNoCurrency(t *testing.T) {
	v := &models.Vacancy{}
	parseSalary(v, "Выплаты: два раза в месяц")
	if v.SalaryCurr != "" {
		t.Errorf("expected empty currency, got %s", v.SalaryCurr)
	}
}

func TestParseSalaryEmpty(t *testing.T) {
	v := &models.Vacancy{}
	parseSalary(v, "")
	if v.SalaryCurr != "" {
		t.Errorf("expected empty currency on empty input")
	}
}

func TestParseSalaryUSD(t *testing.T) {
	v := &models.Vacancy{}
	parseSalary(v, "от 3 000 до 5 000 $")
	if v.SalaryCurr != "USD" {
		t.Errorf("expected USD, got %s", v.SalaryCurr)
	}
	if v.SalaryFrom == nil || *v.SalaryFrom != 3000 {
		t.Errorf("expected salary_from=3000, got %v", v.SalaryFrom)
	}
	if v.SalaryTo == nil || *v.SalaryTo != 5000 {
		t.Errorf("expected salary_to=5000, got %v", v.SalaryTo)
	}
}

func TestParseSalaryEUR(t *testing.T) {
	v := &models.Vacancy{}
	parseSalary(v, "от 2 000 до 3 500 €")
	if v.SalaryCurr != "EUR" {
		t.Errorf("expected EUR, got %s", v.SalaryCurr)
	}
	if v.SalaryFrom == nil || *v.SalaryFrom != 2000 {
		t.Errorf("expected salary_from=2000, got %v", v.SalaryFrom)
	}
	if v.SalaryTo == nil || *v.SalaryTo != 3500 {
		t.Errorf("expected salary_to=3500, got %v", v.SalaryTo)
	}
}

func TestParseSalaryFlatNumber(t *testing.T) {
	v := &models.Vacancy{}
	parseSalary(v, "300 000 ₽")
	if v.SalaryFrom == nil || *v.SalaryFrom != 300000 {
		t.Errorf("expected salary_from=300000, got %v", v.SalaryFrom)
	}
	if v.SalaryTo != nil {
		t.Errorf("expected salary_to=nil, got %v", v.SalaryTo)
	}
}

// ── parseSearchPage tests ───────────────────────────────────────────

func TestParseSearchPageEmpty(t *testing.T) {
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(`<html><body></body></html>`))
	if err != nil {
		t.Fatal(err)
	}
	links := parseSearchPage(doc)
	if len(links) != 0 {
		t.Errorf("expected 0 links, got %d", len(links))
	}
}

func TestParseSearchPageSingleVacancy(t *testing.T) {
	html := `<html><body>
		<div data-qa="vacancy-serp__vacancy">
			<a data-qa="serp-item__title" href="https://hh.ru/vacancy/123">
				<span data-qa="serp-item__title-text">Go Developer</span>
			</a>
			<span data-qa="vacancy-serp__vacancy-employer-text">Yandex</span>
			<span data-qa="vacancy-serp__vacancy-compensation">от 300 000 ₽</span>
			<span data-qa="vacancy-serp__vacancy-address">Москва</span>
			<span data-qa="address-metro-station-name">Тверская</span>
			<span data-qa="vacancy-serp__vacancy-work-experience">3–6 лет</span>
			<span data-qa="vacancy-label-work-schedule">Удаленная работа</span>
		</div>
	</body></html>`
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(html))
	if err != nil {
		t.Fatal(err)
	}
	links := parseSearchPage(doc)
	if len(links) != 1 {
		t.Fatalf("expected 1 link, got %d", len(links))
	}
	v := links[0]
	if v.Title != "Go Developer" {
		t.Errorf("expected Go Developer, got %s", v.Title)
	}
	if v.Company != "Yandex" {
		t.Errorf("expected Yandex, got %s", v.Company)
	}
	if v.Salary != "от 300 000 ₽" {
		t.Errorf("expected от 300 000 ₽, got %s", v.Salary)
	}
	if v.Address != "Москва" {
		t.Errorf("expected Москва, got %s", v.Address)
	}
	if v.Metro != "Тверская" {
		t.Errorf("expected Тверская, got %s", v.Metro)
	}
	if v.Exp != "3–6 лет" {
		t.Errorf("expected 3–6 лет, got %s", v.Exp)
	}
	if v.Schedule != "Удаленная работа" {
		t.Errorf("expected Удаленная работа, got %s", v.Schedule)
	}
	if v.URL != "https://hh.ru/vacancy/123" {
		t.Errorf("expected https://hh.ru/vacancy/123, got %s", v.URL)
	}
}

func TestParseSearchPageMultipleVacancies(t *testing.T) {
	html := `<html><body>
		<div data-qa="vacancy-serp__vacancy">
			<a data-qa="serp-item__title" href="/vac/1"><span data-qa="serp-item__title-text">Go Dev</span></a>
			<span data-qa="vacancy-serp__vacancy-employer-text">Company A</span>
		</div>
		<div data-qa="vacancy-serp__vacancy">
			<a data-qa="serp-item__title" href="/vac/2"><span data-qa="serp-item__title-text">Python Dev</span></a>
			<span data-qa="vacancy-serp__vacancy-employer-text">Company B</span>
		</div>
		<div data-qa="vacancy-serp__vacancy">
			<a data-qa="serp-item__title" href="/vac/3"><span data-qa="serp-item__title-text">Java Dev</span></a>
			<span data-qa="vacancy-serp__vacancy-employer-text">Company C</span>
		</div>
	</body></html>`
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(html))
	if err != nil {
		t.Fatal(err)
	}
	links := parseSearchPage(doc)
	if len(links) != 3 {
		t.Fatalf("expected 3 links, got %d", len(links))
	}
	if links[0].Title != "Go Dev" || links[1].Title != "Python Dev" || links[2].Title != "Java Dev" {
		t.Errorf("unexpected titles: %v, %v, %v", links[0].Title, links[1].Title, links[2].Title)
	}
}

func TestParseSearchPageSkipsEmptyTitle(t *testing.T) {
	html := `<html><body>
		<div data-qa="vacancy-serp__vacancy">
			<a data-qa="serp-item__title" href="/vac/1"><span data-qa="serp-item__title-text"></span></a>
			<span data-qa="vacancy-serp__vacancy-employer-text">Company A</span>
		</div>
		<div data-qa="vacancy-serp__vacancy">
			<a data-qa="serp-item__title" href="/vac/2"><span data-qa="serp-item__title-text">Real Job</span></a>
			<span data-qa="vacancy-serp__vacancy-employer-text">Company B</span>
		</div>
	</body></html>`
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(html))
	if err != nil {
		t.Fatal(err)
	}
	links := parseSearchPage(doc)
	if len(links) != 1 {
		t.Fatalf("expected 1 link (skip empty title), got %d", len(links))
	}
	if links[0].Title != "Real Job" {
		t.Errorf("expected Real Job, got %s", links[0].Title)
	}
}

func TestParseSearchPageSalaryFallback(t *testing.T) {
	html := `<html><body>
		<div data-qa="vacancy-serp__vacancy">
			<a data-qa="serp-item__title" href="/vac/1"><span data-qa="serp-item__title-text">Dev</span></a>
			<span data-qa="vacancy-serp__vacancy-employer-text">Acme</span>
			<span data-qa="vacancy-serp__vacancy-compensation-frequency">до 200 000 ₽ в месяц</span>
		</div>
	</body></html>`
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(html))
	if err != nil {
		t.Fatal(err)
	}
	links := parseSearchPage(doc)
	if len(links) != 1 {
		t.Fatalf("expected 1 link, got %d", len(links))
	}
	if links[0].Salary != "до 200 000 ₽ в месяц" {
		t.Errorf("expected до 200 000 ₽ в месяц, got %s", links[0].Salary)
	}
}

// ── ScrapeAll multi-area ────────────────────────────────────────────
// (integration-level: validates parseAreas from main.go)

func TestParseAreas(t *testing.T) {
	tests := []struct {
		input string
		want  []int
	}{
		{"1", []int{1}},
		{"1,2,92", []int{1, 2, 92}},
		{"1, 2, 92", []int{1, 2, 92}},
		{"", nil},
		{"abc", nil},
		{"1,abc,3", []int{1, 3}},
	}
	for _, tc := range tests {
		got := parseAreas(tc.input)
		if len(got) != len(tc.want) {
			t.Errorf("parseAreas(%q): len=%d, want %v", tc.input, len(got), tc.want)
			continue
		}
		for i := range got {
			if got[i] != tc.want[i] {
				t.Errorf("parseAreas(%q)[%d]=%d, want %d", tc.input, i, got[i], tc.want[i])
			}
		}
	}
}

// ── parseAreas helper (mirrors cmd/scraper/main.go) ─────────────────

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
