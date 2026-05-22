"""ffprobe helpers for downloaded video validation."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


def probe_video_duration_sec(path: Path) -> float | None:
    """Return container duration in seconds via ffprobe, or None if unavailable."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        log.debug("ffprobe not on PATH; skipping duration probe for %s", path)
        return None

    path = path.resolve()
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    log.debug("ffprobe command: %s", " ".join(cmd))
    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        log.error("ffprobe failed for %s: %s", path, stderr[-500:])
        return None

    try:
        payload = json.loads(proc.stdout or "{}")
        raw = payload.get("format", {}).get("duration")
        return float(raw) if raw is not None else None
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        log.error("ffprobe JSON parse failed for %s: %s", path, e)
        return None
