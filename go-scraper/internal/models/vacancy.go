package models

type Vacancy struct {
	Name          string   `json:"name"`
	Area          string   `json:"area"`
	SalaryFrom    *int     `json:"salary_from,omitempty"`
	SalaryTo      *int     `json:"salary_to,omitempty"`
	SalaryCurr    string   `json:"salary_currency,omitempty"`
	SalaryRaw     string   `json:"salary_raw,omitempty"`
	Experience    string   `json:"experience"`
	Schedule      string   `json:"schedule"`
	Description   string   `json:"description"`
	KeySkills     []string `json:"key_skills"`
	Employer      string   `json:"employer"`
	PublishedAtRaw string  `json:"published_at"`
	URL           string   `json:"url"`
}
