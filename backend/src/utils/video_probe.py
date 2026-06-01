"""ffprobe helpers for downloaded video validation."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class VideoStreamProbe:
    coded_width: int
    coded_height: int
    rotation_deg: int  # normalized to 0, 90, 180, 270


def normalize_rotation_deg(raw: int | float | str | None) -> int:
    """Normalize rotation metadata to 0, 90, 180, or 270 degrees."""
    if raw is None:
        return 0
    try:
        deg = int(float(raw))
    except (TypeError, ValueError):
        return 0
    deg = deg % 360
    if deg < 0:
        deg += 360
    if deg not in (0, 90, 180, 270):
        log.warning("Unsupported rotation %s; treating as 0", raw)
        return 0
    return deg


def display_dimensions(
    coded_w: int, coded_h: int, rotation_deg: int
) -> tuple[int, int]:
    """Return browser-visible width and height after applying rotation."""
    if rotation_deg in (90, 270):
        return coded_h, coded_w
    return coded_w, coded_h


def infer_rotation_from_expected_display(
    coded_w: int,
    coded_h: int,
    expected_w: int,
    expected_h: int,
) -> int | None:
    """
    Infer rotation when ffprobe reports 0 but upload metadata has display dimensions.

    Returns 90 when coded and expected dimensions are swapped (cannot distinguish
    90° from 270° without container metadata).
    """
    if coded_w == expected_w and coded_h == expected_h:
        return 0
    if coded_w == expected_h and coded_h == expected_w:
        return 90
    return None


def resolve_rotation_deg(
    *,
    coded_w: int,
    coded_h: int,
    probe_deg: int,
    expected_display_size: tuple[int, int] | None = None,
    frame_size: tuple[int, int] | None = None,
) -> int:
    """
    Decide rotation to apply to OpenCV-decoded frames.

    Browser ``videoWidth``/``videoHeight`` (``expected_display_size``) wins when
    supplied. ffprobe rotation can be stale, or frames may already be upright
    because the OpenCV/FFmpeg decoder applied display metadata.
    """
    coded = (coded_w, coded_h)

    if expected_display_size is not None:
        expected = expected_display_size
        if expected == coded:
            return 0
        if expected == (coded_h, coded_w):
            if probe_deg in (90, 270):
                if display_dimensions(coded_w, coded_h, probe_deg) == expected:
                    return probe_deg
            for deg in (90, 270):
                if display_dimensions(coded_w, coded_h, deg) == expected:
                    return deg
            return 90
        if frame_size == expected:
            return 0

    if frame_size is not None and probe_deg != 0:
        if frame_size == display_dimensions(coded_w, coded_h, probe_deg):
            return 0

    # Stale ffprobe on storage that is already upright portrait.
    if (
        probe_deg in (90, 270)
        and coded_h > coded_w
        and frame_size == coded
    ):
        probed = display_dimensions(coded_w, coded_h, probe_deg)
        if probed[0] > probed[1]:
            return 0

    if frame_size == coded and probe_deg != 0:
        return probe_deg

    if probe_deg in (90, 270) and coded_h > coded_w:
        probed = display_dimensions(coded_w, coded_h, probe_deg)
        if probed[0] > probed[1]:
            return 0

    return probe_deg


def _parse_stream_probe(stream: dict) -> VideoStreamProbe | None:
    width = stream.get("width")
    height = stream.get("height")
    if width is None or height is None:
        return None

    rotation_deg = 0
    for side in stream.get("side_data_list") or []:
        if "rotation" in side:
            rotation_deg = normalize_rotation_deg(side["rotation"])
            break

    if rotation_deg == 0:
        tags = stream.get("tags") or {}
        rotate_tag = tags.get("rotate")
        if rotate_tag is not None:
            rotation_deg = normalize_rotation_deg(rotate_tag)

    return VideoStreamProbe(
        coded_width=int(width),
        coded_height=int(height),
        rotation_deg=rotation_deg,
    )


def probe_video_stream(path: Path) -> VideoStreamProbe | None:
    """Return coded dimensions and rotation via ffprobe, or None if unavailable."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        log.debug("ffprobe not on PATH; skipping stream probe for %s", path)
        return None

    path = path.resolve()
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height:stream_tags=rotate:stream_side_data=rotation",
        "-of",
        "json",
        str(path),
    ]
    log.debug("ffprobe command: %s", " ".join(cmd))
    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        log.error("ffprobe stream probe failed for %s: %s", path, stderr[-500:])
        return None

    try:
        payload = json.loads(proc.stdout or "{}")
        streams = payload.get("streams") or []
        if not streams:
            return None
        return _parse_stream_probe(streams[0])
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        log.error("ffprobe stream JSON parse failed for %s: %s", path, e)
        return None


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
