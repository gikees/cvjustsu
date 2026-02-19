"""Main application window with full GUI layout and mode switching."""

from __future__ import annotations

import numpy as np
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from cvjutsu.classifier import SealClassifier
from cvjutsu.data_collector import DataCollector
from cvjutsu.effects import EffectOverlay
from cvjutsu.features import extract_features
from cvjutsu.hand_tracker import HandResult
from cvjutsu.sequence_tracker import SequenceTracker
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
        toolbar.setStyleSheet("background-color: #333; padding: 4px 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)

        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet("font-weight: bold; margin-right: 6px;")
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

        help_btn = QPushButton("Help")
        help_btn.setCheckable(False)
        help_btn.clicked.connect(self._show_help)
        toolbar_layout.addWidget(help_btn)

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

        # Core components
        self._data_collector = DataCollector()
        self._classifier = SealClassifier()
        self._sequence_tracker = SequenceTracker()
        self._effect_overlay = EffectOverlay()
        self._selected_jutsu_seals: list[str] = []

        # Try to load saved model
        if self._classifier.load():
            self._status_bar.showMessage("Model loaded successfully")

        # Connect signals
        self._jutsu_menu.jutsu_selected.connect(self._on_jutsu_selected)
        self._control_panel.reset_clicked.connect(self._on_reset)
        self._collection_panel.capture_requested.connect(self._on_capture)
        self._collection_panel.train_requested.connect(self._on_train)

        # Initialize collection counts
        self._collection_panel.update_counts(self._data_collector.get_counts())

        # Camera thread
        self._camera_thread = CameraThread()
        self._camera_thread.frame_ready.connect(self._on_frame)
        self._camera_thread.fps_updated.connect(self._on_fps)
        self._camera_thread.error.connect(self._on_camera_error)

        self._current_fps = 0.0
        self._num_hands = 0
        self._last_result: HandResult | None = None

        self._camera_thread.start()

    def _set_mode(self, mode: str) -> None:
        self._mode = mode
        is_collect = mode == "collect"
        self._collect_btn.setChecked(is_collect)
        self._recognize_btn.setChecked(not is_collect)
        self._collection_panel.setVisible(is_collect)
        self._control_panel.setVisible(not is_collect)

    def _show_help(self) -> None:
        dlg = QMessageBox(self)
        dlg.setWindowTitle("How CVJutsu Works")
        dlg.setTextFormat(Qt.TextFormat.RichText)
        dlg.setText(
            "<h3>CVJutsu — Naruto Hand Seal Recognition</h3>"
            "<p>This app uses your webcam to detect Naruto-style hand seals "
            "in real time and match them to jutsu sequences.</p>"
        )
        dlg.setInformativeText(
            "<b>Recognize Mode</b><br>"
            "1. Select a jutsu from the left panel.<br>"
            "2. Perform the hand seals shown in the bottom strip.<br>"
            "3. Hold each seal steady until it is confirmed.<br>"
            "4. Complete the full sequence to trigger the jutsu!<br><br>"
            "<b>Collect Data Mode</b><br>"
            "1. Switch to <i>Collect Data</i> in the toolbar.<br>"
            "2. Pick a seal from the dropdown and match the reference image.<br>"
            "3. Press <b>Space</b> or click <b>Capture</b> to save a sample.<br>"
            "4. After collecting samples, click <b>Train</b> to build the model.<br><br>"
            "<b>Keyboard Shortcuts</b><br>"
            "<b>Space</b> — Capture sample (Collect mode)<br>"
            "<b>R</b> — Reset current sequence"
        )
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
        dlg.exec()

    @pyqtSlot(dict)
    def _on_jutsu_selected(self, jutsu: dict) -> None:
        self._selected_jutsu_seals = jutsu["seals"]
        self._seal_strip.set_sequence(jutsu["seals"])
        self._seal_strip.reset()

    @pyqtSlot()
    def _on_reset(self) -> None:
        self._control_panel.reset_display()
        self._seal_strip.reset()
        self._sequence_tracker.reset()

    @pyqtSlot(np.ndarray, object)
    def _on_frame(self, frame: np.ndarray, result: HandResult) -> None:
        self._num_hands = result.num_hands
        self._last_result = result

        # Run recognition pipeline in recognize mode
        if self._mode == "recognize" and self._classifier.is_loaded and result.num_hands > 0:
            features = extract_features(result.landmarks, result.handedness)
            if features is not None:
                seal, confidence = self._classifier.predict(features)
                tracker_state = self._sequence_tracker.update(seal, confidence)

                # Update control panel
                self._control_panel.set_seal(tracker_state.current_seal, tracker_state.current_confidence)
                self._control_panel.set_sequence(tracker_state.confirmed_sequence)

                if tracker_state.jutsu_just_matched and tracker_state.matched_jutsu:
                    self._control_panel.set_jutsu(tracker_state.matched_jutsu.display)
                    if tracker_state.matched_jutsu.effect_asset:
                        self._effect_overlay.trigger(tracker_state.matched_jutsu.effect_asset)

                # Update seal strip progress
                if self._selected_jutsu_seals:
                    completed = self._count_matching_prefix(
                        tracker_state.confirmed_sequence,
                        self._selected_jutsu_seals,
                    )
                    self._seal_strip.update_progress(completed)
        elif self._mode == "recognize" and result.num_hands == 0:
            self._sequence_tracker.update(None, 0.0)
            self._control_panel.set_seal(None)

        # Render effects overlay
        frame = self._effect_overlay.render(frame)

        self._camera_widget.update_frame(frame)
        self._update_status()

    def _count_matching_prefix(self, confirmed: list[str], target: list[str]) -> int:
        """Count how many seals from the end of confirmed match the target sequence prefix."""
        if not confirmed or not target:
            return 0
        # Check suffix of confirmed against prefix of target
        for start in range(len(confirmed)):
            suffix = confirmed[start:]
            match_len = 0
            for i, seal in enumerate(suffix):
                if i < len(target) and seal == target[i]:
                    match_len = i + 1
                else:
                    break
            if match_len > 0 and start + match_len == len(confirmed):
                return match_len
        return 0

    @pyqtSlot(float)
    def _on_fps(self, fps: float) -> None:
        self._current_fps = fps
        self._update_status()

    @pyqtSlot(str)
    def _on_camera_error(self, msg: str) -> None:
        self._status_bar.showMessage(f"Error: {msg}")

    def _update_status(self) -> None:
        model_status = "loaded" if self._classifier.is_loaded else "not loaded"
        self._status_bar.showMessage(
            f"FPS: {self._current_fps:.0f} | Model: {model_status} | "
            f"Hands: {self._num_hands} detected"
        )

    @pyqtSlot(str)
    def _on_capture(self, seal_label: str) -> None:
        if self._last_result is None or self._last_result.num_hands == 0:
            self._status_bar.showMessage("No hands detected — cannot capture")
            return
        ok = self._data_collector.save_sample(
            seal_label,
            self._last_result.landmarks,
            self._last_result.handedness,
        )
        if ok:
            counts = self._data_collector.get_counts()
            self._collection_panel.update_counts(counts)
            self._status_bar.showMessage(f"Captured sample for {seal_label}")
        else:
            self._status_bar.showMessage("Failed to capture sample")

    @pyqtSlot()
    def _on_train(self) -> None:
        """Train the model from collected data."""
        df = self._data_collector.load_all()
        if df is None or len(df) == 0:
            self._status_bar.showMessage("No training data available")
            return

        feature_cols = [c for c in df.columns if c != "label"]
        X = df[feature_cols].values.astype(np.float32)
        y = df["label"].values

        acc = self._classifier.train(X, y)
        self._classifier.save()
        self._status_bar.showMessage(f"Model trained — accuracy: {acc:.1%}")

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
