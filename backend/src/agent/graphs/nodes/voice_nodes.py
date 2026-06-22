"""VoiceOut subgraph LangGraph nodes."""

from __future__ import annotations

import logging

from langchain_core.runnables import RunnableConfig

from agent.domain.models import CoachingEventRecord, VoiceOutDecision, VoiceOutEvent
from agent.domain.voice_dedup import evaluate_dedup
from agent.graphs.runtime import get_deps, get_publisher, get_repository, get_run_context
from agent.graphs.state import TrainerGraphState

logger = logging.getLogger(__name__)


async def dedup_check(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    raw = state.get("voice_event") or {}
    event = VoiceOutEvent.model_validate(raw)

    decision, repeat_state = evaluate_dedup(event, ctx.voice_repeat_state)
    ctx.voice_repeat_state = repeat_state

    return {
        **state,
        "voice_decision": decision.value,
        "voice_event_model": event.model_dump(mode="json"),
        "voice_repeat_count": repeat_state.repeat_count,
    }


async def generate_cue(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    deps = get_deps(config)
    event = VoiceOutEvent.model_validate(state.get("voice_event_model") or state.get("voice_event"))

    message = deps.cue_generator.generate(
        event=event,
        state=ctx.run.merged_observation_state,
    )
    return {**state, "voice_message": message, "voice_event_model": event.model_dump(mode="json")}


async def log_coaching(state: TrainerGraphState, config: RunnableConfig) -> TrainerGraphState:
    ctx = get_run_context(config)
    publisher = get_publisher(config)
    repository = get_repository(config)
    event = VoiceOutEvent.model_validate(state.get("voice_event_model") or state.get("voice_event"))
    message = state.get("voice_message", "")
    repeat_count = state.get("voice_repeat_count", 0)
    decision = state.get("voice_decision")

    trigger = (
        "repeat_threshold"
        if decision == VoiceOutDecision.SPEAK.value and repeat_count == 0
        else "new_issue"
    )

    record = CoachingEventRecord(
        run_id=event.run_id,
        message=message,
        focus_issue=event.focus_issue,
        trigger_reason=event.reason,
        severity=event.severity,
        set_number=event.set_number,
        dedup_repeat_count=repeat_count or None,
    )
    repository.save_coaching_event(record)
    ctx.recent_coaching.append(
        {
            "message": message,
            "focus_issue": event.focus_issue,
            "timestamp": event.timestamp.isoformat(),
        }
    )

    await publisher.publish_voice_cue(
        ctx,
        cue_id=record.id,
        message=message,
        focus_issue=event.focus_issue,
        severity=event.severity,
        trigger=trigger,
        repeat_count=repeat_count,
    )
    return state


def route_after_dedup(state: TrainerGraphState) -> str:
    if state.get("voice_decision") == VoiceOutDecision.INCREMENT.value:
        return "skip"
    return "speak"
