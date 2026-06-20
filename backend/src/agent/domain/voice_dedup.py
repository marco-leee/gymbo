"""Voice-out deduplication policy."""

from __future__ import annotations

from agent.domain.models import VoiceOutDecision, VoiceOutEvent, VoiceRepeatState


def _normalize(issue: str) -> str:
    return issue.strip().lower()


def evaluate_dedup(
    event: VoiceOutEvent,
    repeat_state: VoiceRepeatState,
) -> tuple[VoiceOutDecision, VoiceRepeatState]:
    """Decide whether to speak, skip, or increment repeat count."""
    focus = _normalize(event.focus_issue)
    threshold = repeat_state.threshold
    last = repeat_state.last_voiced_issue

    if last is None or _normalize(last) != focus:
        repeat_state.last_voiced_issue = event.focus_issue
        repeat_state.repeat_count = 0
        return VoiceOutDecision.SPEAK, repeat_state

    repeat_state.repeat_count += 1
    if repeat_state.repeat_count >= threshold:
        repeat_state.repeat_count = 0
        return VoiceOutDecision.SPEAK, repeat_state

    return VoiceOutDecision.INCREMENT, repeat_state
