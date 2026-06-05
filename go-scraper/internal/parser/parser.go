package parser

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"sync"
	"time"

	"github.com/user/hhru-parser/go-scraper/internal/models"
)

const (
	BaseURL = "https://api.hh.ru"
	PerPage = 100
)

type Client struct {
	http    *http.Client
	mu      sync.Mutex
	calls   int
}

func NewClient() *Client {
	return &Client{
		http: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (c *Client) rateLimit() {
	c.mu.Lock()
	c.calls++
	count := c.calls
	c.mu.Unlock()

	if count%10 == 0 {
		time.Sleep(1 * time.Second)
	}
}

func (c *Client) SearchVacancies(req models.SearchRequest) (*models.SearchResponse, error) {
	c.rateLimit()

	params := url.Values{}
	params.Set("text", req.Text)
	params.Set("page", strconv.Itoa(req.Page))
	params.Set("per_page", strconv.Itoa(PerPage))
	if req.Area > 0 {
		params.Set("area", strconv.Itoa(req.Area))
	}
	if req.Period > 0 {
		params.Set("period", strconv.Itoa(req.Period))
	}

	u := fmt.Sprintf("%s/vacancies?%s", BaseURL, params.Encode())
	resp, err := c.http.Get(u)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API error: %s", resp.Status)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read body failed: %w", err)
	}

	var result models.SearchResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("unmarshal failed: %w", err)
	}

	return &result, nil
}

func (c *Client) GetVacancy(id string) (*models.VacancyRaw, error) {
	c.rateLimit()

	u := fmt.Sprintf("%s/vacancies/%s", BaseURL, id)
	resp, err := c.http.Get(u)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API error: %s", resp.Status)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read body failed: %w", err)
	}

	var v models.VacancyRaw
	if err := json.Unmarshal(body, &v); err != nil {
		return nil, fmt.Errorf("unmarshal failed: %w", err)
	}

	return &v, nil
}

func (c *Client) ScrapeAll(text string, area, period, maxPages int) ([]models.Vacancy, error) {
	var all []models.Vacancy

	first, err := c.SearchVacancies(models.SearchRequest{
		Text:    text,
		Area:    area,
		Period:  period,
		Page:    0,
		PerPage: PerPage,
	})
	if err != nil {
		return nil, fmt.Errorf("first request: %w", err)
	}

	totalPages := first.Pages
	if maxPages > 0 && maxPages < totalPages {
		totalPages = maxPages
	}

	fmt.Printf("Found %d vacancies, scraping %d pages...\n", first.Found, totalPages)

	var mu sync.Mutex
	var wg sync.WaitGroup
	sem := make(chan struct{}, 5)

	processPage := func(page int) {
		defer wg.Done()
		sem <- struct{}{}
		defer func() { <-sem }()

		resp, err := c.SearchVacancies(models.SearchRequest{
			Text:    text,
			Area:    area,
			Period:  period,
			Page:    page,
			PerPage: PerPage,
		})
		if err != nil {
			fmt.Printf("Page %d error: %v\n", page, err)
			return
		}

		for _, raw := range resp.Items {
			v := convertVacancy(raw)
			mu.Lock()
			all = append(all, v)
			mu.Unlock()
		}
		fmt.Printf("Page %d/%d done (%d items)\n", page+1, totalPages, len(resp.Items))
	}

	for page := 0; page < totalPages; page++ {
		wg.Add(1)
		go processPage(page)
	}

	wg.Wait()
	return all, nil
}

func convertVacancy(raw models.VacancyRaw) models.Vacancy {
	v := models.Vacancy{
		ID:          raw.ID,
		Name:        raw.Name,
		Area:        raw.Area.Name,
		Description: raw.Description,
		Experience:  raw.Experience.Name,
		Schedule:    raw.Schedule.Name,
		Employment:  raw.Employment.Name,
		Employer:    raw.Employer.Name,
	}

	if raw.Salary != nil {
		v.SalaryFrom = raw.Salary.From
		v.SalaryTo = raw.Salary.To
		v.SalaryCurr = raw.Salary.Currency
	}

	for _, s := range raw.KeySkills {
		v.KeySkills = append(v.KeySkills, s.Name)
	}

	if t, err := time.Parse(time.RFC3339, raw.PublishedAt); err == nil {
		v.PublishedAt = t
	}

	return v
}

func MarshalVacancies(vacancies []models.Vacancy) ([]byte, error) {
	return json.MarshalIndent(vacancies, "", "  ")
}
