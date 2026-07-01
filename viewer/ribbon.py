"""リボンUI（タブ切替式のグループ化ツールバー）。

Office / Foxit などで一般的な「リボン」レイアウトを、このアプリの既存 QAction を
そのまま流用して組み立てる。各ボタンは QToolButton.setDefaultAction で action に
束ねるため、有効/無効・チェック状態は action 側と自動同期する。

表示ルール（バランス重視）:
- 小ボタンは縦2段スタックが基本（高さを抑えて横に効率よく並べる）。
- big ボタン: 幅はラベルに合わせて自動（文字は見切れない）。主要機能のみに使う。
- 長い action 名は action.setIconText("短い名前") でリボン用の短縮表示にできる。
- 折りたたみ: 右上の ▴ ボタン / タブのダブルクリック。折りたたみ中はタブバーのみ。
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

STACK_ROWS = 2  # 小ボタンの段数（2段=横に効率配置）


def _apply_ribbon_text(btn: QToolButton, action) -> None:
    """リボン用の短縮ラベル（iconText）があればボタンに反映する。"""
    it = action.iconText()
    if it and it != action.text():
        btn.setText(it)


class RibbonGroup(QWidget):
    """リボン内の1グループ（上部にボタン、下部にグループ名）。"""

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
        _apply_ribbon_text(btn, action)
        btn.setAutoRaise(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if big:
            # 幅は文字に合わせて自動（固定幅にしない＝見切れ防止）
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setIconSize(QSize(20, 20))
            btn.setFixedHeight(50)
            fm = btn.fontMetrics()
            btn.setMinimumWidth(max(52, fm.horizontalAdvance(btn.text()) + 16))
        else:
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setIconSize(QSize(16, 16))
            btn.setMinimumHeight(24)
        self._row.addWidget(btn)
        return btn

    def add_stack(self, actions: list, rows: int = STACK_ROWS) -> None:
        """小ボタンを縦 rows 段で積む。列内のボタン幅は自動で揃う。"""
        col = None
        for i, act in enumerate(actions):
            if i % rows == 0:
                col = QVBoxLayout()
                col.setContentsMargins(0, 0, 0, 0)
                col.setSpacing(1)
                col.setAlignment(Qt.AlignmentFlag.AlignTop)
                self._row.addLayout(col)
            btn = QToolButton()
            btn.setDefaultAction(act)
            _apply_ribbon_text(btn, act)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setIconSize(QSize(16, 16))
            btn.setAutoRaise(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # 列の幅いっぱいに広げる → 同列のボタン幅が揃って整って見える
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setMinimumHeight(24)
            col.addWidget(btn)

    def add_widget(self, w: QWidget) -> None:
        self._row.addWidget(w)

    def add_label(self, text: str) -> None:
        self._row.addWidget(QLabel(text))


class Ribbon(QTabWidget):
    """タブごとにグループを並べるリボン本体。折りたたみ対応。"""

    EXPANDED_HEIGHT = 96  # 2段スタック向けに低め

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setDocumentMode(True)
        self.tabBar().setExpanding(False)
        self.setMaximumHeight(self.EXPANDED_HEIGHT)
        self.setObjectName("ribbon")
        self._collapsed = False

        # 折りたたみボタン。documentMode ではコーナーウィジェットが出ない環境が
        # あるため、リボン直下の子として自前で右上に配置する（確実に見える）。
        btn = QToolButton(self)
        btn.setText("▴")
        btn.setAutoRaise(True)
        btn.setToolTip("リボンを折りたたみ / 展開（タブのダブルクリックでも可）")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(24, 20)
        btn.clicked.connect(self.toggle_collapsed)
        btn.raise_()
        self._collapse_btn = btn

        # タブのダブルクリックで折りたたみ切替、折りたたみ中のクリックで展開
        self.tabBarDoubleClicked.connect(lambda _i: self.toggle_collapsed())
        self.tabBarClicked.connect(self._expand_if_collapsed)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt 命名)
        super().resizeEvent(event)
        # 右上（タブバーの行内）に常時配置
        self._collapse_btn.move(self.width() - self._collapse_btn.width() - 4, 2)
        self._collapse_btn.raise_()

    # --- 折りたたみ -----------------------------------------------------
    # 折りたたみ中にタブをクリックすると「一時展開」し、リボンの外を
    # クリックすると自動で再び折りたたまれる（Office と同じ挙動）。
    def is_collapsed(self) -> bool:
        return self._collapsed

    def set_collapsed(self, on: bool) -> None:
        self._collapsed = on
        self._end_temp_open()
        self._collapse_btn.setText("▾" if on else "▴")
        if on:
            self.setMaximumHeight(self.tabBar().sizeHint().height() + 3)
        else:
            self.setMaximumHeight(self.EXPANDED_HEIGHT)

    def toggle_collapsed(self) -> None:
        self.set_collapsed(not self._collapsed)

    def _expand_if_collapsed(self, _index: int) -> None:
        if self._collapsed and not getattr(self, "_temp_open", False):
            # 一時展開（_collapsed は True のまま）
            self._temp_open = True
            self.setMaximumHeight(self.EXPANDED_HEIGHT)
            QApplication.instance().installEventFilter(self)

    def _end_temp_open(self) -> None:
        if getattr(self, "_temp_open", False):
            self._temp_open = False
            QApplication.instance().removeEventFilter(self)

    def eventFilter(self, obj, event) -> bool:  # noqa: N802 (Qt 命名)
        # 一時展開中、リボンの外側をクリックしたら折りたたみへ戻す
        if (getattr(self, "_temp_open", False)
                and event.type() == QEvent.Type.MouseButtonPress):
            w = QApplication.widgetAt(QCursor.pos())
            inside = False
            while w is not None:
                if w is self:
                    inside = True
                    break
                w = w.parentWidget()
            if not inside:
                self._end_temp_open()
                self.setMaximumHeight(self.tabBar().sizeHint().height() + 3)
        return super().eventFilter(obj, event)

    # --- ページ / グループ ----------------------------------------------
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
#ribbon > QTabBar::tab { padding: 4px 16px; }
#ribbonGroupTitle { color: palette(mid); font-size: 11px; }
#ribbonSep { color: rgba(0,0,0,0.10); margin: 4px 2px; }
#ribbon QToolButton { padding: 2px 6px; border-radius: 4px; }
#ribbon QToolButton:hover { background: rgba(37,99,235,0.12); }
#ribbon QToolButton:checked { background: rgba(37,99,235,0.20); }
"""
