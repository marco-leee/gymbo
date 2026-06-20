"""Dry-run VLM adapter using fixture JSON from tmp/vlm-state/processed/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from agent.domain.models import FrameSnapshot, VLMFrameResult
from agent.pipeline.vlm.openrouter_adapter import VLMContextAdapter

REP_PHASES = ("setup", "descending", "bottom", "ascending", "lockout", "rest")
FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tmp" / "vlm-state" / "processed"


class DryRunVLMAdapter:
    def __init__(self, *, fixture_dir: Path | None = None) -> None:
        self._fixture_dir = fixture_dir or FIXTURE_DIR
        self._fixture_files = sorted(self._fixture_dir.glob("*_vlm_analyze.json"))
        self._index = 0

    def analyze(
        self,
        *,
        frames: Sequence[FrameSnapshot],
        context: VLMContextAdapter,
    ) -> VLMFrameResult:
        current = frames[-1]
        if self._fixture_files:
            path = self._fixture_files[self._index % len(self._fixture_files)]
            self._index += 1
            data = json.loads(path.read_text(encoding="utf-8"))
            latest = data.get("latest_vlm") or {}
            if latest:
                latest["frame_index"] = current.frame_index
                latest["timestamp_sec"] = current.timestamp_sec
                return VLMFrameResult.model_validate(latest)

        phase = REP_PHASES[current.frame_index % len(REP_PHASES)]
        voice = current.frame_index > 0 and current.frame_index % 5 == 0
        return VLMFrameResult(
            frame_index=current.frame_index,
            timestamp_sec=current.timestamp_sec,
            in_rep=phase not in ("setup", "rest"),
            rep_phase=phase,
            observations=[f"Frame {current.frame_index}: athlete in {phase} phase"],
            issues=(
                ["slight forward lean"]
                if current.frame_index > 0 and current.frame_index % 7 == 0
                else []
            ),
            severity="moderate" if current.frame_index > 0 and current.frame_index % 7 == 0 else "none",
            confidence=0.85,
            rep_completed=phase == "lockout",
            action="voice_out" if voice else "observe",
            voice_reason="Repeated forward lean detected" if voice else None,
            focus_issue="Keep chest up and core braced" if voice else None,
        )
