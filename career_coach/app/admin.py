"""Admin catalog management: CRUD for categories and subcategories."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import require_admin
from .catalog import _TREE_LOADER, cat_dict
from .db import get_session
from .models import Category, Subcategory

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
