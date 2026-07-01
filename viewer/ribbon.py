"""リボンUI（タブ切替式のグループ化ツールバー）。

Office / Foxit などで一般的な「リボン」レイアウトを、このアプリの既存 QAction を
そのまま流用して組み立てる。各ボタンは QToolButton.setDefaultAction で action に
束ねるため、有効/無効・チェック状態・テキストは action 側と自動同期する。

アイコンは Windows 標準のアイコンフォント（Segoe Fluent Icons / Segoe MDL2
Assets）のグリフを描画して使う（モノクロで Word/Excel 風）。フォントやグリフが
無い環境ではアイコン無し（テキストのみ）に自動フォールバックする。
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontInfo,
    QFontMetrics,
    QIcon,
    QPainter,
    QPixmap,
)
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

_ICON_FONT_NAME: str | None = None
_ICON_FONT_CHECKED = False


def _icon_font_name() -> str | None:
    """使用できるアイコンフォント名を1回だけ判定してキャッシュする。"""
    global _ICON_FONT_NAME, _ICON_FONT_CHECKED
    if _ICON_FONT_CHECKED:
        return _ICON_FONT_NAME
    _ICON_FONT_CHECKED = True
    for name in ("Segoe Fluent Icons", "Segoe MDL2 Assets"):
        f = QFont(name)
        if QFontInfo(f).family() == name:
            _ICON_FONT_NAME = name
            break
    return _ICON_FONT_NAME


def sym_icon(glyph: str, px: int = 32, color: str = "#3c4043") -> QIcon:
    """アイコンフォントのグリフを描画して QIcon を返す。無ければ空アイコン。"""
    name = _icon_font_name()
    if not name or not glyph:
        return QIcon()
    font = QFont(name)
    font.setPixelSize(int(px * 0.66))
    if not QFontMetrics(font).inFontUcs4(ord(glyph[0])):
        return QIcon()  # このグリフはフォントに無い → テキストのみ
    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    p.setFont(font)
    p.setPen(QColor(color))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, glyph)
    p.end()
    return QIcon(pm)


class RibbonGroup(QWidget):
    """リボン内の1グループ（下部にグループ名、上部にボタン）。"""

    def __init__(self, title: str) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 3, 8, 2)
        outer.setSpacing(1)
        self._row = QHBoxLayout()
        self._row.setContentsMargins(0, 0, 0, 0)
        self._row.setSpacing(3)
        self._row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        outer.addLayout(self._row, 1)
        cap = QLabel(title)
        cap.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        cap.setObjectName("ribbonGroupTitle")
        outer.addWidget(cap)

    def add_action(self, action, big: bool = False) -> QToolButton:
        btn = QToolButton()
        btn.setDefaultAction(action)
        btn.setAutoRaise(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if big:
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setIconSize(QSize(26, 26))
            btn.setFixedSize(QSize(64, 64))
        else:
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setIconSize(QSize(16, 16))
            btn.setMinimumHeight(24)
        self._row.addWidget(btn)
        return btn

    def add_stack(self, actions: list) -> None:
        """小さなアイコン＋文字ボタンを縦に3個ずつ積む（省スペース・整列）。"""
        col = None
        for i, act in enumerate(actions):
            if i % 3 == 0:
                col = QVBoxLayout()
                col.setContentsMargins(0, 0, 0, 0)
                col.setSpacing(1)
                self._row.addLayout(col)
            btn = QToolButton()
            btn.setDefaultAction(act)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setIconSize(QSize(16, 16))
            btn.setAutoRaise(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setMinimumWidth(96)
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
        self.setMaximumHeight(120)
        self.setObjectName("ribbon")

    def add_page(self, name: str) -> QWidget:
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(4, 3, 4, 1)
        row.setSpacing(0)
        row.setAlignment(Qt.AlignmentFlag.AlignLeft)
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
#ribbon > QTabBar::tab { padding: 5px 16px; }
#ribbonGroupTitle { color: palette(mid); font-size: 11px; }
#ribbonSep { color: rgba(0,0,0,0.10); margin: 5px 2px; }
#ribbon QToolButton { padding: 2px 6px; border-radius: 4px; }
#ribbon QToolButton:hover { background: rgba(37,99,235,0.12); }
#ribbon QToolButton:checked { background: rgba(37,99,235,0.20); }
"""
