import json
import logging
import os
import subprocess
from typing import Any, Optional

try:
    from src.nlp.skills import classify_level
except ImportError:
    classify_level = None

logger = logging.getLogger(__name__)

AREA_NAMES = {
    "1": "Москва", "2": "Санкт-Петербург", "3": "Екатеринбург",
    "4": "Новосибирск", "53": "Краснодар", "88": "Казань", "92": "Тула",
}


def _scrape_vacancies(
    query: str, areas: str, period: int, scraper_bin: str, data_dir: str
) -> list[dict[str, Any]] | None:
    out_path = os.path.join(data_dir, "bot_check.json")
    cmd = [
        scraper_bin, "-q", query, "-areas", areas,
        "-period", str(period), "-pages", "1", "-o", out_path,
    ]
    logger.info("Running: %s", " ".join(cmd))
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        logger.error("Scraper timed out for query=%s areas=%s", query, areas)
        return None
    except Exception as e:
        logger.error("Scraper failed: %s", e)
        return None

    if not os.path.exists(out_path):
        logger.error("Output file not found: %s", out_path)
        return None

    try:
        with open(out_path, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        logger.error("Failed to load JSON: %s", e)
        return None

    items = raw if isinstance(raw, list) else raw.get("vacancies", [])
    return items


def _format_area_names(areas_str: str) -> str:
    ids = areas_str.split(",")
    names = [AREA_NAMES.get(id.strip(), f"id={id}") for id in ids if id.strip()]
    return ", ".join(names)


def check_subscription(sub: dict, scraper_bin: str, data_dir: str, db) -> Optional[str]:
    vacancies = _scrape_vacancies(
        sub["query"], sub["areas"], sub["period"], scraper_bin, data_dir
    )
    if not vacancies:
        return None

    level_filter = sub.get("level_filter", "").strip().lower()
    new_vacancies = []

    for v in vacancies:
        if level_filter and classify_level:
            try:
                level = classify_level(
                    v.get("name", ""),
                    v.get("description") or "",
                    v.get("experience", ""),
                )
                if level != level_filter:
                    continue
            except Exception:
                pass

        url = v.get("url", "")
        if not url:
            continue
        if db.is_sent(sub["chat_id"], url):
            continue

        new_vacancies.append(v)

    if not new_vacancies:
        return None

    for v in new_vacancies:
        db.mark_sent(sub["chat_id"], v.get("url", ""))

    limit = 50
    shown = new_vacancies[:limit]

    parts = []
    header = f"🔔 <b>Новые вакансии: {sub['query']}</b>\n"
    header += _format_area_names(sub["areas"])
    if sub["period"]:
        header += f" · за {sub['period']} дн."
    if level_filter:
        header += f" · уровень: {level_filter}"
    parts.append(header)

    for i, v in enumerate(shown, 1):
        line = f"\n{i}. <b>{v.get('name', '—')}</b>"
        employer = v.get("employer", "")
        if employer:
            line += f" — {employer}"
        parts.append(line)
        salary_raw = v.get("salary_raw", "")
        if salary_raw:
            parts.append(f"   💰 {salary_raw}")
        area = v.get("area", "")
        if area:
            parts.append(f"   📍 {area}")
        parts.append(f"   🔗 {v.get('url', '')}")

    total = len(new_vacancies)
    if total > limit:
        parts.append(f"\nВсего: {limit} из {total} новых")
    else:
        parts.append(f"\nВсего: {total} новых")

    return "\n".join(parts)
