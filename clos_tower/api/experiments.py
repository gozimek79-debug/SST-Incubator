"""API – experiments (read-only)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_experiments():
    return {"experiments": [], "note": "Registry integration pending"}


@router.get("/{run_id}")
async def get_experiment(run_id: str):
    return {"run_id": run_id, "note": "Read-only endpoint"}
