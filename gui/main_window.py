"""Main application window with full GUI layout and mode switching."""

from __future__ import annotations

import time

import cv2
import numpy as np
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

import config
from cvjutsu.classifier import SealClassifier
from cvjutsu.data_collector import DataCollector
from cvjutsu.effects import EffectOverlay
from cvjutsu.features import extract_features
from cvjutsu.hand_tracker import HandResult
from cvjutsu.jutsu_db import JUTSU_LIST
from cvjutsu.sequence_tracker import SequenceTracker
from gui.camera_widget import CameraThread, CameraWidget
from gui.collection_panel import CollectionPanel
from gui.seal_strip import SealStrip
from gui.styles import APP_STYLE


class MainWindow(QMainWindow):
    """Top-level window with toolbar, camera feed, and seal strip."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CVJutsu - Naruto Hand Seal Recognition")
        self.setMinimumSize(900, 700)
        self.setStyleSheet(APP_STYLE)

        self._mode = "recognize"  # or "collect"

        # Build UI
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- Toolbar ---
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

        # Jutsu selector dropdown
        sep = QLabel("|")
        sep.setStyleSheet("color: #666; margin: 0 8px;")
        toolbar_layout.addWidget(sep)

        jutsu_label = QLabel("Jutsu:")
        jutsu_label.setStyleSheet("font-weight: bold; margin-right: 4px;")
        toolbar_layout.addWidget(jutsu_label)

        self._jutsu_combo = QComboBox()
        self._jutsu_combo.setMinimumWidth(220)
        self._jutsu_combo.addItem("— Select Jutsu —", None)
        for jutsu in JUTSU_LIST:
            info = {
                "display": jutsu.display,
                "element": jutsu.element,
                "seals": jutsu.seals,
                "name": jutsu.name,
            }
            self._jutsu_combo.addItem(jutsu.display, info)
        self._jutsu_combo.currentIndexChanged.connect(self._on_jutsu_combo_changed)
        toolbar_layout.addWidget(self._jutsu_combo)

        toolbar_layout.addStretch()

        self._reset_btn = QPushButton("Reset")
        self._reset_btn.clicked.connect(self._on_reset)
        toolbar_layout.addWidget(self._reset_btn)

        help_btn = QPushButton("Help")
        help_btn.setCheckable(False)
        help_btn.clicked.connect(self._show_help)
        toolbar_layout.addWidget(help_btn)

        root_layout.addWidget(toolbar)

        # --- Main content area ---
        content = QWidget()
        self._content_layout = QHBoxLayout(content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)

        # Center — camera + seal strip
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        self._camera_widget = CameraWidget()
        center_layout.addWidget(self._camera_widget, stretch=1)

        self._seal_strip = SealStrip()
        center_layout.addWidget(self._seal_strip)

        self._content_layout.addWidget(center, stretch=1)

        # Right panel — collection (only visible in collect mode)
        self._collection_panel = CollectionPanel()
        self._collection_panel.hide()
        self._content_layout.addWidget(self._collection_panel)

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

        # Overlay state for drawing on video
        self._overlay_seal: str | None = None
        self._overlay_confidence: float = 0.0
        self._overlay_jutsu: str | None = None
        self._overlay_jutsu_element: str | None = None
        self._overlay_jutsu_time: float = 0.0
        self._overlay_sequence: list[str] = []
        self._confirm_flash_frames: int = 0

        # Try to load saved model
        if self._classifier.load():
            self._status_bar.showMessage("Model loaded successfully")

        # Connect signals
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

    def _on_jutsu_combo_changed(self, index: int) -> None:
        info = self._jutsu_combo.itemData(index)
        if info is None:
            self._selected_jutsu_seals = []
            self._seal_strip.set_sequence([])
            return
        self._selected_jutsu_seals = info["seals"]
        self._seal_strip.set_sequence(info["seals"])
        self._seal_strip.reset()

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
            "1. Select a jutsu from the toolbar dropdown.<br>"
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

    @pyqtSlot()
    def _on_reset(self) -> None:
        self._overlay_seal = None
        self._overlay_confidence = 0.0
        self._overlay_jutsu = None
        self._overlay_jutsu_element = None
        self._overlay_jutsu_time = 0.0
        self._overlay_sequence = []
        self._confirm_flash_frames = 0
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

                self._overlay_seal = tracker_state.current_seal
                self._overlay_confidence = tracker_state.current_confidence
                self._overlay_sequence = tracker_state.confirmed_sequence

                if tracker_state.seal_just_confirmed:
                    self._confirm_flash_frames = 4

                if tracker_state.jutsu_just_matched and tracker_state.matched_jutsu:
                    self._overlay_jutsu = tracker_state.matched_jutsu.display
                    self._overlay_jutsu_element = tracker_state.matched_jutsu.element
                    self._overlay_jutsu_time = time.time()
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
            state = self._sequence_tracker.update(None, 0.0)
            self._overlay_seal = None
            self._overlay_confidence = 0.0
            self._overlay_sequence = state.confirmed_sequence

        # Draw recognition overlay on video
        if self._mode == "recognize":
            frame = self._draw_overlay(frame)

        # Render effects overlay
        frame = self._effect_overlay.render(frame)

        self._camera_widget.update_frame(frame)
        self._update_status()

    def _draw_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Draw recognition overlay: sequence chain, seal info, flash, and jutsu banner."""
        h, w = frame.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX

        # --- Confirmation flash (green border) ---
        if self._confirm_flash_frames > 0:
            cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 255, 0), 4)
            self._confirm_flash_frames -= 1

        # --- Sequence chain at upper-left ---
        if self._overlay_sequence:
            parts = []
            for seal in self._overlay_sequence:
                display = config.SEAL_DISPLAY.get(seal, seal)
                parts.append(display)
            # Append "?" for the next expected seal if a jutsu is selected
            if self._selected_jutsu_seals:
                idx = len(self._overlay_sequence)
                if idx < len(self._selected_jutsu_seals):
                    next_seal = self._selected_jutsu_seals[idx]
                    next_display = config.SEAL_DISPLAY.get(next_seal, next_seal)
                    parts.append(f"{next_display}?")
            chain_text = " \u2192 ".join(parts)
            font_scale = 0.6
            thickness = 1
            (tw, th), _ = cv2.getTextSize(chain_text, font, font_scale, thickness)
            # Semi-transparent background bar
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (tw + 20, th + 16), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
            cv2.putText(frame, chain_text, (10, th + 8), font, font_scale,
                        (255, 255, 255), thickness, cv2.LINE_AA)

        # --- Current seal + confidence at upper-right ---
        if self._overlay_seal:
            display = config.SEAL_DISPLAY.get(self._overlay_seal, self._overlay_seal)
            text = f"{display.upper()} {int(self._overlay_confidence * 100)}%"
            font_scale = 0.9
            thickness = 2
            (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)
            x = w - tw - 12
            y = 32
            cv2.putText(frame, text, (x + 1, y + 1), font, font_scale,
                        (0, 0, 0), thickness + 2, cv2.LINE_AA)
            cv2.putText(frame, text, (x, y), font, font_scale,
                        (100, 255, 100), thickness, cv2.LINE_AA)

        # --- Jutsu match banner (auto-clears after effect duration) ---
        if self._overlay_jutsu:
            elapsed = time.time() - self._overlay_jutsu_time
            if elapsed > EffectOverlay.EFFECT_DURATION:
                self._overlay_jutsu = None
                self._overlay_jutsu_element = None
            else:
                banner_h = 60
                banner_y = h - banner_h
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, banner_y), (w, h), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

                color = self._jutsu_element_color(self._overlay_jutsu_element)
                font_scale = 1.0
                thickness = 2
                (tw, th), _ = cv2.getTextSize(self._overlay_jutsu, font, font_scale, thickness)
                tx = (w - tw) // 2
                ty = banner_y + (banner_h + th) // 2
                cv2.putText(frame, self._overlay_jutsu, (tx + 1, ty + 1), font,
                            font_scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
                cv2.putText(frame, self._overlay_jutsu, (tx, ty), font,
                            font_scale, color, thickness, cv2.LINE_AA)

        return frame

    @staticmethod
    def _jutsu_element_color(element: str | None) -> tuple[int, int, int]:
        """Map jutsu element to BGR color for overlay text."""
        colors = {
            "Fire": (74, 88, 255),       # orange-red
            "Water": (255, 180, 60),     # blue
            "Lightning": (255, 255, 100), # light blue
            "Earth": (60, 160, 220),     # brown-gold
        }
        return colors.get(element or "", (255, 255, 255))

    def _count_matching_prefix(self, confirmed: list[str], target: list[str]) -> int:
        """Count how many seals from the end of confirmed match the target sequence prefix."""
        if not confirmed or not target:
            return 0
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

        acc = self._classifier.train(X, y, augment=True)
        self._classifier.save()
        classes = self._classifier.classes
        self._status_bar.showMessage(
            f"Model trained — accuracy: {acc:.1%} | "
            f"{len(classes)} classes: {', '.join(sorted(classes))}"
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
