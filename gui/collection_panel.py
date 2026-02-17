"""Right panel for data collection mode: seal selector, counts, capture."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

import config


class CollectionPanel(QFrame):
    """Right panel for collecting training data."""

    capture_requested = pyqtSignal(str)  # Emits selected seal label
    train_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self.setFixedWidth(200)

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
        layout.addWidget(self._seal_combo)

        sep = QLabel("─" * 20)
        sep.setStyleSheet("color: #555; margin: 8px 0;")
        layout.addWidget(sep)

        counts_title = QLabel("Sample Counts:")
        counts_title.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(counts_title)

        self._count_labels: dict[str, QLabel] = {}
        for seal_id in config.SEAL_NAMES:
            display = config.SEAL_DISPLAY.get(seal_id, seal_id)
            label = QLabel(f"{display}:  0")
            label.setStyleSheet("font-family: monospace;")
            self._count_labels[seal_id] = label
            layout.addWidget(label)

        layout.addStretch()

        self._capture_btn = QPushButton("CAPTURE (Space)")
        self._capture_btn.setStyleSheet("font-size: 14px; padding: 10px;")
        self._capture_btn.clicked.connect(self._on_capture)
        layout.addWidget(self._capture_btn)

        self._train_btn = QPushButton("Train Model")
        self._train_btn.clicked.connect(self.train_requested.emit)
        layout.addWidget(self._train_btn)

    def _on_capture(self) -> None:
        seal_id = self._seal_combo.currentData()
        self.capture_requested.emit(seal_id)

    def update_counts(self, counts: dict[str, int]) -> None:
        for seal_id, count in counts.items():
            if seal_id in self._count_labels:
                display = config.SEAL_DISPLAY.get(seal_id, seal_id)
                self._count_labels[seal_id].setText(f"{display}:  {count}")

    @property
    def selected_seal(self) -> str:
        return self._seal_combo.currentData()
