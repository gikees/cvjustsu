"""Bottom strip: seal sequence display with progress highlighting."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

import config


class SealCard(QFrame):
    """Single seal card in the sequence strip."""

    def __init__(self, seal_id: str, parent=None) -> None:
        super().__init__(parent)
        self.seal_id = seal_id
        self.setObjectName("sealCard")
        self.setFixedSize(100, 80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        display = config.SEAL_DISPLAY.get(seal_id, seal_id)

        self._icon_label = QLabel(f"[{display.upper()}]")
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self._icon_label)

        self._name_label = QLabel(display)
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_label.setStyleSheet("font-size: 11px; color: #aaa;")
        layout.addWidget(self._name_label)

    def set_state(self, state: str) -> None:
        """Set visual state: 'pending', 'active', or 'done'."""
        name_map = {
            "pending": "sealCard",
            "active": "sealCardActive",
            "done": "sealCardDone",
        }
        self.setObjectName(name_map.get(state, "sealCard"))
        self.style().unpolish(self)
        self.style().polish(self)


class SealStrip(QFrame):
    """Horizontal strip showing the seal sequence for a selected jutsu."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self.setFixedHeight(120)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(8, 4, 8, 4)

        self._title = QLabel("SEAL SEQUENCE")
        self._title.setObjectName("sectionTitle")
        self._outer.addWidget(self._title)

        self._strip_widget = QWidget()
        self._strip_layout = QHBoxLayout(self._strip_widget)
        self._strip_layout.setContentsMargins(0, 0, 0, 0)
        self._strip_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._outer.addWidget(self._strip_widget)

        self._cards: list[SealCard] = []
        self._placeholder = QLabel("Select a jutsu to see its seal sequence")
        self._placeholder.setStyleSheet("color: #666; font-style: italic;")
        self._strip_layout.addWidget(self._placeholder)

    def set_sequence(self, seals: list[str]) -> None:
        """Display a new seal sequence."""
        # Clear existing
        self._clear()

        if not seals:
            self._placeholder = QLabel("Select a jutsu to see its seal sequence")
            self._placeholder.setStyleSheet("color: #666; font-style: italic;")
            self._strip_layout.addWidget(self._placeholder)
            return

        for i, seal_id in enumerate(seals):
            if i > 0:
                arrow = QLabel("→")
                arrow.setStyleSheet("font-size: 20px; color: #666; padding: 0 4px;")
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._strip_layout.addWidget(arrow)

            card = SealCard(seal_id)
            self._cards.append(card)
            self._strip_layout.addWidget(card)

        self._strip_layout.addStretch()

    def update_progress(self, completed: int) -> None:
        """Highlight completed seals and mark the next as active."""
        for i, card in enumerate(self._cards):
            if i < completed:
                card.set_state("done")
            elif i == completed:
                card.set_state("active")
            else:
                card.set_state("pending")

    def reset(self) -> None:
        """Reset all cards to pending."""
        for card in self._cards:
            card.set_state("pending")

    def _clear(self) -> None:
        while self._strip_layout.count():
            item = self._strip_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()
