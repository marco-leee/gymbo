"""Set subgraph LangGraph nodes."""

from __future__ import annotations

import asyncio
import logging

from langchain_core.runnables import RunnableConfig

from agent.domain.models import RunPhase, RunStatus, VoiceOutEvent
from agent.domain.observation_merger import merge_observation, reset_set_reps
from agent.domain.rep_completion import is_set_complete
from agent.domain.safety_evaluator import evaluate_set_safety
from agent.graphs.runtime import get_deps, get_publisher, get_run_context
from agent.graphs.state import TrainerGraphState, apply_status_phase
from agent.pipeline.preprocessor import decode_incoming, incoming_to_snapshot
from agent.pipeline.vlm.openrouter_adapter import VLMContextAdapter

logger = logging.getLogger(__name__)

CYCLE_INTERVAL_SEC = 1.0


async def begin_set(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    publisher = get_publisher(config)
    reset_set_reps(ctx.run.merged_observation_state)
    apply_status_phase(ctx.run, RunStatus.ACTIVE, RunPhase.SET_IN_PROGRESS)
    await publisher.publish_state(ctx)
    return {**state, "frame_index": state.get("frame_index", 0), "set_complete": False, "set_emergency": False}


def _should_end_set(state: TrainerGraphState, config: RunnableConfig) -> bool:
    ctx = get_run_context(config)
    if ctx.paused or ctx.end_requested:
        return True
    if ctx.end_set_requested:
        ctx.end_set_requested = False
        return True
    return is_set_complete(
        ctx.run.merged_observation_state.completed_reps,
        ctx.run.config.target_reps_per_set,
    )


async def grab_frame(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    if _should_end_set(state, config):
        return {
            **state,
            "set_complete": True,
            "paused": ctx.paused,
            "end_requested": ctx.end_requested,
        }

    if ctx.frame_buffer.latest() is None:
        logger.debug("Empty frame buffer — skipping cycle")
        return {**state, "has_frame": False}

    return {**state, "has_frame": True}


async def preprocess_pose(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    if not state.get("has_frame"):
        return state

    ctx = get_run_context(config)
    deps = get_deps(config)
    frame = ctx.frame_buffer.latest()
    if frame is None:
        return {**state, "has_frame": False}

    try:
        bgr = decode_incoming(frame)
        deps.pose.estimate(bgr)
    except Exception as exc:
        logger.warning("Pose/preprocess failed: %s", exc)
        return {**state, "has_frame": False, "vlm_skipped": True}

    return {**state, "vlm_skipped": False}


async def vlm_analyze(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    if not state.get("has_frame") or state.get("vlm_skipped"):
        return {**state, "vlm_action": "observe"}

    ctx = get_run_context(config)
    deps = get_deps(config)
    frame = ctx.frame_buffer.latest()
    if frame is None:
        return {**state, "vlm_action": "observe"}

    frame_index = state.get("frame_index", 0)
    snapshot = incoming_to_snapshot(frame, frame_index)
    prior = ctx.frame_history.prior_frames()
    all_frames = prior + [snapshot]

    vlm_ctx = VLMContextAdapter(
        merged_state=ctx.run.merged_observation_state,
        set_number=ctx.run.current_set_number,
        exercise_type=ctx.run.exercise_type,
        recent_coaching=ctx.recent_coaching,
    )

    try:
        vlm = deps.vlm.analyze(frames=all_frames, context=vlm_ctx)
    except Exception as exc:
        logger.warning("VLM analyze failed: %s", exc)
        return {**state, "vlm_action": "observe"}

    ctx.frame_history.append(snapshot)
    merge_observation(ctx.run.merged_observation_state, vlm)

    return {
        **state,
        "frame_index": frame_index + 1,
        "vlm_action": vlm.action,
        "vlm_focus_issue": vlm.focus_issue,
        "vlm_voice_reason": vlm.voice_reason,
        "vlm_severity": vlm.severity,
        "vlm_issues": vlm.issues,
        "frame_seq": frame.seq,
    }


async def observe_update(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    publisher = get_publisher(config)
    await publisher.publish_state(ctx)
    return state


async def emit_voice(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    focus = state.get("vlm_focus_issue")
    if not focus:
        return state

    event = VoiceOutEvent(
        run_id=ctx.run.id,
        set_number=ctx.run.current_set_number,
        focus_issue=focus,
        reason=state.get("vlm_voice_reason") or "Form cue needed",
        severity=state.get("vlm_severity") or "moderate",
        frame_seq=state.get("frame_seq", 0),
    )
    await ctx.enqueue_voice(event)
    return state


async def safety_check(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    if not state.get("has_frame") or state.get("vlm_skipped"):
        return state

    ctx = get_run_context(config)
    publisher = get_publisher(config)
    from agent.domain.models import VLMFrameResult

    vlm = VLMFrameResult(
        severity=state.get("vlm_severity") or "none",  # type: ignore[arg-type]
        issues=state.get("vlm_issues") or [],
    )
    safety = evaluate_set_safety(vlm)
    if not safety.safe:
        ctx.paused = True
        apply_status_phase(ctx.run, RunStatus.PAUSED, RunPhase.SET_IN_PROGRESS)
        await publisher.publish_emergency(
            ctx,
            source=safety.source,
            severity="critical",
            description=safety.description,
        )
        return {**state, "set_emergency": True, "paused": True}

    if _should_end_set(state, config):
        return {**state, "set_complete": True}

    await publisher.publish_state(ctx)
    return state


async def wait_cycle(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    interval = 0.05 if ctx.dry_run else CYCLE_INTERVAL_SEC
    await asyncio.sleep(interval)
    return state


def route_after_grab(state: TrainerGraphState) -> str:
    if state.get("set_complete") or state.get("set_emergency"):
        return "done"
    if state.get("paused") or state.get("end_requested"):
        return "done"
    if not state.get("has_frame"):
        return "wait"
    return "preprocess"


def route_after_vlm(state: TrainerGraphState) -> str:
    if not state.get("has_frame") or state.get("vlm_skipped"):
        return "safety"
    if state.get("vlm_action") == "voice_out" and state.get("vlm_focus_issue"):
        return "voice"
    return "observe"


def route_after_safety(state: TrainerGraphState, config: RunnableConfig) -> str:
    if state.get("set_emergency") or state.get("set_complete"):
        return "done"
    ctx = get_run_context(config)
    if ctx.paused or ctx.end_requested:
        return "done"
    return "wait"
