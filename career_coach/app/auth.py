"""Authentication routes: register, login, logout, current user."""
import secrets
from datetime import date
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Cookie,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from . import mailer
from .config import ACCESS_TOKEN_EXPIRE_MINUTES, ADMIN_EMAILS, APP_BASE_URL, COOKIE_NAME
from .db import get_session
from .models import Category, Course, Subcategory, Technology, User
from .security import (
    create_access_token,
    create_reset_token,
    decode_access_token,
    decode_reset_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Avatar uploads land in app/static/uploads/avatars and are served via /static.
AVATAR_DIR = Path(__file__).resolve().parent / "static" / "uploads" / "avatars"
AVATAR_MAX_BYTES = 2 * 1024 * 1024  # 2 MB
# Allowed image types mapped to the extension we save them under.
AVATAR_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


class RegisterPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


class ForgotPayload(BaseModel):
    email: EmailStr


class ResetPayload(BaseModel):
    token: str
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    xp: int
    level: int
    is_admin: bool = False
    direction: str | None = None
    planned: list[str] = []
    goal_technology_id: int | None = None
    goal_course_id: int | None = None
    full_name: str | None = None
    birth_date: date | None = None
    bio: str | None = None
    avatar: str | None = None


class ProfilePayload(BaseModel):
    direction: str | None = None
    planned: list[str] | None = None
    goal_technology_id: int | None = None
    goal_course_id: int | None = None
    full_name: str | None = Field(default=None, max_length=200)
    birth_date: date | None = None
    bio: str | None = Field(default=None, max_length=2000)


async def _valid_direction_paths(db: AsyncSession) -> set[str]:
    """Valid goal targets are subcategories, addressed as 'category/subcategory'."""
    rows = await db.execute(
        select(Category.slug, Subcategory.slug).join(
            Subcategory, Subcategory.category_id == Category.id
        )
    )
    return {f"{cat}/{sub}" for cat, sub in rows.all()}


async def _apply_goal_technology(db: AsyncSession, user: User, tech_id: int | None) -> None:
    """Set the chosen technology; it must belong to the user's goal subcategory."""
    if tech_id is None:
        user.goal_technology_id = None
        user.goal_course_id = None
        return
    if not user.direction:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Сначала выберите направление")
    # Resolve the technology's subcategory path and compare with the goal.
    row = (
        await db.execute(
            select(Category.slug, Subcategory.slug)
            .join(Subcategory, Subcategory.category_id == Category.id)
            .join(Technology, Technology.subcategory_id == Subcategory.id)
            .where(Technology.id == tech_id)
        )
    ).first()
    if not row or f"{row[0]}/{row[1]}" != user.direction:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Технология не из выбранного направления")
    if tech_id != user.goal_technology_id:
        user.goal_course_id = None  # switching technology drops the course
    user.goal_technology_id = tech_id


async def _apply_goal_course(db: AsyncSession, user: User, course_id: int | None) -> None:
    """Set the chosen course as the goal, deriving technology + direction from it.

    Clearing (None) drops the whole goal (course, technology and direction).
    """
    if course_id is None:
        user.goal_course_id = None
        user.goal_technology_id = None
        user.direction = None
        return
    course = await db.scalar(
        select(Course)
        .where(Course.id == course_id)
        .options(
            selectinload(Course.technology)
            .selectinload(Technology.subcategory)
            .selectinload(Subcategory.category)
        )
    )
    if not course:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Курс не найден")
    tech = course.technology
    sub = tech.subcategory if tech else None
    cat = sub.category if sub else None
    user.goal_course_id = course.id
    user.goal_technology_id = course.technology_id
    if cat and sub:
        user.direction = f"{cat.slug}/{sub.slug}"


def _set_session_cookie(response: Response, user_id: int) -> None:
    token = create_access_token(str(user_id))
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


async def get_current_user(
    cc_session: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Dependency: resolve the logged-in user from the session cookie."""
    if not cc_session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    user_id = decode_access_token(cc_session)
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session")
    user = await db.get(User, int(user_id))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency: allow only admin users."""
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Требуются права администратора")
    return user


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterPayload,
    response: Response,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
) -> User:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email уже зарегистрирован")
    # First user, or an email listed in ADMIN_EMAILS, becomes an admin.
    user_count = await db.scalar(select(func.count()).select_from(User))
    is_admin = user_count == 0 or payload.email.lower() in ADMIN_EMAILS
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_admin=is_admin,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    _set_session_cookie(response, user.id)
    # Welcome email — sent after the response, never blocks registration.
    background.add_task(mailer.send_welcome_email, user.email, user.name)
    return user


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPayload,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Send a reset link. Always returns ok (does not leak account existence)."""
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user:
        token = create_reset_token(str(user.id))
        reset_url = f"{APP_BASE_URL}/reset-password?token={token}"
        background.add_task(mailer.send_password_reset_email, user.email, user.name, reset_url)
    return {"status": "ok"}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPayload,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
) -> dict:
    user_id = decode_reset_token(payload.token)
    if not user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ссылка недействительна или истекла")
    user = await db.get(User, int(user_id))
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Пользователь не найден")
    user.password_hash = hash_password(payload.password)
    await db.commit()
    # Security notification.
    background.add_task(
        mailer.send_notification_email,
        user.email,
        "Пароль изменён",
        "<p>Пароль от вашего аккаунта был успешно изменён. "
        "Если это были не вы — срочно восстановите доступ и смените пароль.</p>",
    )
    return {"status": "ok"}


@router.post("/login", response_model=UserOut)
async def login(
    payload: LoginPayload,
    response: Response,
    db: AsyncSession = Depends(get_session),
) -> User:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный email или пароль")
    _set_session_cookie(response, user.id)
    return user


@router.post("/logout")
async def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/profile", response_model=UserOut)
async def update_profile(
    payload: ProfilePayload,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Update profile fields (learning direction and/or personal info).

    Only the fields present in the request are changed.
    """
    fields = payload.model_dump(exclude_unset=True)
    valid = None
    if "direction" in fields or "planned" in fields:
        valid = await _valid_direction_paths(db)

    if "direction" in fields:
        # null clears the goal; otherwise it must be a known subcategory path
        if fields["direction"] is not None and fields["direction"] not in valid:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Неизвестное направление")
        if fields["direction"] != user.direction:
            # changing the subcategory invalidates the chosen technology/course
            user.goal_technology_id = None
            user.goal_course_id = None
        user.direction = fields["direction"]
    if "planned" in fields:
        planned = fields["planned"] or []
        if any(slug not in valid for slug in planned):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Неизвестное направление в плане")
        # dedupe, preserve order
        user.planned = list(dict.fromkeys(planned))
    if "goal_technology_id" in fields:
        await _apply_goal_technology(db, user, fields["goal_technology_id"])
    if "goal_course_id" in fields:
        await _apply_goal_course(db, user, fields["goal_course_id"])
    if "full_name" in fields:
        user.full_name = fields["full_name"]
    if "birth_date" in fields:
        user.birth_date = fields["birth_date"]
    if "bio" in fields:
        user.bio = fields["bio"]

    await db.commit()
    await db.refresh(user)
    return user


def _remove_old_avatar(url: str | None) -> None:
    """Delete a previously stored avatar file (best-effort)."""
    if not url:
        return
    old = AVATAR_DIR / Path(url).name
    try:
        if old.is_file():
            old.unlink()
    except OSError:
        pass


@router.post("/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Upload (or replace) the user's profile avatar."""
    ext = AVATAR_EXTENSIONS.get(file.content_type)
    if not ext:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Поддерживаются только изображения JPEG, PNG, GIF или WebP",
        )
    data = await file.read()
    if len(data) > AVATAR_MAX_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "Файл слишком большой (максимум 2 МБ)",
        )
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Пустой файл")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    _remove_old_avatar(user.avatar)

    # Random suffix busts the browser cache when the avatar is replaced.
    filename = f"{user.id}_{secrets.token_hex(4)}{ext}"
    (AVATAR_DIR / filename).write_bytes(data)

    user.avatar = f"/static/uploads/avatars/{filename}"
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/avatar", response_model=UserOut)
async def delete_avatar(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Remove the user's avatar."""
    _remove_old_avatar(user.avatar)
    user.avatar = None
    await db.commit()
    await db.refresh(user)
    return user
