import pytest
from src.nlp.skills import extract_skills, classify_level


def test_extract_skills_go():
    skills = extract_skills("We use Go for backend development")
    assert "go" in skills


def test_extract_skills_python():
    skills = extract_skills("Python developer with Django experience")
    assert "python" in skills
    assert "django" in skills


def test_extract_skills_multiple():
    skills = extract_skills("Golang, PostgreSQL, Docker, Kubernetes, Kafka")
    for s in ["golang", "postgresql", "docker", "kubernetes", "kafka"]:
        assert s in skills, f"expected {s} in skills"


def test_extract_skills_empty():
    assert extract_skills("") == []
    assert extract_skills(None) == []


def test_classify_level_senior_from_experience():
    assert classify_level("", "", "более 6 лет") == "senior"


def test_classify_level_middle_from_experience():
    assert classify_level("", "", "1–3 года") == "middle"


def test_classify_level_senior_from_title():
    assert classify_level("Senior Go developer", "", "") == "senior"


def test_classify_level_junior_from_title():
    assert classify_level("Junior Python developer", "", "") == "junior"


class TestVacancyModel:
    def test_key_skills_null_becomes_empty(self):
        from src.models import Vacancy
        v = Vacancy(name="test", area="Moscow", key_skills=None)
        assert v.key_skills == []

    def test_key_skills_list_preserved(self):
        from src.models import Vacancy
        v = Vacancy(name="test", area="Moscow", key_skills=["Go", "Python"])
        assert v.key_skills == ["Go", "Python"]


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
        # Check skills
        skill_names = [s for s, _ in result["top_skills"]]
        assert "go" in skill_names
        assert result["area_distribution"] == {"Moscow": 1}
