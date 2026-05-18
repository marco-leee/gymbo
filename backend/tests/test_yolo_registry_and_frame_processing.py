"""Tests for stream registry and frame parse/decode helpers."""

from __future__ import annotations

from models.yolo_ws_protocol import YoloRegisterStream
from yolo_frame_processing import frame_bytes_to_bgr, parse_yolo_frame_event
from yolo_stream_registry import StreamRegistry


def test_registry_register_unregister_and_disconnect_session():
    r = StreamRegistry(max_streams=10)
    ok, err = r.register(
        "sess-a", "stream-1", camera_view="RIGHT", exercise_type="SQUAT"
    )
    assert ok and err is None
    assert r.is_owned_by("stream-1", "sess-a")

    ok2, err2 = r.register(
        "sess-b", "stream-1", camera_view="RIGHT", exercise_type="SQUAT"
    )
    assert not ok2 and err2

    assert r.unregister("sess-a", "stream-1")
    assert not r.is_owned_by("stream-1", "sess-a")

    r.register("sess-x", "s1", camera_view="LEFT", exercise_type="LUNGE")
    r.register("sess-x", "s2", camera_view="LEFT", exercise_type="LUNGE")
    dropped = r.disconnect_session("sess-x")
    assert set(dropped) == {"s1", "s2"}
    assert not r.is_owned_by("s1", "sess-x")


def test_registry_stream_count():
    r = StreamRegistry(max_streams=10)
    assert r.stream_count() == 0
    r.register("a", "x", camera_view="RIGHT", exercise_type="SQUAT")
    assert r.stream_count() == 1
    r.unregister("a", "x")
    assert r.stream_count() == 0


def test_registry_capacity():
    r = StreamRegistry(max_streams=1)
    assert r.register("a", "one", camera_view="RIGHT", exercise_type="SQUAT")[0]
    ok, err = r.register("a", "two", camera_view="RIGHT", exercise_type="SQUAT")
    assert not ok and err == "server stream capacity reached"


def test_parse_yolo_frame_event():
    incoming = parse_yolo_frame_event(
        {
            "stream_id": "abc",
            "seq": 0,
            "dimensions": {"width": 2, "height": 2, "format": "rgb"},
            "frame": b"\x00" * 12,
        }
    )
    assert incoming.meta.stream_id == "abc"
    assert incoming.meta.seq == 0
    assert len(incoming.frame) == 12


def test_parse_yolo_frame_memoryview():
    mv = memoryview(b"\x01\x02\x03\x04")
    incoming = parse_yolo_frame_event(
        {
            "stream_id": "x",
            "seq": 1,
            "dimensions": {"width": 2, "height": 2, "format": "rgb"},
            "frame": mv,
        }
    )
    assert incoming.frame == bytes(mv)


def test_frame_rgb_decode():
    buf = bytes(range(2 * 2 * 3))
    img = frame_bytes_to_bgr(buf, 2, 2, "rgb")
    assert img.shape == (2, 2, 3)


def test_yolo_register_stream_model():
    m = YoloRegisterStream.model_validate({"stream_id": "z"})
    assert m.camera_view is None
