package parser

import (
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/user/hhru-parser/go-scraper/internal/models"
)

const (
	baseSearchURL = "https://hh.ru/search/vacancy"
	baseVacURL    = "https://hh.ru/vacancy"
	maxRetries    = 3
)

var userAgents = []string{
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
}

type Client struct {
	httpClient *http.Client
	rateLimiter <-chan time.Time
	workers     int
}

func NewClient() *Client {
	return &Client{
		httpClient: &http.Client{
			Timeout: 15 * time.Second,
		},
		rateLimiter: time.Tick(300 * time.Millisecond),
		workers:     3,
	}
}

func (c *Client) randUA() string {
	return userAgents[rand.Intn(len(userAgents))]
}

func (c *Client) newReq(urlStr string) (*http.Request, error) {
	req, err := http.NewRequest("GET", urlStr, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", c.randUA())
	return req, nil
}

func (c *Client) doRequest(req *http.Request) (*http.Response, error) {
	<-c.rateLimiter
	var resp *http.Response
	var err error
	for i := 0; i < maxRetries; i++ {
		resp, err = c.httpClient.Do(req)
		if err != nil {
			time.Sleep(time.Second)
			continue
		}
		if resp.StatusCode == 429 {
			resp.Body.Close()
			time.Sleep(2 * time.Second)
			continue
		}
		if resp.StatusCode == 200 || resp.StatusCode == 404 {
			return resp, nil
		}
		resp.Body.Close()
		time.Sleep(time.Second)
	}
	return resp, err
}

func (c *Client) fetchDoc(urlStr string) (*goquery.Document, error) {
	req, err := c.newReq(urlStr)
	if err != nil {
		return nil, err
	}
	resp, err := c.doRequest(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, urlStr)
	}
	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return nil, err
	}
	return doc, nil
}

func (c *Client) ScrapeAll(query string, areas []int, period int, maxPages int) ([]models.Vacancy, error) {
	var allVacancies []models.Vacancy

	for _, area := range areas {
		log.Printf("=== Scraping area %d ===", area)

		var allLinks []vacancyLink

		for page := 0; ; page++ {
			if maxPages > 0 && page >= maxPages {
				break
			}

			u := fmt.Sprintf("%s?text=%s&area=%d&page=%d&items_on_page=50&order_by=publication_time",
				baseSearchURL, url.QueryEscape(query), area, page)
			if period > 0 {
				u += fmt.Sprintf("&search_period=%d", period)
			}

			log.Printf("Search page %d: %s", page, u)

			doc, err := c.fetchDoc(u)
			if err != nil {
				return nil, fmt.Errorf("search page %d (area %d): %v", page, area, err)
			}

			links := parseSearchPage(doc)
			if len(links) == 0 {
				log.Printf("No more vacancies found on page %d (area %d)", page, area)
				break
			}

			allLinks = append(allLinks, links...)
			log.Printf("Found %d vacancies on page %d (total: %d, area %d)", len(links), page, len(allLinks), area)
		}

		if len(allLinks) == 0 {
			log.Printf("No vacancies found for area %d, skipping", area)
			continue
		}

		log.Printf("Fetching details for %d vacancies in area %d...", len(allLinks), area)

		vacancies := c.fetchDetails(allLinks)
		allVacancies = append(allVacancies, vacancies...)
	}

	return allVacancies, nil
}

type vacancyLink struct {
	URL     string
	Title   string
	Company string
	Salary  string
	Address string
	Metro   string
	Exp     string
	Schedule string
}

func parseSearchPage(doc *goquery.Document) []vacancyLink {
	var links []vacancyLink

	doc.Find("div[data-qa=vacancy-serp__vacancy]").Each(func(i int, s *goquery.Selection) {
		v := vacancyLink{}

		titleSel := s.Find("a[data-qa=serp-item__title]")
		v.URL, _ = titleSel.Attr("href")
		v.Title = strings.TrimSpace(titleSel.Find("span[data-qa=serp-item__title-text]").Text())

		v.Company = strings.TrimSpace(s.Find("span[data-qa=vacancy-serp__vacancy-employer-text]").Text())

		compSel := s.Find("span[data-qa=vacancy-serp__vacancy-compensation]")
		if compSel.Length() == 0 {
			compSel = s.Find("span[data-qa^=vacancy-serp__vacancy-compensation-frequency]")
		}
		v.Salary = strings.TrimSpace(compSel.Text())

		v.Address = strings.TrimSpace(s.Find("span[data-qa=vacancy-serp__vacancy-address]").Text())

		metroSel := s.Find("span[data-qa=address-metro-station-name]")
		var metroParts []string
		metroSel.Each(func(i int, sel *goquery.Selection) {
			t := strings.TrimSpace(sel.Text())
			if t != "" {
				metroParts = append(metroParts, t)
			}
		})
		v.Metro = strings.Join(metroParts, ", ")

		expSel := s.Find("[data-qa^=vacancy-serp__vacancy-work-experience]")
		v.Exp = strings.TrimSpace(expSel.First().Text())

		scheduleSel := s.Find("[data-qa^=vacancy-label-work-schedule]")
		v.Schedule = strings.TrimSpace(scheduleSel.First().Text())

		if v.Title != "" && v.URL != "" {
			links = append(links, v)
		}
	})

	return links
}

func (c *Client) fetchDetails(links []vacancyLink) []models.Vacancy {
	var (
		mu        sync.Mutex
		vacancies []models.Vacancy
		wg        sync.WaitGroup
		sem       = make(chan struct{}, c.workers)
	)

	for _, link := range links {
		wg.Add(1)
		sem <- struct{}{}
		go func(l vacancyLink) {
			defer wg.Done()
			defer func() { <-sem }()

			v := c.fetchVacancyPage(l)
			if v != nil {
				mu.Lock()
				vacancies = append(vacancies, *v)
				mu.Unlock()
			}
		}(link)
	}

	wg.Wait()
	return vacancies
}

