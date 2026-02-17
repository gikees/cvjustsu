"""MediaPipe Hands wrapper for hand landmark detection.

Uses the MediaPipe Tasks API (HandLandmarker) in VIDEO mode.
"""

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

import config

# MediaPipe Tasks imports
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# Hand connections for drawing (21 landmarks)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),       # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),       # index
    (5, 9), (9, 10), (10, 11), (11, 12),   # middle
    (9, 13), (13, 14), (14, 15), (15, 16), # ring
    (13, 17), (17, 18), (18, 19), (19, 20),# pinky
    (0, 17),                                # palm
]

MODEL_PATH = config.ASSETS_DIR / "hand_landmarker.task"


@dataclass
class HandResult:
    """Result from processing a single frame."""
    landmarks: list[list[tuple[float, float, float]]] = field(default_factory=list)
    handedness: list[str] = field(default_factory=list)
    num_hands: int = 0
    annotated_frame: np.ndarray | None = None


class HandTracker:
    """Wraps MediaPipe HandLandmarker (Tasks API) for detection and drawing."""

    def __init__(self) -> None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Hand landmarker model not found at {MODEL_PATH}. "
                "Download from: https://storage.googleapis.com/mediapipe-models/"
                "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
            )

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=VisionRunningMode.VIDEO,
            num_hands=config.MP_MAX_HANDS,
            min_hand_detection_confidence=config.MP_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MP_MIN_TRACKING_CONFIDENCE,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        self._frame_ts = 0

    def process(self, frame: np.ndarray, draw: bool = True) -> HandResult:
        """Process a BGR frame and return hand landmarks.

        Args:
            frame: BGR image from OpenCV.
            draw: Whether to draw landmarks on the frame.

        Returns:
            HandResult with landmarks normalized [0,1] and optional annotated frame.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        self._frame_ts += 33  # ~30fps interval in ms
        results = self._landmarker.detect_for_video(mp_image, self._frame_ts)

        hand_result = HandResult()

        if results.hand_landmarks:
            for hand_lms, handedness_info in zip(
                results.hand_landmarks,
                results.handedness,
            ):
                # Extract (x, y, z) for each of 21 landmarks
                lms = [(lm.x, lm.y, lm.z) for lm in hand_lms]
                hand_result.landmarks.append(lms)

                # Handedness label (Left/Right)
                label = handedness_info[0].category_name
                hand_result.handedness.append(label)

                if draw:
                    self._draw_landmarks(frame, hand_lms)

        hand_result.num_hands = len(hand_result.landmarks)
        if draw:
            hand_result.annotated_frame = frame

        return hand_result

    def _draw_landmarks(self, frame: np.ndarray, landmarks) -> None:
        """Draw hand landmarks and connections on the frame."""
        h, w = frame.shape[:2]
        points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

        # Draw connections
        for start, end in HAND_CONNECTIONS:
            cv2.line(frame, points[start], points[end], (0, 255, 0), 2)

        # Draw landmark points
        for pt in points:
            cv2.circle(frame, pt, 4, (0, 0, 255), -1)

    def close(self) -> None:
        self._landmarker.close()
