"""Application configuration and system-prompt loading."""
from functools import lru_cache
from pathlib import Path

# career_coach/  (project root, parent of the app package)
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_PATH = BASE_DIR / "docs.md"

APP_NAME = "Duckie — Career Coach"
GOAL = "Стать Python-разработчиком с доходом $100k+ к концу года"


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
