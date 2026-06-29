"""FastAPI entrypoint for the Duckie career-coach portal (skeleton).

Frontend is a Vue 3 SPA (CDN build) served as static pages; data comes from
the JSON API below. Auth uses Postgres + JWT session cookie. No LLM provider
is wired up yet: /api/chat returns a stub.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .auth import router as auth_router
from .config import APP_NAME, CATEGORIES, GOAL, SLASH_COMMANDS, TAGLINE, get_system_prompt
from .db import init_db

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = BASE_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(auth_router)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
async def landing() -> FileResponse:
    """Public landing page with IT categories (no auth required)."""
    return FileResponse(TEMPLATES / "landing.html")


@app.get("/app")
async def portal() -> FileResponse:
    """Serve the portal SPA shell (auth handled client-side via /api/auth/me)."""
    return FileResponse(TEMPLATES / "index.html")


@app.get("/login")
async def login_page() -> FileResponse:
    """Serve the registration / login page."""
    return FileResponse(TEMPLATES / "auth.html")


@app.get("/api/meta")
async def meta() -> dict:
    """App metadata for the frontend (name, goal, commands)."""
    return {"app_name": APP_NAME, "goal": GOAL, "commands": SLASH_COMMANDS}


@app.get("/api/categories")
async def categories() -> dict:
    """IT directions shown on the public landing page."""
    return {"tagline": TAGLINE, "categories": CATEGORIES}


@app.get("/api/health")
async def health() -> dict:
    """Liveness check; confirms the system prompt is loadable."""
    return {"status": "ok", "system_prompt_loaded": bool(get_system_prompt())}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    """Stub chat handler (no LLM connected yet)."""
    return ChatResponse(
        reply=(
            "🦆 (LLM не подключён) Duckie получил сообщение: "
            f"«{payload.message.strip()}». Ответы появятся после подключения провайдера."
        )
    )
