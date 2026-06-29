"""Application configuration and system-prompt loading."""
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# career_coach/  (project root, parent of the app package)
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_PATH = BASE_DIR / "docs.md"

load_dotenv(BASE_DIR / ".env")

APP_NAME = "Duckie — Career Coach"
TAGLINE = "Твой путь в IT — учись, проверяй знания, расти"
GOAL = "Стать Python-разработчиком с доходом $100k+ к концу года"

# IT-направления для публичной главной страницы.
CATEGORIES = [
    {"slug": "backend", "title": "Backend", "icon": "🛠️", "color": "#5d3fd3",
     "desc": "Python, Java, Go, C#, PHP"},
    {"slug": "databases", "title": "Базы данных", "icon": "🗄️", "color": "#0ea5e9",
     "desc": "SQL, PostgreSQL, проектирование, оптимизация"},
    {"slug": "frontend", "title": "Frontend", "icon": "🎨", "color": "#f59e0b",
     "desc": "HTML, CSS, JavaScript, Vue, React"},
    {"slug": "data-science", "title": "Data Science / ML", "icon": "📊", "color": "#10b981",
     "desc": "Анализ данных, машинное обучение, нейросети"},
    {"slug": "devops", "title": "DevOps", "icon": "⚙️", "color": "#ef4444",
     "desc": "Docker, CI/CD, облака, инфраструктура"},
    {"slug": "mobile", "title": "Мобильная разработка", "icon": "📱", "color": "#ec4899",
     "desc": "iOS, Android, кроссплатформенные приложения"},
    {"slug": "gamedev", "title": "GameDev", "icon": "🎮", "color": "#8b5cf6",
     "desc": "Разработка игр: Unity, Unreal, игровая логика"},
    {"slug": "ui-ux", "title": "UI/UX-дизайн", "icon": "🎯", "color": "#f43f5e",
     "desc": "Проектирование интерфейсов, Figma, прототипы"},
    {"slug": "3d-graphics", "title": "3D и графика", "icon": "🧊", "color": "#06b6d4",
     "desc": "3D-моделирование, Blender, текстуры, рендеринг"},
    {"slug": "qa", "title": "QA / Тестирование", "icon": "🧪", "color": "#22c55e",
     "desc": "Ручное и автоматизированное тестирование"},
]

# --- Database / auth settings (overridable via .env) ---
# Postgres.app default: current OS user, no password, localhost:5432.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres@localhost:5432/duckie_coach",
)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days
RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "30"))
COOKIE_NAME = "cc_session"

# Base URL used to build links in emails (e.g. password reset).
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")


def _parse_seconds(value: str, default: int) -> int:
    """Parse '30s' / '30' into seconds."""
    value = (value or "").strip().lower().rstrip("s")
    return int(value) if value.isdigit() else default


# --- SMTP / email settings (from .env) ---
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", APP_NAME)
SMTP_TLS_POLICY = os.getenv("SMTP_TLS_POLICY", "starttls").lower()  # starttls | ssl | none
SMTP_TIMEOUT = _parse_seconds(os.getenv("SMTP_TIMEOUT", "30"), 30)
# Master switch: emails are sent only when SMTP is configured.
EMAIL_ENABLED = bool(SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD)


@lru_cache
def get_system_prompt() -> str:
    """Read docs.md, which serves as the coach's system prompt.

    Cached so the file is read once per process. The result will later be
    passed to an LLM provider; for now it is only loaded and exposed.
    """
    return DOCS_PATH.read_text(encoding="utf-8")


# Slash commands declared in docs.md, surfaced to the UI as navigation.
SLASH_COMMANDS = [
    {"command": "/help", "label": "Help", "description": "List of slash commands"},
    {"command": "/learn", "label": "Learn", "description": "Enter learning mode"},
    {"command": "/quiz", "label": "Quiz", "description": "Enter quiz mode"},
    {"command": "/challenge", "label": "Challenge", "description": "Code challenge mode"},
    {"command": "/rank", "label": "Rank", "description": "Show level and XP"},
    {"command": "/notes", "label": "Notes", "description": "Condensed study outline"},
    {"command": "/motivate", "label": "Motivate", "description": "Motivational pep talk"},
    {"command": "/esc", "label": "Exit", "description": "Exit all modes"},
]
