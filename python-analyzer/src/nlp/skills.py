import re

try:
    import pymorphy3
    _morph = pymorphy3.MorphAnalyzer()
except ImportError:
    _morph = None


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
    "c#": "C#",
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
    "питон": "Python",
    "джава": "Java",
    "джаваскрипт": "JavaScript",
    "пхп": "PHP",
    "php": "PHP",
    "gitlab ci": "GitLab CI",
    "docker compose": "Docker Compose",
    "dockerfile": "Docker",
    "kuber": "Kubernetes",
    "kubera": "Kubernetes",
    "postgre": "PostgreSQL",
    "kibana": "Kibana",
    "selenium": "Selenium",
    "playwright": "Playwright",
    "puppeteer": "Puppeteer",
    "swagger": "Swagger",
    "openapi": "OpenAPI",
    "restful": "REST",
    "soap": "SOAP",
    "websocket": "WebSocket",
    "websockets": "WebSocket",
    "oauth": "OAuth",
    "jwt": "JWT",
    "oauth2": "OAuth2",
    "oidc": "OpenID Connect",
    "spring": "Spring",
    "hibernate": "Hibernate",
    "asp.net": "ASP.NET",
    ".net": ".NET",
    "react native": "React Native",
    "flutter": "Flutter",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "objective-c": "Objective-C",
    "scala": "Scala",
    "haskell": "Haskell",
    "lua": "Lua",
    "perl": "Perl",
    "r language": "R",
    "matlab": "MATLAB",
    "tableau": "Tableau",
    "airflow": "Airflow",
    "spark": "Apache Spark",
    "hadoop": "Hadoop",
    "nginx": "Nginx",
    "haproxy": "HAProxy",
    "traefik": "Traefik",
    "consul": "Consul",
    "vault": "Vault",
    "istio": "Istio",
    "envoy": "Envoy",
    "helm": "Helm",
    "rancher": "Rancher",
    "sonarqube": "SonarQube",
    "jenkins": "Jenkins",
    "teamcity": "TeamCity",
    "circleci": "CircleCI",
    "github": "GitHub",
    "bitbucket": "Bitbucket",
    "sentry": "Sentry",
    "datadog": "Datadog",
    "new relic": "New Relic",
    "jaeger": "Jaeger",
    "opentelemetry": "OpenTelemetry",
    "cassandra": "Cassandra",
    "mariadb": "MariaDB",
    "sqlite": "SQLite",
    "oracle": "Oracle",
    "mssql": "MS SQL",
    "dynamodb": "DynamoDB",
    "firebase": "Firebase",
    "s3": "Amazon S3",
    "lambda": "AWS Lambda",
    "ec2": "AWS EC2",
    "eks": "Amazon EKS",
    "rds": "Amazon RDS",
    "cloudformation": "AWS CloudFormation",
    "serverless": "Serverless",
}

KNOWN_SKILLS_LOWER = sorted({s.lower() for s in SKILL_ALIASES}, key=len, reverse=True)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[а-яёa-z0-9+#.]+", text.lower())


def _lemmatize(tokens: list[str]) -> set[str]:
    if not _morph:
        return set(tokens)
    lemmas = set()
    for t in tokens:
        if t and t[0].isalpha():
            p = _morph.parse(t)[0]
            if p.score > 0.3:
                lemmas.add(p.normal_form)
        else:
            lemmas.add(t)
    return lemmas


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

    tokens = _tokenize(text)
    lemmas = _lemmatize(tokens)
    for skill in KNOWN_SKILLS_LOWER:
        if skill not in text_lower and skill in lemmas:
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
