"""Thin CLI for offline graph dev — delegates to compiled LangGraph session."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

import cv2
import numpy as np
from dotenv import load_dotenv

from agent.app.event_publisher import RunEventPublisher
from agent.app.run_context import RunContext
from agent.domain.models import CoachedExerciseRun, ExerciseRunConfig, IncomingFrame
from agent.graphs.factory import (
    build_dependencies,
    build_session_graph,
    build_voice_graph,
)
from agent.graphs.runtime import build_graph_config
from agent.graphs.state import build_initial_state
from agent.infra.run_repository import RunRepository

logger = logging.getLogger(__name__)


def _env_path() -> Path:
    return Path(__file__).resolve().parent / ".env"


def _minimal_jpeg() -> bytes:
    img = np.zeros((64, 64, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    if not ok:
        raise RuntimeError("Failed to encode test JPEG")
    return buf.tobytes()


async def _run_graph(*, dry_run: bool) -> None:
    deps = build_dependencies(dry_run=dry_run)
    run = CoachedExerciseRun(
        id="cli-run",
        gymbo_session_id="cli-session",
        session_exercise_id="cli-exercise",
        trainer_id="cli",
        client_id="cli",
        config=ExerciseRunConfig(planned_sets=1, target_reps_per_set=2, rest_needed=False),
    )
    ctx = RunContext(run=run, dry_run=dry_run)
    ctx.frame_buffer.push(
        IncomingFrame(seq=1, timestamp_sec=0.0, jpeg_bytes=_minimal_jpeg(), width=64, height=64)
    )

    async def noop_emit(sid, event, data):
        print(f"[{event}]", data.get("phase") or data.get("status") or "")

    publisher = RunEventPublisher(noop_emit)
    repo = RunRepository()
    config = build_graph_config(ctx=ctx, deps=deps, publisher=publisher, repository=repo)
    voice_graph = build_voice_graph()
    await ctx.start_voice_graph_consumer(voice_graph, config)

    graph = build_session_graph()
    initial = build_initial_state(run)
    await graph.ainvoke(initial, config)
    logger.info("Session graph complete: status=%s", run.status.value)


def main(argv: list[str] | None = None) -> int:
    load_dotenv(_env_path())
    parser = argparse.ArgumentParser(description="Trainer agent offline CLI")
    parser.add_argument("--video", type=str, default=os.getenv("VIDEO_PATH"), help="Legacy video path flag")
    parser.add_argument("--dry-run", action="store_true", help="Skip API calls")
    args = parser.parse_args(argv)

    if args.video:
        print(
            "Note: --video file ingest moved to live WS frame loop. "
            "Use trainer_fastapi_main.py + /trainer for live frames, or --dry-run for graph smoke.",
            file=sys.stderr,
        )

    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run_graph(dry_run=args.dry_run))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
