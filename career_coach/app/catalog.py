"""Public catalog API: categories and their subcategories (read-only)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .config import TAGLINE
from .db import get_session
from .models import Category, Subcategory, Technology

router = APIRouter(prefix="/api", tags=["catalog"])


def course_dict(c) -> dict:
    return {
        "id": c.id, "title": c.title, "author": c.author,
        "duration": c.duration, "url": c.url,
        "description": c.description, "position": c.position,
    }


def tech_dict(t) -> dict:
    return {
        "id": t.id, "slug": t.slug, "title": t.title,
        "description": t.description, "position": t.position,
        "courses": [course_dict(c) for c in t.courses],
    }


def sub_dict(s) -> dict:
    return {
        "id": s.id, "slug": s.slug, "title": s.title,
        "description": s.description, "position": s.position,
        "technologies": [tech_dict(t) for t in s.technologies],
    }


# Eager-load the full category → subcategory → technology → course tree so the
# dict builders never trigger a lazy load under async (which would error).
_TREE_LOADER = (
    selectinload(Category.subcategories)
    .selectinload(Subcategory.technologies)
    .selectinload(Technology.courses)
)


def cat_dict(c) -> dict:
    return {
        "id": c.id, "slug": c.slug, "title": c.title, "icon": c.icon,
        "color": c.color,
        # 'desc' kept for backward compatibility with existing frontend
        "desc": c.description, "description": c.description,
        "position": c.position,
        "subcategories": [sub_dict(s) for s in c.subcategories],
    }


async def _all_categories(db: AsyncSession) -> list[Category]:
    result = await db.scalars(
        select(Category)
        .options(_TREE_LOADER)
        .order_by(Category.position, Category.id)
    )
    return list(result.all())


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_session)) -> dict:
    cats = await _all_categories(db)
    return {"tagline": TAGLINE, "categories": [cat_dict(c) for c in cats]}


@router.get("/categories/{slug}")
async def get_category(slug: str, db: AsyncSession = Depends(get_session)) -> dict:
    cat = await db.scalar(
        select(Category)
        .where(Category.slug == slug)
        .options(_TREE_LOADER)
    )
    if not cat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Категория не найдена")
    return cat_dict(cat)
