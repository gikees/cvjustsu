"""Application QSS styling — clean neutral theme."""

DARK_BG = "#2b2b2b"
PANEL_BG = "#333333"
ACCENT = "#4a9eff"
ACCENT_HOVER = "#3a8eef"
TEXT_PRIMARY = "#e0e0e0"
TEXT_SECONDARY = "#999"
BORDER_COLOR = "#555"
HIGHLIGHT_BG = "#444"

APP_STYLE = f"""
QMainWindow {{
    background-color: {DARK_BG};
}}

QWidget {{
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 13px;
}}

QLabel {{
    color: {TEXT_PRIMARY};
}}

QLabel#sectionTitle {{
    font-size: 14px;
    font-weight: bold;
    padding: 4px 0px;
}}

QPushButton {{
    background-color: {HIGHLIGHT_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 6px 14px;
}}

QPushButton:hover {{
    background-color: {ACCENT};
}}

QPushButton:pressed {{
    background-color: {ACCENT_HOVER};
}}

QPushButton:checked {{
    background-color: {ACCENT};
    border: 1px solid {ACCENT};
}}

QListWidget {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 4px;
    outline: none;
}}

QListWidget::item {{
    padding: 8px;
    border-radius: 3px;
}}

QListWidget::item:selected {{
    background-color: {ACCENT};
    color: white;
}}

QListWidget::item:hover {{
    background-color: {HIGHLIGHT_BG};
}}

QComboBox {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 4px 8px;
    color: {TEXT_PRIMARY};
}}

QComboBox::drop-down {{
    border: none;
}}

QComboBox QAbstractItemView {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER_COLOR};
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT};
}}

QProgressBar {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    text-align: center;
    color: {TEXT_PRIMARY};
    height: 18px;
}}

QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 3px;
}}

QStatusBar {{
    background-color: {PANEL_BG};
    color: {TEXT_SECONDARY};
    border-top: 1px solid {BORDER_COLOR};
    font-size: 12px;
}}

QFrame#panel {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px;
}}

QFrame#sealCard {{
    background-color: {DARK_BG};
    border: 2px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 6px;
}}

QFrame#sealCardActive {{
    background-color: {DARK_BG};
    border: 2px solid {ACCENT};
    border-radius: 8px;
    padding: 6px;
}}

QFrame#sealCardDone {{
    background-color: {HIGHLIGHT_BG};
    border: 2px solid {ACCENT};
    border-radius: 8px;
    padding: 6px;
}}
"""
