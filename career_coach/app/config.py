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
# Категории/подкатегории теперь хранятся в БД (см. app/models.py и app/seed.py).

# --- Геймификация: правила XP/уровней (из docs.md) ---
XP_PER_LEVEL = 100                       # XP на один уровень
MAX_LEVEL = 50                           # потолок уровня
MAX_XP = XP_PER_LEVEL * MAX_LEVEL        # 5000 — выше XP не растёт
# Сколько XP даёт завершённое действие. Суммы фиксированы на сервере,
# клиент присылает только название действия.
XP_REWARDS = {
    "quiz": 10,        # +10 XP за квиз
    "challenge": 100,  # +100 XP за код-челлендж
}

# --- Сертификаты (Этап 6) ---
# Уровни-вехи, за достижение которых выдаётся сертификат-ранг. Ранги привязаны
# к карьерной лестнице разработчика (цель Duckie — стать senior-разработчиком).
CERT_LEVELS = (5, 10, 25, 50)
CERT_RANKS = {
    5: "Стажёр",
    10: "Джуниор-разработчик",
    25: "Мидл-разработчик",
    50: "Сеньор-разработчик",
}

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

# Emails that always get admin rights. The very first registered user also
# becomes admin automatically.
ADMIN_EMAILS = {
    e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()
}
# Emails that get the mentor role on registration (unless already admin).
MENTOR_EMAILS = {
    e.strip().lower() for e in os.getenv("MENTOR_EMAILS", "").split(",") if e.strip()
}

# User roles. 'user' — learner; 'mentor' — can add courses and help learners;
# 'admin' — full catalog + user management.
ROLE_USER = "user"
ROLE_MENTOR = "mentor"
ROLE_ADMIN = "admin"
ROLES = (ROLE_USER, ROLE_MENTOR, ROLE_ADMIN)


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
