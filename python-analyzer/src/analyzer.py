from src.nlp.skills import extract_skills, classify_level
from src.models import Vacancy
import pandas as pd
from collections import Counter


def analyze_vacancies(vacancies: list[Vacancy]) -> dict:
    df = pd.DataFrame([v.model_dump() for v in vacancies])

    skills_counter = Counter()
    level_dist = Counter()
    area_dist = Counter()
    salary_data = []

    for v in vacancies:
        skills = extract_skills(v.description or "")
        for s in v.key_skills:
            skills.append(s)
        skills_counter.update(skills)

        level = classify_level(v.name, v.description or "", v.experience)
        level_dist[level] += 1

        area_dist[v.area] += 1

        if v.salary_from or v.salary_to:
            sal = v.salary_to or v.salary_from
            if v.salary_from and v.salary_to:
                sal = (v.salary_from + v.salary_to) // 2
            if v.salary_currency == "RUR":
                salary_data.append(sal)

    result = {
        "total": len(vacancies),
        "top_skills": skills_counter.most_common(30),
        "level_distribution": dict(level_dist),
        "area_distribution": dict(area_dist),
    }

    if salary_data:
        result["salary"] = {
            "avg": int(sum(salary_data) / len(salary_data)),
            "min": min(salary_data),
            "max": max(salary_data),
            "count": len(salary_data),
        }

    return result
