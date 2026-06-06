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
    "1–3 года": "middle",
    "3–6 лет": "senior",
    "более 6 лет": "senior",
}


SKILL_ALIASES = {
    "go": "Go",
    "golang": "Go",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "react": "React",
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "ci/cd": "CI/CD",
    "github actions": "GitHub Actions",
    "gitlab": "GitLab",
    "git": "Git",
    "docker": "Docker",
    "redis": "Redis",
    "kafka": "Kafka",
    "rabbitmq": "RabbitMQ",
    "nats": "NATS",
    "grpc": "gRPC",
    "graphql": "GraphQL",
    "rest": "REST",
    "rest api": "REST API",
    "api": "API",
    "sql": "SQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "clickhouse": "ClickHouse",
    "elasticsearch": "Elasticsearch",
    "elastic": "Elasticsearch",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "linux": "Linux",
    "python": "Python",
    "java": "Java",
    "rust": "Rust",
    "c++": "C++",
    "nosql": "NoSQL",
    "html": "HTML",
    "css": "CSS",
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scikit-learn": "scikit-learn",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "langchain": "LangChain",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "nlp": "NLP",
    "llm": "LLM",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "angular": "Angular",
    "redux": "Redux",
    "webpack": "Webpack",
    "agile": "Agile",
    "scrum": "Scrum",
    "jira": "Jira",
    "confluence": "Confluence",
    "microservices": "Microservices",
}

KNOWN_SKILLS_LOWER = sorted({s.lower() for s in SKILL_ALIASES}, key=len, reverse=True)


def normalize_skill(name: str) -> str:
    key = name.lower().replace("\u00a0", " ").strip()
    return SKILL_ALIASES.get(key, name.strip())


def extract_skills(text: str) -> list[str]:
    if not text:
        return []

    text_lower = text.lower()
    found = []
    seen = set()
    for skill in KNOWN_SKILLS_LOWER:
        if skill in text_lower:
            norm = normalize_skill(skill)
            if norm not in seen:
                seen.add(norm)
                found.append(norm)

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
