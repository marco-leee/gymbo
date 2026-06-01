"""Tests for ffprobe stream parsing and display dimension helpers."""

from __future__ import annotations

from utils.video_probe import (
    VideoStreamProbe,
    _parse_stream_probe,
    display_dimensions,
    infer_rotation_from_expected_display,
    normalize_rotation_deg,
    probe_video_stream,
)


def test_normalize_rotation_deg_values() -> None:
    assert normalize_rotation_deg(None) == 0
    assert normalize_rotation_deg("90") == 90
    assert normalize_rotation_deg(-90) == 270
    assert normalize_rotation_deg(180) == 180
    assert normalize_rotation_deg(360) == 0
    assert normalize_rotation_deg(450) == 90


def test_display_dimensions_swaps_for_90_and_270() -> None:
    assert display_dimensions(1920, 1080, 0) == (1920, 1080)
    assert display_dimensions(1920, 1080, 90) == (1080, 1920)
    assert display_dimensions(1920, 1080, 180) == (1920, 1080)
    assert display_dimensions(1920, 1080, 270) == (1080, 1920)


def test_infer_rotation_from_expected_display() -> None:
    assert infer_rotation_from_expected_display(1920, 1080, 1920, 1080) == 0
    assert infer_rotation_from_expected_display(1920, 1080, 1080, 1920) == 90
    assert infer_rotation_from_expected_display(1920, 1080, 1280, 720) is None


def test_parse_stream_probe_rotate_tag() -> None:
    probe = _parse_stream_probe(
        {
            "width": 1920,
            "height": 1080,
            "tags": {"rotate": "90"},
        }
    )
    assert probe == VideoStreamProbe(
        coded_width=1920, coded_height=1080, rotation_deg=90
    )


def test_parse_stream_probe_side_data_rotation() -> None:
    probe = _parse_stream_probe(
        {
            "width": 1920,
            "height": 1080,
            "side_data_list": [{"rotation": -90}],
        }
    )
    assert probe == VideoStreamProbe(
        coded_width=1920, coded_height=1080, rotation_deg=270
    )


def test_parse_stream_probe_side_data_overrides_missing_tag() -> None:
    probe = _parse_stream_probe(
        {
            "width": 1280,
            "height": 720,
            "tags": {"rotate": "0"},
            "side_data_list": [{"rotation": 180}],
        }
    )
    assert probe == VideoStreamProbe(
        coded_width=1280, coded_height=720, rotation_deg=180
    )


def test_parse_stream_probe_no_rotation() -> None:
    probe = _parse_stream_probe({"width": 640, "height": 480})
    assert probe == VideoStreamProbe(
        coded_width=640, coded_height=480, rotation_deg=0
    )


def test_probe_video_stream_parses_json(monkeypatch) -> None:
    import utils.video_probe as vp

    payload = (
        '{"streams":[{"width":1920,"height":1080,"tags":{"rotate":"90"}}]}'
    )

    class FakeProc:
        stdout = payload
        stderr = ""

    monkeypatch.setattr(vp.shutil, "which", lambda _name: "/usr/bin/ffprobe")
    monkeypatch.setattr(vp.subprocess, "run", lambda *_a, **_k: FakeProc())

    probe = probe_video_stream(vp.Path("/tmp/fake.mp4"))
    assert probe == VideoStreamProbe(
        coded_width=1920, coded_height=1080, rotation_deg=90
    )
