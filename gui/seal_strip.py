"""Bottom strip: seal sequence display with reference images and progress highlighting."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import config


class SealCard(QFrame):
    """Single seal card in the sequence strip with reference image."""

    def __init__(self, seal_id: str, img_size: int = 96, parent=None) -> None:
        super().__init__(parent)
        self.seal_id = seal_id
        self.setObjectName("sealCard")

        card_w = img_size + 24
        card_h = img_size + 40
        self.setFixedSize(card_w, card_h)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        display = config.SEAL_DISPLAY.get(seal_id, seal_id)

        # Seal reference image
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setFixedSize(img_size, img_size)

        img_path = config.seal_image_path(seal_id)
        if img_path.exists():
            pixmap = QPixmap(str(img_path))
            scaled = pixmap.scaled(
                img_size, img_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._image_label.setPixmap(scaled)
        else:
            self._image_label.setText(f"[{display.upper()}]")
            self._image_label.setStyleSheet("font-size: 14px; font-weight: bold;")

        layout.addWidget(self._image_label)

        # Seal name below
        self._name_label = QLabel(display)
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_label.setStyleSheet("font-size: 12px; color: #aaa;")
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
    """Horizontal strip showing the seal sequence for a selected jutsu.

    Card sizes adapt to the number of seals so fewer seals get bigger images.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(120)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(8, 4, 8, 4)

        self._title = QLabel("SEAL SEQUENCE")
        self._title.setObjectName("sectionTitle")
        self._outer.addWidget(self._title)

        self._strip_widget = QWidget()
        self._strip_layout = QHBoxLayout(self._strip_widget)
        self._strip_layout.setContentsMargins(0, 0, 0, 0)
        self._strip_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._outer.addWidget(self._strip_widget, stretch=1)

        self._cards: list[SealCard] = []
        self._placeholder = QLabel("Select a jutsu to see its seal sequence")
        self._placeholder.setStyleSheet("color: #666; font-style: italic;")
        self._strip_layout.addWidget(self._placeholder)

    def _calc_img_size(self, num_seals: int) -> int:
        """Calculate image size based on number of seals and available space."""
        available_h = self.height() - 60  # title + margins
        max_from_height = max(available_h - 40, 80)  # leave room for name label

        # Also limit by width: cards + arrows must fit
        available_w = self.width() - 30
        arrow_space = max(0, num_seals - 1) * 40
        card_w_budget = (available_w - arrow_space) / max(num_seals, 1)
        max_from_width = max(int(card_w_budget) - 24, 80)

        return min(max_from_height, max_from_width, 250)

    def set_sequence(self, seals: list[str]) -> None:
        """Display a new seal sequence with dynamically sized cards."""
        self._clear()

        if not seals:
            self._placeholder = QLabel("Select a jutsu to see its seal sequence")
            self._placeholder.setStyleSheet("color: #666; font-style: italic;")
            self._strip_layout.addWidget(self._placeholder)
            return

        img_size = self._calc_img_size(len(seals))

        for i, seal_id in enumerate(seals):
            if i > 0:
                arrow = QLabel("→")
                arrow.setStyleSheet("font-size: 24px; color: #666; padding: 0 6px;")
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._strip_layout.addWidget(arrow)

            card = SealCard(seal_id, img_size=img_size)
            self._cards.append(card)
            self._strip_layout.addWidget(card)

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
