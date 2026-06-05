from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Vacancy(BaseModel):
    id: str
    name: str
    area: str
    salary_from: Optional[int] = None
    salary_to: Optional[int] = None
    salary_currency: str = ""
    experience: str = ""
    schedule: str = ""
    employment: str = ""
    description: str = ""
    key_skills: list[str] = []
    employer: str = ""
    published_at: Optional[datetime] = None
