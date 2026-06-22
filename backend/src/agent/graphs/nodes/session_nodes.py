"""Session graph LangGraph nodes."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from langchain_core.runnables import RunnableConfig

from agent.domain.exercise_feedback import build_feedback_summary, format_feedback_text
from agent.domain.models import RunPhase, RunStatus
from agent.domain.rep_completion import has_more_sets
from agent.exercises.registry import get_profile
from agent.graphs.runtime import get_publisher, get_repository, get_run_context
from agent.graphs.state import TrainerGraphState, apply_status_phase, state_patch_from_run


async def _persist(ctx, repository) -> None:
    ctx.run.updated_at = datetime.now(UTC)
    repository.update_run(ctx.run)


async def _phase_delay(ctx) -> None:
    await asyncio.sleep(0.1 if ctx.dry_run else 2)


async def prepare(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    publisher = get_publisher(config)
    repository = get_repository(config)
    profile = get_profile(ctx.run.exercise_type)

    ctx.run.started_at = datetime.now(UTC)
    apply_status_phase(ctx.run, RunStatus.PREPARING, RunPhase.PREPARE)
    await _persist(ctx, repository)
    await publisher.publish_phase_message(ctx, phase="prepare", message=profile.prep_message)
    await publisher.publish_state(ctx)
    await _phase_delay(ctx)
    return state_patch_from_run(ctx.run)


async def setup(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    publisher = get_publisher(config)
    repository = get_repository(config)
    profile = get_profile(ctx.run.exercise_type)

    apply_status_phase(ctx.run, RunStatus.SETUP, RunPhase.SETUP)
    await _persist(ctx, repository)
    await publisher.publish_phase_message(ctx, phase="setup", message=profile.setup_message)
    await publisher.publish_state(ctx)
    await _phase_delay(ctx)
    apply_status_phase(ctx.run, RunStatus.ACTIVE, RunPhase.SET_IN_PROGRESS)
    await _persist(ctx, repository)
    await publisher.publish_state(ctx)
    return state_patch_from_run(ctx.run)


async def announce_set(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    publisher = get_publisher(config)
    await publisher.publish_phase_message(
        ctx,
        phase="set_announce",
        message=f"Set {ctx.run.current_set_number} — target {ctx.run.config.target_reps_per_set} reps.",
        metadata={
            "set_number": ctx.run.current_set_number,
            "target_reps": ctx.run.config.target_reps_per_set,
        },
    )
    return state_patch_from_run(ctx.run)


async def after_set(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    if ctx.end_requested:
        return {**state_patch_from_run(ctx.run), "end_requested": True}
    if state.get("set_emergency") or (ctx.paused and not state.get("set_complete")):
        return {
            **state_patch_from_run(ctx.run),
            "paused": ctx.paused,
            "set_emergency": bool(state.get("set_emergency")),
        }
    if not state.get("set_complete"):
        return state_patch_from_run(ctx.run)

    ctx.run.completed_sets += 1
    return state_patch_from_run(ctx.run, set_complete=True)


async def increment_set(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    ctx.run.current_set_number += 1
    ctx.run.merged_observation_state.completed_reps = 0
    return state_patch_from_run(ctx.run)


async def exercise_feedback(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    publisher = get_publisher(config)
    repository = get_repository(config)
    apply_status_phase(ctx.run, RunStatus.FEEDBACK, RunPhase.FEEDBACK)
    await _persist(ctx, repository)

    coaching = repository.list_coaching_for_run(ctx.run.id)
    summary = build_feedback_summary(
        merged=ctx.run.merged_observation_state,
        coaching_events=coaching,
        planned_sets=ctx.run.config.planned_sets,
        target_reps=ctx.run.config.target_reps_per_set,
    )
    feedback = format_feedback_text(summary)
    ctx.run.exercise_feedback = feedback
    await publisher.publish_phase_message(
        ctx, phase="feedback", message=feedback, metadata=summary
    )
    return state_patch_from_run(ctx.run)


async def session_complete(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    publisher = get_publisher(config)
    repository = get_repository(config)

    if ctx.end_requested and not ctx.run.exercise_feedback:
        coaching = repository.list_coaching_for_run(ctx.run.id)
        summary = build_feedback_summary(
            merged=ctx.run.merged_observation_state,
            coaching_events=coaching,
            planned_sets=ctx.run.config.planned_sets,
            target_reps=ctx.run.config.target_reps_per_set,
        )
        ctx.run.exercise_feedback = format_feedback_text(summary)

    apply_status_phase(ctx.run, RunStatus.ENDED, RunPhase.SESSION_COMPLETE)
    ctx.run.ended_at = datetime.now(UTC)
    await _persist(ctx, repository)
    await publisher.publish_phase_message(
        ctx,
        phase="session_complete",
        message="Exercise complete. Great work!",
    )
    await publisher.publish_state(ctx)
    return state_patch_from_run(ctx.run)


def route_after_prepare(state: TrainerGraphState, config: RunnableConfig) -> str:
    ctx = get_run_context(config)
    if ctx.end_requested or ctx.paused:
        return "end"
    return "setup"


def route_after_setup(state: TrainerGraphState, config: RunnableConfig) -> str:
    ctx = get_run_context(config)
    if ctx.end_requested or ctx.paused:
        return "end"
    return "sets"


def route_after_set(state: TrainerGraphState, config: RunnableConfig) -> str:
    ctx = get_run_context(config)
    if ctx.end_requested:
        return "end"
    if ctx.paused or state.get("set_emergency"):
        return "pause"
    if not has_more_sets(ctx.run.current_set_number, ctx.run.config.planned_sets):
        return "feedback"
    if ctx.run.config.rest_needed and ctx.run.config.rest_duration_sec > 0:
        return "rest"
    return "next_set"


def route_after_rest(state: TrainerGraphState, config: RunnableConfig) -> str:
    ctx = get_run_context(config)
    if ctx.end_requested or ctx.paused:
        return "pause"
    return "next_set"


def route_more_sets(state: TrainerGraphState, config: RunnableConfig) -> str:
    ctx = get_run_context(config)
    if not has_more_sets(ctx.run.current_set_number, ctx.run.config.planned_sets):
        return "feedback"
    return "announce"