func (c *Client) fetchVacancyPage(l vacancyLink) *models.Vacancy {
	doc, err := c.fetchDoc(l.URL)
	if err != nil {
		log.Printf("Error fetching %s: %v", l.URL, err)
		return nil
	}

	v := &models.Vacancy{
		Name:       l.Title,
		Employer:   l.Company,
		Area:       l.Address,
		Experience: l.Exp,
		Schedule:   l.Schedule,
	}

	if l.Metro != "" {
		if v.Area != "" {
			v.Area += ", " + l.Metro
		} else {
			v.Area = l.Metro
		}
	}

	if t := strings.TrimSpace(doc.Find("a[data-qa=vacancy-company-name]").First().Text()); t != "" {
		v.Employer = t
	}
	if t := strings.TrimSpace(doc.Find("div[data-qa=vacancy-address-with-map]").Text()); t != "" {
		v.Area = t
	}
	if t := strings.TrimSpace(doc.Find("span[data-qa=vacancy-experience]").Text()); t != "" {
		v.Experience = t
	}
	schedSel := doc.Find("div[data-qa=work-schedule-by-days-text]")
	if schedSel.Length() == 0 {
		schedSel = doc.Find("div[data-qa=work-formats-text]")
	}
	if t := strings.TrimSpace(schedSel.Text()); t != "" {
		v.Schedule = t
	}

	salarySel := doc.Find("div[data-qa=vacancy-salary]")
	if salarySel.Length() == 0 {
		salarySel = doc.Find("span[data-qa=vacancy-salary-compensation-type-net]")
	}
	if t := strings.TrimSpace(salarySel.Text()); t != "" {
		parseSalary(v, t)
	}

	if t := strings.TrimSpace(doc.Find("h1[data-qa=vacancy-title]").Text()); t != "" {
		v.Name = t
	}

	descSel := doc.Find("div[data-qa=vacancy-description]")
	if descSel.Length() > 0 {
		v.Description = strings.TrimSpace(descSel.Text())
	}

	doc.Find("li[data-qa=skills-element]").Each(func(i int, s *goquery.Selection) {
		if skill := strings.TrimSpace(s.Text()); skill != "" {
			v.KeySkills = append(v.KeySkills, skill)
		}
	})

	doc.Find("script[type='application/ld+json']").Each(func(i int, s *goquery.Selection) {
		if v.PublishedAtRaw != "" {
			return
		}
		jsonText := strings.TrimSpace(s.Text())
		if idx := strings.Index(jsonText, `"datePosted"`); idx >= 0 {
			remainder := jsonText[idx+12:]
			colonIdx := strings.Index(remainder, ":")
			if colonIdx >= 0 {
				valStr := strings.TrimSpace(remainder[colonIdx+1:])
				if len(valStr) > 2 && valStr[0] == '"' {
					if endIdx := strings.Index(valStr[1:], `"`); endIdx >= 0 {
						v.PublishedAtRaw = valStr[1 : endIdx+1]
					}
				}
			}
		}
	})

	return v
}

func parseSalary(v *models.Vacancy, raw string) {
	v.SalaryRaw = raw
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return
	}

	curr := ""
	switch {
	case strings.Contains(raw, "₽"):
		curr = "RUR"
	case strings.Contains(raw, "$"):
		curr = "USD"
	case strings.Contains(raw, "€"):
		curr = "EUR"
	case strings.Contains(raw, "₸"):
		curr = "KZT"
	default:
		return
	}
	v.SalaryCurr = curr

	normalized := strings.NewReplacer(
		"\u00a0", "",
		"\u202f", "",
		"\u2009", "",
		" ", "",
	).Replace(raw)

	if currIdx := strings.IndexAny(normalized, "₽$€₸"); currIdx >= 0 {
		normalized = normalized[:currIdx]
	}

	if strings.Contains(normalized, "от") && strings.Contains(normalized, "до") {
		parts := strings.SplitN(normalized, "до", 2)
		if len(parts) == 2 {
			fromStr := strings.TrimSpace(strings.TrimPrefix(strings.TrimPrefix(parts[0], "от"), "от"))
			toStr := strings.TrimSpace(parts[1])
			if from, err := strconv.Atoi(fromStr); err == nil {
				v.SalaryFrom = &from
			}
			if to, err := strconv.Atoi(toStr); err == nil {
				v.SalaryTo = &to
			}
		}
	} else if strings.HasPrefix(normalized, "от") {
		valStr := strings.TrimSpace(strings.TrimPrefix(normalized, "от"))
		if val, err := strconv.Atoi(valStr); err == nil {
			v.SalaryFrom = &val
		}
	} else if strings.HasPrefix(normalized, "до") {
		valStr := strings.TrimSpace(strings.TrimPrefix(normalized, "до"))
		if val, err := strconv.Atoi(valStr); err == nil {
			v.SalaryTo = &val
		}
	} else if strings.Contains(normalized, "-") {
		parts := strings.SplitN(normalized, "-", 2)
		if len(parts) == 2 {
			from, err1 := strconv.Atoi(strings.TrimSpace(parts[0]))
			to, err2 := strconv.Atoi(strings.TrimSpace(parts[1]))
			if err1 == nil {
				v.SalaryFrom = &from
			}
			if err2 == nil {
				v.SalaryTo = &to
			}
		}
	} else {
		if val, err := strconv.Atoi(normalized); err == nil {
			v.SalaryFrom = &val
		}
	}
}
