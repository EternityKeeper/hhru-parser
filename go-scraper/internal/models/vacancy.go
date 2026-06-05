package models

import "time"

type Vacancy struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Area        string    `json:"area"`
	SalaryFrom  *int      `json:"salary_from,omitempty"`
	SalaryTo    *int      `json:"salary_to,omitempty"`
	SalaryCurr  string    `json:"salary_currency,omitempty"`
	Experience  string    `json:"experience"`
	Schedule    string    `json:"schedule"`
	Employment  string    `json:"employment"`
	Description string    `json:"description"`
	KeySkills   []string  `json:"key_skills"`
	Employer    string    `json:"employer"`
	PublishedAt time.Time `json:"published_at"`
}

type VacancyRaw struct {
	ID      string `json:"id"`
	Name    string `json:"name"`
	Area    struct {
		Name string `json:"name"`
	} `json:"area"`
	Salary *struct {
		From     *int    `json:"from"`
		To       *int    `json:"to"`
		Currency string  `json:"currency"`
	} `json:"salary"`
	Experience struct {
		ID   string `json:"id"`
		Name string `json:"name"`
	} `json:"experience"`
	Schedule struct {
		ID   string `json:"id"`
		Name string `json:"name"`
	} `json:"schedule"`
	Employment struct {
		ID   string `json:"id"`
		Name string `json:"name"`
	} `json:"employment"`
	Description string `json:"description"`
	KeySkills   []struct {
		Name string `json:"name"`
	} `json:"key_skills"`
	Employer struct {
		Name string `json:"name"`
	} `json:"employer"`
	PublishedAt string `json:"published_at"`
}

type SearchRequest struct {
	Text      string `json:"text"`
	Area      int    `json:"area,omitempty"`
	Page      int    `json:"page"`
	PerPage   int    `json:"per_page"`
	Period    int    `json:"period,omitempty"`
}

type SearchResponse struct {
	Items      []VacancyRaw `json:"items"`
	Found      int          `json:"found"`
	Pages      int          `json:"pages"`
	PerPage    int          `json:"per_page"`
	Page       int          `json:"page"`
}
