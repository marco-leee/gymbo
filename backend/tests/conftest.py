"""Ensure repo ``src/`` is on sys.path for imports like ``analysis_pipeline``."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

if not os.environ.get("RUN_ML_STACK_TESTS"):
    # Importing ``yolo_inference_runtime`` pulls the Ultralytics/YOLO stack (~torch).
    # Opt-in so default ``pytest`` stays fast and skips ML-heavy collection.
    collect_ignore = ["test_yolo_inference_runtime.py"]
