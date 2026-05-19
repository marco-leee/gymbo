"""Remux pipeline MP4 output for browser inline playback (H.264 + faststart)."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


def remux_mp4_for_browser_playback(source: Path, destination: Path) -> Path:
    """
    Re-encode OpenCV ``mp4v`` output to H.264 with the moov atom at the file start.

    Required for ``<video src>`` range streaming; full-file download may work without this.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is not installed or not on PATH")

    source = source.resolve()
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(source),
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-movflags",
        "+faststart",
        "-an",
        str(destination),
    ]
    log.info("Remuxing %s -> %s for web playback", source, destination)
    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        raise RuntimeError(
            f"ffmpeg remux failed (exit {e.returncode}): {stderr[-2000:]}"
        ) from e

    if not destination.is_file() or destination.stat().st_size == 0:
        raise RuntimeError(f"ffmpeg remux produced empty output: {destination}")

    return destination
