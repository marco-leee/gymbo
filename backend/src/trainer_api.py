"""Internal HTTP API for graph lifecycle (called by SvelteKit)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agent.app.run_controller import RunController

router = APIRouter(prefix="/internal/runs", tags=["trainer-internal"])


def _get_controller() -> RunController:
    from trainer_fastapi_main import get_run_controller

    return get_run_controller()


@router.post("/{run_id}/start")
async def start_run(run_id: str) -> dict:
    controller = _get_controller()
    ctx = await controller.start(run_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "status": ctx.run.status.value}


@router.post("/{run_id}/resume")
async def resume_run(run_id: str) -> dict:
    controller = _get_controller()
    ok = await controller.resume(run_id)
    if not ok:
        raise HTTPException(status_code=409, detail="Run not paused")
    ctx = controller.registry.get(run_id)
    status = ctx.run.status.value if ctx else "active"
    return {"run_id": run_id, "status": status}


@router.post("/{run_id}/end")
async def end_run(run_id: str) -> dict:
    controller = _get_controller()
    ok = await controller.end(run_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "status": "ended"}


@router.post("/{run_id}/pause")
async def pause_run(run_id: str) -> dict:
    controller = _get_controller()
    ok = await controller.pause(run_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "status": "paused"}
