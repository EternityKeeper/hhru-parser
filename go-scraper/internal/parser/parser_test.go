package parser

import (
	"strings"
	"testing"

	"github.com/PuerkitoBio/goquery"
	"github.com/user/hhru-parser/go-scraper/internal/models"
)

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
