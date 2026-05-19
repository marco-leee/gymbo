"""Per-frame artifacts returned from perception + optional legacy JSON export."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from models.overall_results import OverallResult
from pipeline.schemas import FramePerceptionRecord


@dataclass
class FramePerceptionState:
    """Per-frame perception output plus optional legacy OverallResult."""

    overall_result: OverallResult | None
    crop_xyxy: tuple[int, int, int, int] | None
    mask_u8_crop: np.ndarray | None
    cropped_frame: np.ndarray | None
    perception_record: FramePerceptionRecord
