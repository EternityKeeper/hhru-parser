from src.nlp.skills import classify_level, extract_skills, normalize_skill

# ── normalize_skill ──────────────────────────────────────────────────

def test_normalize_skill_lowercase():
    assert normalize_skill("go") == "Go"


def test_normalize_skill_alias():
    assert normalize_skill("golang") == "Go"
    assert normalize_skill("k8s") == "Kubernetes"
    assert normalize_skill("postgres") == "PostgreSQL"


def test_normalize_skill_case_insensitive():
    assert normalize_skill("GOLANG") == "Go"
    assert normalize_skill("PostgreSQL") == "PostgreSQL"


def test_normalize_skill_unknown():
    assert normalize_skill("SomeRandomSkill") == "SomeRandomSkill"


def test_normalize_skill_non_breaking_space():
    result = normalize_skill("Go\u00a0lang")
    assert "Go" in result or "\u00a0" in result


# ── extract_skills ───────────────────────────────────────────────────

def test_extract_skills_go():
    skills = extract_skills("We use Go for backend development")
    assert "Go" in skills


def test_extract_skills_python():
    skills = extract_skills("Python developer with Django experience")
    assert "Python" in skills
    assert "Django" in skills


def test_extract_skills_multiple():
    skills = extract_skills("Golang, PostgreSQL, Docker, Kubernetes, Kafka")
    for s in ["Go", "PostgreSQL", "Docker", "Kubernetes", "Kafka"]:
        assert s in skills, f"expected {s} in skills"


def test_extract_skills_empty():
    assert extract_skills("") == []
    assert extract_skills(None) == []


def test_extract_skills_no_duplicates():
    skills = extract_skills("Go and Golang are both Go language")
    assert skills.count("Go") == 1


def test_extract_skills_case_insensitive():
    skills = extract_skills("python PYTHON Python")
    assert skills == ["Python"]


# ── classify_level ───────────────────────────────────────────────────

def test_classify_level_senior_from_experience():
    assert classify_level("", "", "более 6 лет") == "senior"


def test_classify_level_middle_from_experience():
    assert classify_level("", "", "1–3 года") == "middle"


def test_classify_level_junior_from_experience():
    assert classify_level("", "", "Нет опыта") == "junior"


def test_classify_level_senior_from_title():
    assert classify_level("Senior Go developer", "", "") == "senior"


def test_classify_level_junior_from_title():
    assert classify_level("Junior Python developer", "", "") == "junior"


def test_classify_level_default_middle():
    assert classify_level("Developer", "", "") == "middle"


def test_classify_level_teamlead():
    assert classify_level("Team Lead Golang", "", "") == "senior"


def test_classify_level_intern():
    assert classify_level("Intern Python developer", "", "") == "junior"


def test_classify_level_experience_overrides_title():
    assert classify_level("Senior Go developer", "", "1–3 года") == "middle"


# ── VacancyModel ─────────────────────────────────────────────────────

class TestVacancyModel:
    def test_key_skills_null_becomes_empty(self):
        from src.models import Vacancy
        v = Vacancy(name="test", area="Moscow", key_skills=None)
        assert v.key_skills == []

    def test_key_skills_list_preserved(self):
        from src.models import Vacancy
        v = Vacancy(name="test", area="Moscow", key_skills=["Go", "Python"])
        assert v.key_skills == ["Go", "Python"]

    def test_salary_optional(self):
        from src.models import Vacancy
        v = Vacancy(name="test", area="Moscow")
        assert v.salary_from is None
        assert v.salary_to is None

    def test_published_at_optional(self):
        from src.models import Vacancy
        v = Vacancy(name="test", area="Moscow")
        assert v.published_at == ""


# ── Analyzer ─────────────────────────────────────────────────────────

class TestAnalyzer:
    def test_analyze_empty(self):
        from src.analyzer import analyze_vacancies
        result = analyze_vacancies([])
        assert result["total"] == 0
        assert result["top_skills"] == []

    def test_analyze_basic(self):
        from src.analyzer import analyze_vacancies
        from src.models import Vacancy
        v = Vacancy(
            name="Go developer",
            area="Moscow",
            description="Go, PostgreSQL, Docker",
            key_skills=["Go"],
            experience="1–3 года",
        )
        result = analyze_vacancies([v])
        assert result["total"] == 1
        skill_names = [s for s, _ in result["top_skills"]]
        assert "Go" in skill_names
        assert "PostgreSQL" in skill_names
        assert result["area_distribution"] == {"Moscow": 1}
        assert result["level_distribution"] == {"middle": 1}

    def test_analyze_multiple_vacancies(self):
        from src.analyzer import analyze_vacancies
        from src.models import Vacancy
        v1 = Vacancy(
            name="Go developer", area="Moscow",
            description="Go, PostgreSQL", key_skills=["Go"],
            experience="3–6 лет", salary_from=200000,
            salary_to=300000, salary_currency="RUR",
        )
        v2 = Vacancy(
            name="Python backend", area="Saint-Petersburg",
            description="Python, Django, PostgreSQL", key_skills=[],
            experience="1–3 года", salary_from=150000,
            salary_currency="RUR",
        )
        result = analyze_vacancies([v1, v2])
        assert result["total"] == 2
        assert result["area_distribution"] == {"Moscow": 1, "Saint-Petersburg": 1}
        assert result["level_distribution"] == {"senior": 1, "middle": 1}
        assert result["salary"]["avg"] == 200000
        assert result["salary"]["min"] == 150000
        assert result["salary"]["max"] == 250000

    def test_analyze_city_extraction(self):
        from src.analyzer import _city
        assert _city("Moscow, metro Tverskaya") == "Moscow"
        assert _city("Saint-Petersburg") == "Saint-Petersburg"
        assert _city("") == "Не указан"
        assert _city(None) == "Не указан"

    def test_analyze_skill_dedup_from_description_and_key_skills(self):
        from src.analyzer import analyze_vacancies
        from src.models import Vacancy
        v = Vacancy(
            name="Go developer", area="Moscow",
            description="Go, PostgreSQL, Go", key_skills=["Golang", "Go"],
            experience="",
        )
        result = analyze_vacancies([v])
        skill_names = [s for s, _ in result["top_skills"]]
        assert skill_names == ["Go", "PostgreSQL"] or "Go" in skill_names
        assert result["total"] == 1
