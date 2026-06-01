"""Canonical KIP palette for video overlay (OpenCV BGR).

Keep in sync with app/src/lib/pose/kip-colors.ts (light-theme --chart-* tokens).
"""

from __future__ import annotations

KIP_COLORS_BGR: dict[str, tuple[int, int, int]] = {
    "INSIDE_KNEE": (0, 73, 245),
    "OUTSIDE_HIP": (137, 150, 0),
    "HIP_HINGE": (100, 78, 16),
    "FRONT_KNEE": (0, 185, 255),
}

KIP_LABELS: dict[str, str] = {
    "INSIDE_KNEE": "Inside Knee",
    "OUTSIDE_HIP": "Outside Hip",
    "HIP_HINGE": "Hip Hinge",
    "FRONT_KNEE": "Front Knee",
}
