"""Thin CLI for offline video dev — delegates to agent graph factory."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from agent.app.event_publisher import RunEventPublisher
from agent.app.run_context import RunContext
from agent.domain.models import CoachedExerciseRun, ExerciseRunConfig
from agent.graphs.factory import build_dependencies
from agent.graphs.session import SessionRunner
from agent.infra.run_repository import RunRepository


def _env_path() -> Path:
    return Path(__file__).resolve().parent / ".env"


async def _run_video(*, dry_run: bool) -> None:
    deps = build_dependencies(dry_run=dry_run)
    run = CoachedExerciseRun(
        id="cli-run",
        gymbo_session_id="cli-session",
        session_exercise_id="cli-exercise",
        trainer_id="cli",
        client_id="cli",
        config=ExerciseRunConfig(planned_sets=1, target_reps_per_set=3),
    )
    ctx = RunContext(run=run, dry_run=dry_run)

    async def noop_emit(sid, event, data):
        print(f"[{event}]", data.get("phase") or data.get("status") or "")

    publisher = RunEventPublisher(noop_emit)
    repo = RunRepository()
    runner = SessionRunner(ctx, deps, publisher, repo)
    await runner.run()


def main(argv: list[str] | None = None) -> int:
    load_dotenv(_env_path())
    parser = argparse.ArgumentParser(description="Trainer agent offline CLI")
    parser.add_argument("--video", type=str, default=os.getenv("VIDEO_PATH"), help="Path to video (legacy flag)")
    parser.add_argument("--dry-run", action="store_true", help="Skip API calls")
    args = parser.parse_args(argv)

    if args.video:
        print(
            "Note: --video file ingest moved to live WS frame loop. "
            "Use trainer_fastapi_main.py + /trainer for live frames, or --dry-run for graph smoke.",
            file=sys.stderr,
        )

    asyncio.run(_run_video(dry_run=args.dry_run))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
