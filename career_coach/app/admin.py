"""Admin catalog management: CRUD for categories and subcategories."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_user, require_admin
from .catalog import _TREE_LOADER, cat_dict
from .config import ROLE_ADMIN, ROLE_MENTOR, ROLES
from .db import get_session
from .models import Category, Subcategory, User

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


class CategoryIn(BaseModel):
    slug: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    title: str = Field(min_length=1, max_length=120)
    icon: str = Field(default="📚", max_length=16)
    color: str = Field(default="#5d3fd3", max_length=9)
    description: str = Field(default="", max_length=255)


class CategoryPatch(BaseModel):
    slug: str | None = Field(default=None, min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    title: str | None = Field(default=None, min_length=1, max_length=120)
    icon: str | None = Field(default=None, max_length=16)
    color: str | None = Field(default=None, max_length=9)
    description: str | None = Field(default=None, max_length=255)
    position: int | None = None


class SubcategoryIn(BaseModel):
    slug: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=255)


class SubcategoryPatch(BaseModel):
    slug: str | None = Field(default=None, min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=255)
    position: int | None = None


async def _load_category(category_id: int, db: AsyncSession) -> Category:
    cat = await db.scalar(
        select(Category)
        .where(Category.id == category_id)
        .options(_TREE_LOADER)
        # refresh identity-mapped state so freshly added subs are included
        .execution_options(populate_existing=True)
    )
    if not cat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Категория не найдена")
    return cat


# --- Categories ---

@router.get("/categories")
async def admin_list(db: AsyncSession = Depends(get_session)) -> list[dict]:
    result = await db.scalars(
        select(Category).options(_TREE_LOADER).order_by(Category.position, Category.id)
    )
    return [cat_dict(c) for c in result.all()]


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryIn, db: AsyncSession = Depends(get_session)) -> dict:
    pos = await db.scalar(select(func.count()).select_from(Category))
    cat = Category(position=pos, **payload.model_dump())
    db.add(cat)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Категория с таким slug уже существует")
    return await _category_out(cat.id, db)


@router.patch("/categories/{category_id}")
async def update_category(
    category_id: int, payload: CategoryPatch, db: AsyncSession = Depends(get_session)
) -> dict:
    cat = await _load_category(category_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Категория с таким slug уже существует")
    return await _category_out(category_id, db)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_session)) -> None:
    cat = await _load_category(category_id, db)
    await db.delete(cat)
    await db.commit()


# --- Subcategories ---

@router.post("/categories/{category_id}/subcategories", status_code=status.HTTP_201_CREATED)
async def create_subcategory(
    category_id: int, payload: SubcategoryIn, db: AsyncSession = Depends(get_session)
) -> dict:
    cat = await _load_category(category_id, db)
    pos = len(cat.subcategories)
    db.add(Subcategory(category_id=category_id, position=pos, **payload.model_dump()))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Подкатегория с таким slug уже существует")
    return await _category_out(category_id, db)


@router.patch("/subcategories/{sub_id}")
async def update_subcategory(
    sub_id: int, payload: SubcategoryPatch, db: AsyncSession = Depends(get_session)
) -> dict:
    sub = await db.get(Subcategory, sub_id)
    if not sub:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Подкатегория не найдена")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sub, field, value)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Подкатегория с таким slug уже существует")
    return await _category_out(sub.category_id, db)


@router.delete("/subcategories/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subcategory(sub_id: int, db: AsyncSession = Depends(get_session)) -> None:
    sub = await db.get(Subcategory, sub_id)
    if not sub:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Подкатегория не найдена")
    await db.delete(sub)
    await db.commit()


async def _category_out(category_id: int, db: AsyncSession) -> dict:
    return cat_dict(await _load_category(category_id, db))


# --- Users & roles ---

class RolePatch(BaseModel):
    role: str


def _user_dict(u: User) -> dict:
    return {"id": u.id, "name": u.name, "email": u.email, "role": u.role}


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_session)) -> list[dict]:
    """All users with their roles (admin only), newest first."""
    result = await db.scalars(select(User).order_by(User.id.desc()))
    return [_user_dict(u) for u in result.all()]


@router.patch("/users/{user_id}/role")
async def set_user_role(
    user_id: int,
    payload: RolePatch,
    me: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Change a user's role. Admins cannot change their own role (avoid lockout)."""
    if payload.role not in ROLES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Неизвестная роль")
    if user_id == me.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Нельзя менять собственную роль")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    user.role = payload.role
    user.is_admin = payload.role == ROLE_ADMIN  # keep legacy flag in sync
    if payload.role in (ROLE_MENTOR, ROLE_ADMIN):
        user.mentor_request = None  # promoting clears any pending application
    await db.commit()
    return _user_dict(user)


# --- Mentor applications ---

class MentorDecision(BaseModel):
    decision: str  # "approve" | "reject"


@router.get("/mentor-requests")
async def list_mentor_requests(db: AsyncSession = Depends(get_session)) -> list[dict]:
    """Pending applications to become a mentor (admin only)."""
    result = await db.scalars(
        select(User).where(User.mentor_request == "pending").order_by(User.id.desc())
    )
    return [
        {"id": u.id, "name": u.name, "email": u.email, "note": u.mentor_request_note}
        for u in result.all()
    ]


@router.patch("/mentor-requests/{user_id}")
async def decide_mentor_request(
    user_id: int, payload: MentorDecision, db: AsyncSession = Depends(get_session)
) -> dict:
    """Approve (→ mentor) or reject a pending mentor application."""
    if payload.decision not in ("approve", "reject"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Неизвестное решение")
    user = await db.get(User, user_id)
    if not user or user.mentor_request != "pending":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
    if payload.decision == "approve":
        user.role = ROLE_MENTOR
        user.is_admin = False
        user.mentor_request = None
        user.mentor_request_note = None
    else:
        user.mentor_request = "rejected"
    await db.commit()
    return {"id": user.id, "role": user.role, "mentor_request": user.mentor_request}
