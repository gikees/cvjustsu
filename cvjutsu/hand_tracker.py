"""MediaPipe Hands wrapper for hand landmark detection."""

from dataclasses import dataclass, field

import cv2
import mediapipe as mp
import numpy as np

import config


@dataclass
class HandResult:
    """Result from processing a single frame."""
    landmarks: list[list[tuple[float, float, float]]] = field(default_factory=list)
    handedness: list[str] = field(default_factory=list)
    num_hands: int = 0
    annotated_frame: np.ndarray | None = None


class HandTracker:
    """Wraps MediaPipe Hands for detection and drawing."""

    def __init__(self) -> None:
        self._mp_hands = mp.solutions.hands
        self._mp_draw = mp.solutions.drawing_utils
        self._mp_styles = mp.solutions.drawing_styles
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=config.MP_MAX_HANDS,
            min_detection_confidence=config.MP_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MP_MIN_TRACKING_CONFIDENCE,
        )

    def process(self, frame: np.ndarray, draw: bool = True) -> HandResult:
        """Process a BGR frame and return hand landmarks.

        Args:
            frame: BGR image from OpenCV.
            draw: Whether to draw landmarks on the frame.

        Returns:
            HandResult with landmarks normalized [0,1] and optional annotated frame.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)

        hand_result = HandResult()

        if results.multi_hand_landmarks:
            for hand_lms, handedness_info in zip(
                results.multi_hand_landmarks,
                results.multi_handedness,
            ):
                # Extract (x, y, z) for each of 21 landmarks
                lms = [(lm.x, lm.y, lm.z) for lm in hand_lms.landmark]
                hand_result.landmarks.append(lms)

                # Handedness label (Left/Right) — note: mirrored in selfie mode
                label = handedness_info.classification[0].label
                hand_result.handedness.append(label)

                if draw:
                    self._mp_draw.draw_landmarks(
                        frame,
                        hand_lms,
                        self._mp_hands.HAND_CONNECTIONS,
                        self._mp_styles.get_default_hand_landmarks_style(),
                        self._mp_styles.get_default_hand_connections_style(),
                    )

        hand_result.num_hands = len(hand_result.landmarks)
        if draw:
            hand_result.annotated_frame = frame

        return hand_result

    def close(self) -> None:
        self._hands.close()
