"""Rest subgraph LangGraph nodes."""

from __future__ import annotations

from langchain_core.runnables import RunnableConfig

from agent.domain.models import RunPhase, RunStatus
from agent.graphs.runtime import get_publisher, get_run_context
from agent.graphs.state import TrainerGraphState, apply_status_phase
from agent.infra.clock import SystemClock

REST_TICK_SEC = 15


def _clock(config: RunnableConfig) -> SystemClock:
    cfg = config.get("configurable") or {}
    return cfg.get("clock") or SystemClock()


async def start_timer(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    publisher = get_publisher(config)
    duration = ctx.run.config.rest_duration_sec
    apply_status_phase(ctx.run, RunStatus.RESTING, RunPhase.REST)
    await publisher.publish_phase_message(
        ctx,
        phase="rest",
        message=f"Rest for {duration} seconds. Breathe and recover.",
        metadata={"set_number": ctx.run.current_set_number, "duration_sec": duration},
    )
    await publisher.publish_state(ctx)
    return {**state, "rest_elapsed_sec": 0, "rest_duration_sec": duration}


async def during_rest_tick(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    publisher = get_publisher(config)
    clock = _clock(config)
    duration = state.get("rest_duration_sec", ctx.run.config.rest_duration_sec)
    elapsed = state.get("rest_elapsed_sec", 0)

    if ctx.end_rest_requested or ctx.end_requested or ctx.paused:
        ctx.end_rest_requested = False
        return {**state, "rest_complete": True, "rest_skipped": True}

    tick = min(REST_TICK_SEC, max(0, duration - elapsed))
    if tick > 0:
        await clock.sleep(tick)
    elapsed += tick

    if elapsed < duration:
        msg = "Stay loose — next set coming up."
        ctx.rest_activities.append(msg)
        await publisher.publish_phase_message(
            ctx,
            phase="rest",
            message=msg,
            metadata={"set_number": ctx.run.current_set_number},
        )

    return {**state, "rest_elapsed_sec": elapsed, "rest_complete": elapsed >= duration}


async def finish_rest(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    apply_status_phase(ctx.run, RunStatus.ACTIVE, RunPhase.SET_IN_PROGRESS)
    return {**state, "rest_skipped": False}


def route_rest_tick(state: TrainerGraphState) -> str:
    if state.get("rest_complete"):
        return "done"
    return "tick"
