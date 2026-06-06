import re
from collections import Counter

from src.models import Vacancy
from src.nlp.skills import classify_level, extract_skills, normalize_skill


def _city(area: str) -> str:
    if not area:
        return "Не указан"
    m = re.match(r"^([^,]+)", area)
    return m.group(1).strip() if m else area


def analyze_vacancies(vacancies: list[Vacancy]) -> dict:
    skills_counter = Counter()
    level_dist = Counter()
    area_dist = Counter()
    salary_data = []
    skills_by_area: dict[str, Counter] = {}

    for v in vacancies:
        skills = extract_skills(v.description or "")
        seen = set(skills)
        for s in v.key_skills:
            norm = normalize_skill(s)
            if norm not in seen:
                seen.add(norm)
                skills.append(norm)
        skills_counter.update(skills)

        level = classify_level(v.name, v.description or "", v.experience)
        level_dist[level] += 1

        city = _city(v.area)
        area_dist[city] += 1

        if city not in skills_by_area:
            skills_by_area[city] = Counter()
        skills_by_area[city].update(skills)

        if v.salary_from or v.salary_to:
            sal = v.salary_to or v.salary_from
            if v.salary_from and v.salary_to:
                sal = (v.salary_from + v.salary_to) // 2
            if v.salary_currency == "RUR":
                salary_data.append(sal)

    top_skills = skills_counter.most_common(30)
    top_skills_names = [s for s, _ in top_skills[:10]]

    result = {
        "total": len(vacancies),
        "top_skills": top_skills,
        "level_distribution": dict(level_dist),
        "area_distribution": dict(area_dist),
        "skills_by_area": {
            city: {s: cnt for s, cnt in counter.items() if s in top_skills_names}
            for city, counter in sorted(skills_by_area.items(), key=lambda x: -area_dist.get(x[0], 0))[:7]
        },
    }

    if salary_data:
        result["salary"] = {
            "avg": int(sum(salary_data) / len(salary_data)),
            "min": min(salary_data),
            "max": max(salary_data),
            "count": len(salary_data),
        }

    return result
