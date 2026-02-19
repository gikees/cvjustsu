"""Left panel: jutsu list with selection and info display."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

import config
from cvjutsu.jutsu_db import JUTSU_LIST


class JutsuMenu(QFrame):
    """Left panel showing available jutsu and selected jutsu info."""

    jutsu_selected = pyqtSignal(dict)  # Emits dict with display/element/seals

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("JUTSU MENU")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self._list = QListWidget()
        for jutsu in JUTSU_LIST:
            info = {
                "display": jutsu.display,
                "element": jutsu.element,
                "seals": jutsu.seals,
                "name": jutsu.name,
            }
            item = QListWidgetItem(jutsu.display)
            item.setData(256, info)  # Qt.UserRole = 256
            self._list.addItem(item)
        self._list.currentItemChanged.connect(self._on_selection)
        layout.addWidget(self._list)

        sep = QLabel("─" * 20)
        sep.setStyleSheet("color: #555;")
        layout.addWidget(sep)

        self._info_title = QLabel("SELECTED JUTSU:")
        self._info_title.setObjectName("sectionTitle")
        layout.addWidget(self._info_title)

        self._jutsu_name = QLabel("(none)")
        self._jutsu_name.setWordWrap(True)
        self._jutsu_name.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self._jutsu_name)

        self._element_label = QLabel("")
        layout.addWidget(self._element_label)

        self._seals_label = QLabel("")
        self._seals_label.setWordWrap(True)
        layout.addWidget(self._seals_label)

        layout.addStretch()

        self._selected_jutsu: dict | None = None

    def _on_selection(self, current: QListWidgetItem | None, _prev) -> None:
        if current is None:
            return
        info = current.data(256)
        self._selected_jutsu = info
        self._jutsu_name.setText(info["display"])
        self._element_label.setText(f"Element: {info['element']}")
        seal_names = [config.SEAL_DISPLAY.get(s, s) for s in info["seals"]]
        self._seals_label.setText(f"Seals: {len(info['seals'])} ({' → '.join(seal_names)})")
        self.jutsu_selected.emit(info)

    @property
    def selected_jutsu(self) -> dict | None:
        return self._selected_jutsu
