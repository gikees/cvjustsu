"""Camera capture thread and display widget."""

from __future__ import annotations

import time

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot, Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel

import config
from cvjutsu.hand_tracker import HandTracker, HandResult


class CameraThread(QThread):
    """Captures frames from webcam, runs hand tracking, emits results."""

    frame_ready = pyqtSignal(np.ndarray, object)  # (annotated_frame, HandResult)
    fps_updated = pyqtSignal(float)
    error = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._running = False
        self._tracker = HandTracker()

    def run(self) -> None:
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        if not cap.isOpened():
            self.error.emit("Cannot open camera")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)

        self._running = True
        prev_time = time.time()
        frame_count = 0

        while self._running:
            ret, frame = cap.read()
            if not ret:
                continue

            # Mirror for selfie view
            frame = cv2.flip(frame, 1)

            result = self._tracker.process(frame, draw=True)
            display_frame = result.annotated_frame if result.annotated_frame is not None else frame

            self.frame_ready.emit(display_frame, result)

            # FPS calculation
            frame_count += 1
            now = time.time()
            elapsed = now - prev_time
            if elapsed >= 1.0:
                self.fps_updated.emit(frame_count / elapsed)
                frame_count = 0
                prev_time = now

        self._tracker.close()
        cap.release()

    def stop(self) -> None:
        self._running = False
        self.wait()


class CameraWidget(QLabel):
    """Displays camera frames as a QLabel."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(config.CAMERA_WIDTH, config.CAMERA_HEIGHT)
        self.setStyleSheet("background-color: #2b2b2b;")
        self.setText("Starting camera...")

    @pyqtSlot(np.ndarray)
    def update_frame(self, frame: np.ndarray) -> None:
        """Convert BGR frame to QPixmap and display."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaled)
