"""Public catalog API: categories and their subcategories (read-only)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .config import TAGLINE
from .db import get_session
from .models import Category

router = APIRouter(prefix="/api", tags=["catalog"])


def sub_dict(s) -> dict:
    return {
        "id": s.id, "slug": s.slug, "title": s.title,
        "description": s.description, "position": s.position,
    }


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
        .options(selectinload(Category.subcategories))
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
        .options(selectinload(Category.subcategories))
    )
    if not cat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Категория не найдена")
    return cat_dict(cat)
