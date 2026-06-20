"""Unit tests for voice dedup threshold behavior."""

from __future__ import annotations

from agent.domain.models import VoiceOutEvent, VoiceRepeatState
from agent.domain.voice_dedup import evaluate_dedup, VoiceOutDecision


def _event(issue: str = "forward lean") -> VoiceOutEvent:
    return VoiceOutEvent(
        run_id="run-1",
        set_number=1,
        focus_issue=issue,
        reason="test",
    )


def test_new_issue_speaks_immediately():
    state = VoiceRepeatState(threshold=3)
    decision, new_state = evaluate_dedup(_event(), state)
    assert decision == VoiceOutDecision.SPEAK
    assert new_state.last_voiced_issue == "forward lean"


def test_similar_below_threshold_increments():
    state = VoiceRepeatState(threshold=3, last_voiced_issue="forward lean", repeat_count=0)
    decision, new_state = evaluate_dedup(_event(), state)
    assert decision == VoiceOutDecision.INCREMENT
    assert new_state.repeat_count == 1


def test_similar_at_threshold_speaks():
    state = VoiceRepeatState(threshold=3, last_voiced_issue="forward lean", repeat_count=2)
    decision, new_state = evaluate_dedup(_event(), state)
    assert decision == VoiceOutDecision.SPEAK
    assert new_state.repeat_count == 0
