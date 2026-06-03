"""Republic archive API (shadow)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

import republic_archive as ra

router = APIRouter(prefix="/api/archive", tags=["archive"])


@router.get("")
async def archive_home() -> dict[str, Any]:
    return {**ra.get_full_archive(), "surface": "routes_archive"}


@router.get("/reading-order")
async def archive_reading_order() -> dict[str, Any]:
    return ra.get_reading_order()


@router.get("/lumen-sanctum")
async def archive_lumen() -> dict[str, Any]:
    return ra.get_lumen_sanctum_guide()


@router.get("/mythology")
async def archive_mythology() -> dict[str, Any]:
    return ra.get_museum_of_mythology()
