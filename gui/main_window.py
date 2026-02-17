"""Main application window — minimal Phase 1 version."""

from __future__ import annotations

import numpy as np
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QMainWindow,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from cvjutsu.hand_tracker import HandResult
from gui.camera_widget import CameraThread, CameraWidget


class MainWindow(QMainWindow):
    """Top-level window with camera feed and hand tracking."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CVJutsu - Naruto Hand Seal Recognition")
        self.setMinimumSize(800, 600)

        # Camera widget
        self._camera_widget = CameraWidget()

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self._camera_widget)
        self.setCentralWidget(central)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("FPS: -- | Model: not loaded | Hands: 0 detected")

        # Camera thread
        self._camera_thread = CameraThread()
        self._camera_thread.frame_ready.connect(self._on_frame)
        self._camera_thread.fps_updated.connect(self._on_fps)
        self._camera_thread.error.connect(self._on_camera_error)

        self._current_fps = 0.0
        self._num_hands = 0

        self._camera_thread.start()

    @pyqtSlot(np.ndarray, object)
    def _on_frame(self, frame: np.ndarray, result: HandResult) -> None:
        self._num_hands = result.num_hands
        self._camera_widget.update_frame(frame)
        self._update_status()

    @pyqtSlot(float)
    def _on_fps(self, fps: float) -> None:
        self._current_fps = fps
        self._update_status()

    @pyqtSlot(str)
    def _on_camera_error(self, msg: str) -> None:
        self._status_bar.showMessage(f"Error: {msg}")

    def _update_status(self) -> None:
        self._status_bar.showMessage(
            f"FPS: {self._current_fps:.0f} | Model: not loaded | "
            f"Hands: {self._num_hands} detected"
        )

    def closeEvent(self, event) -> None:
        self._camera_thread.stop()
        event.accept()
