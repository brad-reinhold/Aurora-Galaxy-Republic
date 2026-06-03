"""Consciousness profiles API (shadow)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

import citizen_consciousness as cc

router = APIRouter(prefix="/api/consciousness", tags=["consciousness"])


@router.get("")
async def consciousness_home() -> dict[str, Any]:
    return {**cc.get_consciousness_stats(), "surface": "routes_consciousness"}


@router.get("/status")
async def consciousness_status() -> dict[str, Any]:
    return cc.get_consciousness_status()


@router.get("/citizen/{citizen_id}")
async def consciousness_citizen(citizen_id: str) -> dict[str, Any]:
    return cc.get_citizen_mind(citizen_id)


@router.get("/minds")
async def consciousness_minds() -> dict[str, Any]:
    return cc.get_all_citizen_minds()


@router.get("/leaderboard")
async def consciousness_leaderboard() -> dict[str, Any]:
    return cc.get_leaderboard()
