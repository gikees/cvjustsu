"""Right panel for data collection mode: seal selector, reference image, counts, capture."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import config


class CollectionPanel(QFrame):
    """Right panel for collecting training data."""

    capture_requested = pyqtSignal(str)  # Emits selected seal label
    train_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("COLLECT DATA")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        seal_label = QLabel("Seal:")
        layout.addWidget(seal_label)

        self._seal_combo = QComboBox()
        for seal_id in config.SEAL_NAMES:
            display = config.SEAL_DISPLAY.get(seal_id, seal_id)
            self._seal_combo.addItem(display, seal_id)
        self._seal_combo.currentIndexChanged.connect(self._on_seal_changed)
        layout.addWidget(self._seal_combo)

        # Reference image for the selected seal
        self._ref_image = QLabel()
        self._ref_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ref_image.setFixedSize(180, 150)
        self._ref_image.setStyleSheet("margin: 8px 0;")
        layout.addWidget(self._ref_image)

        sep = QLabel("─" * 20)
        sep.setStyleSheet("color: #555;")
        layout.addWidget(sep)

        counts_title = QLabel("Sample Counts:")
        counts_title.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(counts_title)

        counts_container = QWidget()
        counts_layout = QVBoxLayout(counts_container)
        counts_layout.setContentsMargins(0, 0, 0, 0)
        counts_layout.setSpacing(2)
        self._count_labels: dict[str, QLabel] = {}
        for seal_id in config.SEAL_NAMES:
            display = config.SEAL_DISPLAY.get(seal_id, seal_id)
            label = QLabel(f"{display}:  0")
            label.setStyleSheet("font-family: monospace;")
            self._count_labels[seal_id] = label
            counts_layout.addWidget(label)

        scroll = QScrollArea()
        scroll.setWidget(counts_container)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        layout.addWidget(scroll, stretch=1)

        self._capture_btn = QPushButton("CAPTURE (Space)")
        self._capture_btn.setStyleSheet("font-size: 14px; padding: 10px;")
        self._capture_btn.clicked.connect(self._on_capture)
        layout.addWidget(self._capture_btn)

        self._auto_btn = QPushButton("AUTO-CAPTURE: OFF")
        self._auto_btn.setCheckable(True)
        self._auto_btn.setStyleSheet("font-size: 14px; padding: 10px;")
        self._auto_btn.clicked.connect(self._toggle_auto_capture)
        layout.addWidget(self._auto_btn)

        self._auto_timer = QTimer(self)
        self._auto_timer.setInterval(1000)
        self._auto_timer.timeout.connect(self._on_capture)

        self._train_btn = QPushButton("Train Model")
        self._train_btn.clicked.connect(self.train_requested.emit)
        layout.addWidget(self._train_btn)

        # Load initial reference image
        self._update_ref_image()

    def _on_seal_changed(self, _index: int) -> None:
        self._update_ref_image()

    def _update_ref_image(self) -> None:
        seal_id = self._seal_combo.currentData()
        if seal_id is None:
            return
        img_path = config.seal_image_path(seal_id)
        if img_path.exists():
            pixmap = QPixmap(str(img_path))
            scaled = pixmap.scaled(
                170, 140,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._ref_image.setPixmap(scaled)
        else:
            display = config.SEAL_DISPLAY.get(seal_id, seal_id)
            self._ref_image.setText(f"[{display}]")

    def _on_capture(self) -> None:
        seal_id = self._seal_combo.currentData()
        self.capture_requested.emit(seal_id)

    def _toggle_auto_capture(self, checked: bool) -> None:
        if checked:
            self._auto_btn.setText("AUTO-CAPTURE: ON")
            self._auto_timer.start()
        else:
            self._auto_btn.setText("AUTO-CAPTURE: OFF")
            self._auto_timer.stop()

    def update_counts(self, counts: dict[str, int]) -> None:
        for seal_id, count in counts.items():
            if seal_id in self._count_labels:
                display = config.SEAL_DISPLAY.get(seal_id, seal_id)
                self._count_labels[seal_id].setText(f"{display}:  {count}")

    @property
    def selected_seal(self) -> str:
        return self._seal_combo.currentData()
