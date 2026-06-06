from pydantic import BaseModel, field_validator


class Vacancy(BaseModel):
    name: str
    area: str
    salary_from: int | None = None
    salary_to: int | None = None
    salary_currency: str = ""
    salary_raw: str = ""
    experience: str = ""
    schedule: str = ""
    description: str = ""
    key_skills: list[str] = []
    employer: str = ""
    published_at: str = ""
    url: str = ""

    @field_validator("key_skills", mode="before")
    @classmethod
    def null_to_empty(cls, v):
        return v or []
