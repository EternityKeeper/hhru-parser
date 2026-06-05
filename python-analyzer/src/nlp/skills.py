JUNIOR_KEYWORDS = [
    "junior", "джуниор", "стажёр", "intern", "trainee", "начинающий",
    "младший", "student", "student", "без опыта",
]

MIDDLE_KEYWORDS = [
    "middle", "мидл", "разработчик", "developer", "engineer", "программист",
]

SENIOR_KEYWORDS = [
    "senior", "сеньор", "старший", "lead", "тимлид", "team lead",
    "tech lead", "архитектор", "architect", "principal",
]

EXPERIENCE_LEVEL_MAP = {
    "Нет опыта": "junior",
    "От 1 года до 3 лет": "middle",
    "От 3 до 6 лет": "senior",
    "Более 6 лет": "senior",
}


def extract_skills(text: str) -> list[str]:
    if not text:
        return []

    text_lower = text.lower()
    known_skills = [
        "python", "go", "golang", "rust", "c++", "java", "javascript", "typescript",
        "sql", "postgresql", "mysql", "mongodb", "redis", "clickhouse",
        "docker", "kubernetes", "git", "linux", "ci/cd", "github actions",
        "fastapi", "django", "flask", "react", "vue", "angular",
        "pandas", "numpy", "scikit-learn", "pytorch", "tensorflow", "langchain",
        "kafka", "rabbitmq", "nats", "grpc", "rest", "graphql",
        "aws", "gcp", "azure", "terraform", "ansible",
        "machine learning", "deep learning", "nlp", "llm",
        "nosql", "elasticsearch", "prometheus", "grafana",
        "html", "css", "redux", "webpack", "node.js",
        "oop", "solid", "tdd", "ddd", "microservices",
        "agile", "scrum", "jira", "confluence",
    ]

    found = []
    for skill in known_skills:
        if skill in text_lower:
            found.append(skill)

    return found


def classify_level(title: str, description: str, experience: str) -> str:
    text = f"{title} {description}".lower()

    level_from_exp = EXPERIENCE_LEVEL_MAP.get(experience, "")
    if level_from_exp:
        return level_from_exp

    for kw in SENIOR_KEYWORDS:
        if kw in text:
            return "senior"
    for kw in JUNIOR_KEYWORDS:
        if kw in text:
            return "junior"
    for kw in MIDDLE_KEYWORDS:
        if kw in text:
            return "middle"

    return "middle"
