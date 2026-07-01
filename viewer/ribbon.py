"""リボンUI（タブ切替式のグループ化ツールバー）。

Office / Foxit などで一般的な「リボン」レイアウトを、このアプリの既存 QAction を
そのまま流用して組み立てる。各ボタンは QToolButton.setDefaultAction で action に
束ねるため、有効/無効・チェック状態・テキストは action 側と自動同期する。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class RibbonGroup(QWidget):
    """リボン内の1グループ（下部にグループ名、上部にボタンの横並び）。"""

    def __init__(self, title: str) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 4, 6, 2)
        outer.setSpacing(2)
        self._row = QHBoxLayout()
        self._row.setContentsMargins(0, 0, 0, 0)
        self._row.setSpacing(2)
        self._row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        outer.addLayout(self._row, 1)
        cap = QLabel(title)
        cap.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        cap.setObjectName("ribbonGroupTitle")
        outer.addWidget(cap)

    def add_action(self, action, big: bool = False) -> QToolButton:
        btn = QToolButton()
        btn.setDefaultAction(action)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        btn.setAutoRaise(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if big:
            btn.setMinimumHeight(50)
            btn.setMinimumWidth(52)
        else:
            btn.setMinimumHeight(24)
        self._row.addWidget(btn)
        return btn

    def add_stack(self, actions: list) -> None:
        """小さなボタンを縦に3個ずつ積む（省スペース）。"""
        col = None
        for i, act in enumerate(actions):
            if i % 3 == 0:
                col = QVBoxLayout()
                col.setContentsMargins(0, 0, 0, 0)
                col.setSpacing(1)
                self._row.addLayout(col)
            btn = QToolButton()
            btn.setDefaultAction(act)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            btn.setAutoRaise(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            col.addWidget(btn)

    def add_widget(self, w: QWidget) -> None:
        self._row.addWidget(w)

    def add_label(self, text: str) -> None:
        self._row.addWidget(QLabel(text))


class Ribbon(QTabWidget):
    """タブごとにグループを並べるリボン本体。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setDocumentMode(True)
        self.tabBar().setExpanding(False)
        self.setMaximumHeight(118)
        self.setObjectName("ribbon")

    def add_page(self, name: str) -> QWidget:
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(4, 3, 4, 1)
        row.setSpacing(0)
        row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        page.setProperty("_ribbon_row", True)
        page._ribbon_row = row  # type: ignore[attr-defined]
        self.addTab(page, name)
        return page

    def add_group(self, page: QWidget, title: str) -> RibbonGroup:
        g = RibbonGroup(title)
        page._ribbon_row.addWidget(g)  # type: ignore[attr-defined]
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setObjectName("ribbonSep")
        page._ribbon_row.addWidget(sep)  # type: ignore[attr-defined]
        return g

    def end_page(self, page: QWidget) -> None:
        page._ribbon_row.addStretch(1)  # type: ignore[attr-defined]


RIBBON_QSS = """
#ribbon { background: palette(window); }
#ribbon > QTabBar::tab { padding: 4px 14px; }
#ribbonGroupTitle { color: palette(mid); font-size: 11px; }
#ribbonSep { color: rgba(0,0,0,0.12); margin: 4px 2px; }
#ribbon QToolButton { padding: 3px 8px; border-radius: 4px; }
#ribbon QToolButton:hover { background: rgba(37,99,235,0.12); }
#ribbon QToolButton:checked { background: rgba(37,99,235,0.20); }
"""
