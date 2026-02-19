"""Right panel for recognition mode: current seal, sequence, jutsu match."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

import config


class ControlPanel(QFrame):
    """Right panel showing recognition status."""

    reset_clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("CURRENT SEAL")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self._seal_display = QLabel("[---]")
        self._seal_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._seal_display.setStyleSheet("font-size: 24px; font-weight: bold; padding: 12px;")
        layout.addWidget(self._seal_display)

        self._seal_name = QLabel("No seal detected")
        self._seal_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._seal_name.setStyleSheet("font-size: 12px; color: #aaa;")
        layout.addWidget(self._seal_name)

        conf_label = QLabel("Confidence:")
        conf_label.setStyleSheet("margin-top: 8px;")
        layout.addWidget(conf_label)

        self._confidence_bar = QProgressBar()
        self._confidence_bar.setRange(0, 100)
        self._confidence_bar.setValue(0)
        layout.addWidget(self._confidence_bar)

        sep1 = QLabel("─" * 20)
        sep1.setStyleSheet("color: #555;")
        layout.addWidget(sep1)

        seq_title = QLabel("SEQUENCE:")
        seq_title.setObjectName("sectionTitle")
        layout.addWidget(seq_title)

        self._sequence_label = QLabel("(empty)")
        self._sequence_label.setWordWrap(True)
        self._sequence_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self._sequence_label)

        sep2 = QLabel("─" * 20)
        sep2.setStyleSheet("color: #555;")
        layout.addWidget(sep2)

        jutsu_title = QLabel("JUTSU:")
        jutsu_title.setObjectName("sectionTitle")
        layout.addWidget(jutsu_title)

        self._jutsu_label = QLabel("(none yet)")
        self._jutsu_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._jutsu_label.setWordWrap(True)
        self._jutsu_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self._jutsu_label)

        layout.addStretch()

        self._reset_btn = QPushButton("Reset")
        self._reset_btn.clicked.connect(self.reset_clicked.emit)
        layout.addWidget(self._reset_btn)

    def set_seal(self, seal_id: str | None, confidence: float = 0.0) -> None:
        if seal_id is None:
            self._seal_display.setText("[---]")
            self._seal_name.setText("No seal detected")
            self._confidence_bar.setValue(0)
            return

        display = config.SEAL_DISPLAY.get(seal_id, seal_id)
        self._seal_display.setText(f"[{display.upper()}]")
        self._seal_name.setText(display)
        self._confidence_bar.setValue(int(confidence * 100))

    def set_sequence(self, seals: list[str]) -> None:
        if not seals:
            self._sequence_label.setText("(empty)")
            return
        names = [config.SEAL_DISPLAY.get(s, s) for s in seals]
        self._sequence_label.setText(" → ".join(names) + " → ?")

    def set_jutsu(self, jutsu_name: str | None) -> None:
        if jutsu_name is None:
            self._jutsu_label.setText("(none yet)")
            self._jutsu_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        else:
            self._jutsu_label.setText(f"✦ {jutsu_name} ✦")
            self._jutsu_label.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #4a9eff;"
            )

    def reset_display(self) -> None:
        self.set_seal(None)
        self.set_sequence([])
        self.set_jutsu(None)
