"""FastAPI entrypoint for the Duckie career-coach portal (skeleton).

Frontend is a Vue 3 SPA (CDN build) served as a static page; data comes from
the JSON API below. No LLM provider is wired up yet: /api/chat returns a stub.
The system prompt (docs.md) is loaded and exposed so the LLM can be plugged in
later without restructuring.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import APP_NAME, GOAL, SLASH_COMMANDS, get_system_prompt

BASE_DIR = Path(__file__).resolve().parent
INDEX_HTML = BASE_DIR / "templates" / "index.html"

app = FastAPI(title=APP_NAME)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
async def index() -> FileResponse:
    """Serve the Vue SPA shell (not rendered through Jinja)."""
    return FileResponse(INDEX_HTML)


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
    """Stub chat handler.

    No LLM is connected yet. Echoes the message so the UI can be exercised;
    this is where the provider call (using get_system_prompt()) will go.
    """
    return ChatResponse(
        reply=(
            "🦆 (LLM не подключён) Duckie получил сообщение: "
            f"«{payload.message.strip()}». Ответы появятся после подключения провайдера."
        )
    )
