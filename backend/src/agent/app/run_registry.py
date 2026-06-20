"""In-memory registry of active coached exercise runs."""

from __future__ import annotations

from agent.app.run_context import RunContext


class RunRegistry:
    def __init__(self) -> None:
        self._runs: dict[str, RunContext] = {}

    def register(self, ctx: RunContext) -> None:
        self._runs[ctx.run.id] = ctx

    def get(self, run_id: str) -> RunContext | None:
        return self._runs.get(run_id)

    def remove(self, run_id: str) -> RunContext | None:
        return self._runs.pop(run_id, None)

    def by_sid(self, sid: str) -> RunContext | None:
        for ctx in self._runs.values():
            if ctx.sid == sid:
                return ctx
        return None

    def count(self) -> int:
        return len(self._runs)
