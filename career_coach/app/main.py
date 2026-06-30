"""FastAPI entrypoint for the Duckie career-coach portal (skeleton).

Frontend is a Vue 3 SPA (CDN build) served as static pages; data comes from
the JSON API below. Auth uses Postgres + JWT session cookie. No LLM provider
is wired up yet: /api/chat returns a stub.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

logging.getLogger("duckie").setLevel(logging.INFO)

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .admin import router as admin_router
from .auth import router as auth_router
from .catalog import router as catalog_router
from .config import APP_NAME, GOAL, SLASH_COMMANDS, get_system_prompt
from .db import init_db

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = BASE_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Route our "duckie" logs through uvicorn's handlers so they appear in console.
    duckie_logger = logging.getLogger("duckie")
    duckie_logger.handlers = logging.getLogger("uvicorn").handlers or duckie_logger.handlers
    await init_db()
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(admin_router)


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


@app.get("/reset-password")
async def reset_password_page() -> FileResponse:
    """Serve the password-reset page (token read from the query string)."""
    return FileResponse(TEMPLATES / "reset.html")


@app.get("/admin")
async def admin_page() -> FileResponse:
    """Serve the admin catalog-management page (access checked client-side)."""
    return FileResponse(TEMPLATES / "admin.html")


@app.get("/goal")
@app.get("/goal/{category}")
@app.get("/goal/{category}/{subcategory}")
@app.get("/goal/{category}/{subcategory}/{technology}")
async def goal_page(category: str = "", subcategory: str = "", technology: str = "") -> FileResponse:
    """Goal drill-down pages: categories → subcategories → technologies → courses.

    The current level is read from the URL path on the client.
    """
    return FileResponse(TEMPLATES / "goal.html")


@app.get("/course/{course_id}")
async def course_page(course_id: int) -> FileResponse:
    """Course info page with the learning plan (course id read client-side)."""
    return FileResponse(TEMPLATES / "course.html")


@app.get("/course/{course_id}/view")
async def course_view_page(course_id: int) -> FileResponse:
    """Placeholder 'watch course' page (content to come later)."""
    return FileResponse(TEMPLATES / "course_view.html")


@app.get("/course/{course_id}/reviews")
async def course_reviews_page(course_id: int) -> FileResponse:
    """Standalone page with reviews for a single course (course id read client-side)."""
    return FileResponse(TEMPLATES / "course_reviews.html")


@app.get("/api/meta")
async def meta() -> dict:
    """App metadata for the frontend (name, goal, commands)."""
    return {"app_name": APP_NAME, "goal": GOAL, "commands": SLASH_COMMANDS}


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
