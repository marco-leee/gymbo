"""Tests for KIP angle overlays on processed video frames."""

from __future__ import annotations

import numpy as np
import pytest

from pipeline.kip_colors import KIP_COLORS_BGR
from pipeline.overlays import draw_kip_angle, render_kip_angles


def test_kip_colors_bgr_keys_match_frontend_kips() -> None:
    assert set(KIP_COLORS_BGR) == {
        "INSIDE_KNEE",
        "OUTSIDE_HIP",
        "HIP_HINGE",
        "FRONT_KNEE",
    }
    for b, g, r in KIP_COLORS_BGR.values():
        assert 0 <= b <= 255
        assert 0 <= g <= 255
        assert 0 <= r <= 255


def test_kip_colors_hex_bgr_conversion() -> None:
    """BGR tuples must match app/src/lib/pose/kip-colors.ts hex values."""
    expected = {
        "INSIDE_KNEE": "#F54900",
        "OUTSIDE_HIP": "#009689",
        "HIP_HINGE": "#104E64",
        "FRONT_KNEE": "#FFB900",
    }
    for kip, hex_color in expected.items():
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        assert KIP_COLORS_BGR[kip] == (b, g, r)


def test_draw_kip_angle_modifies_image() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    before = frame.copy()
    draw_kip_angle(
        frame,
        center=(200, 200),
        angle=95,
        rotation_angle=45,
        color_bgr=KIP_COLORS_BGR["INSIDE_KNEE"],
        label="Inside Knee",
    )
    assert not np.array_equal(frame, before)


def test_render_kip_angles_applies_crop_offset() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    kips = {
        "INSIDE_KNEE": {
            "idx_to_coordinates": {
                "23": [10.0, 20.0],
                "25": [50.0, 60.0],
                "27": [90.0, 80.0],
            },
            "angle": 100,
            "rotation_angle": 30,
            "comment": "GOOD",
            "colour": [0, 255, 0],
        }
    }
    crop_xy = (100, 50, 400, 450)
    out = render_kip_angles(frame, kips, crop_xy)
    assert out is frame
    assert np.any(out != 0)


def test_render_kip_angles_skips_unknown_kip() -> None:
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    kips = {
        "UNKNOWN_KIP": {
            "idx_to_coordinates": {
                "0": [10.0, 20.0],
                "1": [50.0, 60.0],
                "2": [90.0, 80.0],
            },
            "angle": 100,
            "rotation_angle": 30,
        }
    }
    out = render_kip_angles(frame, kips, None)
    assert np.all(out == 0)


def test_render_kip_angles_handles_empty_kips() -> None:
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    out = render_kip_angles(frame, None, None)
    assert out is frame
    assert np.all(out == 0)


def test_render_kip_angles_skips_invalid_vertex_count() -> None:
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    kips = {
        "INSIDE_KNEE": {
            "idx_to_coordinates": {"25": [50.0, 60.0]},
            "angle": 100,
            "rotation_angle": 30,
        }
    }
    out = render_kip_angles(frame, kips, None)
    assert np.all(out == 0)
