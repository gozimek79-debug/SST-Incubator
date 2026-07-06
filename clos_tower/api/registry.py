"""API – registry (read-only)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_registry():
    return {"registry": [], "note": "Read-only access"}
