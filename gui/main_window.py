"""Main application window with full GUI layout and mode switching."""

from __future__ import annotations

import numpy as np
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from cvjutsu.hand_tracker import HandResult
from gui.camera_widget import CameraThread, CameraWidget
from gui.collection_panel import CollectionPanel
from gui.control_panel import ControlPanel
from gui.jutsu_menu import JutsuMenu
from gui.seal_strip import SealStrip
from gui.styles import APP_STYLE


class MainWindow(QMainWindow):
    """Top-level window with all panels, mode toggle, and camera feed."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CVJutsu - Naruto Hand Seal Recognition")
        self.setMinimumSize(1080, 700)
        self.setStyleSheet(APP_STYLE)

        self._mode = "recognize"  # or "collect"

        # Build UI
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Mode toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #16213e; padding: 4px 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)

        mode_label = self._make_label("Mode:")
        toolbar_layout.addWidget(mode_label)

        self._collect_btn = QPushButton("Collect Data")
        self._collect_btn.setCheckable(True)
        self._collect_btn.clicked.connect(lambda: self._set_mode("collect"))
        toolbar_layout.addWidget(self._collect_btn)

        self._recognize_btn = QPushButton("Recognize")
        self._recognize_btn.setCheckable(True)
        self._recognize_btn.setChecked(True)
        self._recognize_btn.clicked.connect(lambda: self._set_mode("recognize"))
        toolbar_layout.addWidget(self._recognize_btn)

        toolbar_layout.addStretch()
        root_layout.addWidget(toolbar)

        # Main content area: left | center | right
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(6, 6, 6, 6)
        content_layout.setSpacing(6)

        # Left panel — jutsu menu
        self._jutsu_menu = JutsuMenu()
        content_layout.addWidget(self._jutsu_menu)

        # Center — camera + seal strip
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(6)

        self._camera_widget = CameraWidget()
        center_layout.addWidget(self._camera_widget, stretch=1)

        self._seal_strip = SealStrip()
        center_layout.addWidget(self._seal_strip)

        content_layout.addWidget(center, stretch=1)

        # Right panel — recognition or collection
        self._control_panel = ControlPanel()
        self._collection_panel = CollectionPanel()
        self._collection_panel.hide()

        content_layout.addWidget(self._control_panel)
        content_layout.addWidget(self._collection_panel)

        root_layout.addWidget(content, stretch=1)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("FPS: -- | Model: not loaded | Hands: 0 detected")

        # Connect signals
        self._jutsu_menu.jutsu_selected.connect(self._on_jutsu_selected)
        self._control_panel.reset_clicked.connect(self._on_reset)

        # Camera thread
        self._camera_thread = CameraThread()
        self._camera_thread.frame_ready.connect(self._on_frame)
        self._camera_thread.fps_updated.connect(self._on_fps)
        self._camera_thread.error.connect(self._on_camera_error)

        self._current_fps = 0.0
        self._num_hands = 0
        self._last_result: HandResult | None = None

        self._camera_thread.start()

    def _make_label(self, text: str):
        from PyQt6.QtWidgets import QLabel
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight: bold; margin-right: 6px;")
        return lbl

    def _set_mode(self, mode: str) -> None:
        self._mode = mode
        is_collect = mode == "collect"
        self._collect_btn.setChecked(is_collect)
        self._recognize_btn.setChecked(not is_collect)
        self._collection_panel.setVisible(is_collect)
        self._control_panel.setVisible(not is_collect)

    @pyqtSlot(dict)
    def _on_jutsu_selected(self, jutsu: dict) -> None:
        self._seal_strip.set_sequence(jutsu["seals"])
        self._seal_strip.reset()

    @pyqtSlot()
    def _on_reset(self) -> None:
        self._control_panel.reset_display()
        self._seal_strip.reset()

    @pyqtSlot(np.ndarray, object)
    def _on_frame(self, frame: np.ndarray, result: HandResult) -> None:
        self._num_hands = result.num_hands
        self._last_result = result
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
        model_status = "not loaded"
        self._status_bar.showMessage(
            f"FPS: {self._current_fps:.0f} | Model: {model_status} | "
            f"Hands: {self._num_hands} detected"
        )

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Space and self._mode == "collect":
            self._collection_panel.capture_requested.emit(
                self._collection_panel.selected_seal
            )
        elif event.key() == Qt.Key.Key_R:
            self._on_reset()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        self._camera_thread.stop()
        event.accept()
