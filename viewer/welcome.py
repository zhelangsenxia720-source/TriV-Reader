"""PDF 未読込時に表示するウェルカム画面。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class WelcomeWidget(QWidget):
    """中央にアプリ名と「開く」ボタン、D&D ヒントを表示する。"""

    open_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QWidget()
        card.setObjectName("welcomeCard")
        card.setMaximumWidth(460)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(14)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo = QLabel("📄")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 56px;")
        lay.addWidget(logo)

        title = QLabel("PDF Editor")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        lay.addWidget(title)

        subtitle = QLabel("閲覧・編集・注釈・OCR・変換まで、これひとつで。")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: palette(mid); font-size: 13px;")
        subtitle.setWordWrap(True)
        lay.addWidget(subtitle)

        lay.addSpacing(8)
        self.open_button = QPushButton("PDF を開く")
        self.open_button.setObjectName("primary")
        self.open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_button.clicked.connect(self.open_requested.emit)
        lay.addWidget(self.open_button, alignment=Qt.AlignmentFlag.AlignCenter)

        hint = QLabel("またはここに PDF をドラッグ&ドロップ")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: palette(mid); font-size: 12px;")
        lay.addWidget(hint)

        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
