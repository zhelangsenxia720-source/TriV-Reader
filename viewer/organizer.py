"""ページ整理用の大画面（グリッド表示）。

サムネイルを大きなグリッドで並べ、複数選択して削除・抽出・回転、
ドラッグで並べ替えができる。ビューワーとは画面を切り替えて使う。
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .document import PdfDocument

ORIG_INDEX_ROLE = Qt.ItemDataRole.UserRole


class _Grid(QListWidget):
    """サムネイルのアイコングリッド。複数選択とボタンによる並べ替えに対応。

    ネイティブのドラッグ&ドロップは環境により動作しないため採用せず、
    「左へ/右へ」「先頭へ/末尾へ」ボタンで確実に並べ替える方式にしている。
    """

    reordered = Signal(list, list)  # (新しい順序, 移動後に選択すべき位置)
    """注: PageOrganizer 側にも同名・同型のシグナルがあり、そこへ転送される。"""

    def __init__(self, thumb: int, parent=None) -> None:
        super().__init__(parent)
        self._thumb = thumb
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Static)
        self.setUniformItemSizes(True)
        self.setSpacing(12)
        self.setIconSize(QSize(thumb, int(thumb * 1.4)))
        self.setGridSize(QSize(thumb + 30, int(thumb * 1.4) + 40))
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.apply_theme(False)

    def apply_theme(self, dark: bool) -> None:
        """選択ページ強調のスタイルをテーマに合わせる。"""
        if dark:
            self.setStyleSheet(
                """
                QListWidget { background: #242426; }
                QListWidget::item { border: 2px solid transparent; border-radius: 8px;
                    padding: 4px; color: #ddd; }
                QListWidget::item:selected { background: #234; border: 3px solid #3a8fe0;
                    color: #cfe6ff; }
                QListWidget::item:hover { background: #303338; }
                """
            )
        else:
            self.setStyleSheet(
                """
                QListWidget { background: #fafafa; }
                QListWidget::item { border: 2px solid transparent; border-radius: 8px;
                    padding: 4px; color: #333; }
                QListWidget::item:selected { background: #d6e4ff; border: 3px solid #1a73e8;
                    color: #0b3d91; }
                QListWidget::item:hover { background: #eef3ff; }
                """
            )

    def move_selected(self, step: int) -> None:
        """選択ページを step（-1=左 / +1=右）だけ移動する。"""
        rows = sorted(self.row(it) for it in self.selectedItems())
        if not rows:
            return
        if step < 0:
            if rows[0] == 0:
                return  # 先頭より前へは動かせない
            for r in rows:  # 左から処理
                it = self.takeItem(r)
                self.insertItem(r - 1, it)
                it.setSelected(True)
        else:
            if rows[-1] == self.count() - 1:
                return  # 末尾より後ろへは動かせない
            for r in reversed(rows):  # 右から処理
                it = self.takeItem(r)
                self.insertItem(r + 1, it)
                it.setSelected(True)
        self._emit_order()

    def move_to_edge(self, to_front: bool) -> None:
        """選択ページをまとめて先頭(または末尾)へ移動する。"""
        rows = sorted(self.row(it) for it in self.selectedItems())
        if not rows:
            return
        moved = [self.takeItem(r) for r in reversed(rows)]
        moved.reverse()
        base = 0 if to_front else self.count()
        self.clearSelection()
        for offset, it in enumerate(moved):
            self.insertItem(base + offset, it)
            it.setSelected(True)
        self._emit_order()

    def _emit_order(self) -> None:
        new_order = [
            self.item(r).data(ORIG_INDEX_ROLE) for r in range(self.count())
        ]
        # 移動後に選択し直すべき位置（再読み込みで選択が消えても復元するため）
        new_selected = sorted(self.row(it) for it in self.selectedItems())
        self.reordered.emit(new_order, new_selected)


class PageOrganizer(QWidget):
    """ページ整理画面。各操作は選択ページに対して行う。"""

    reordered = Signal(list, list)    # (新しい順序, 移動後に選択すべき位置)
    delete_requested = Signal(list)   # 選択ページの削除
    extract_requested = Signal(list)  # 選択ページの抽出
    export_images_requested = Signal(list)  # 選択ページを画像に書き出し
    rotate_requested = Signal(list, int)  # 選択ページの回転(度)
    split_requested = Signal()        # 分割
    page_activated = Signal(int)      # ダブルクリックでビューワーへ

    THUMB = 190

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        bar = QHBoxLayout()
        self._sel_label = QLabel("未選択")
        self._sel_label.setStyleSheet("font-weight:bold; color:#1a73e8;")
        bar.addWidget(self._sel_label)
        bar.addStretch(1)
        self._btn_front = QPushButton("⏮ 先頭へ")
        self._btn_move_l = QPushButton("◀ 左へ")
        self._btn_move_r = QPushButton("右へ ▶")
        self._btn_back = QPushButton("末尾へ ⏭")
        self._btn_rotate_l = QPushButton("⟲ 左回転")
        self._btn_rotate_r = QPushButton("⟳ 右回転")
        self._btn_delete = QPushButton("選択を削除")
        self._btn_extract = QPushButton("選択を抽出")
        self._btn_images = QPushButton("選択を画像に")
        self._btn_split = QPushButton("分割")
        for b in (
            self._btn_front,
            self._btn_move_l,
            self._btn_move_r,
            self._btn_back,
            self._btn_rotate_l,
            self._btn_rotate_r,
            self._btn_delete,
            self._btn_extract,
            self._btn_images,
            self._btn_split,
        ):
            bar.addWidget(b)
        layout.addLayout(bar)
        hint = QLabel(
            "ページを選択して「先頭へ / ◀左へ / 右へ▶ / 末尾へ」で並べ替え。"
            "Ctrl/Shift で複数選択できます。"
        )
        hint.setStyleSheet("color:#777;")
        layout.addWidget(hint)

        self.grid = _Grid(self.THUMB)
        layout.addWidget(self.grid)

        # 配線
        self._btn_front.clicked.connect(lambda: self.grid.move_to_edge(True))
        self._btn_back.clicked.connect(lambda: self.grid.move_to_edge(False))
        self._btn_move_l.clicked.connect(lambda: self.grid.move_selected(-1))
        self._btn_move_r.clicked.connect(lambda: self.grid.move_selected(1))
        self._btn_rotate_l.clicked.connect(
            lambda: self._emit_rotate(-90)
        )
        self._btn_rotate_r.clicked.connect(lambda: self._emit_rotate(90))
        self._btn_delete.clicked.connect(
            lambda: self._emit_selected(self.delete_requested)
        )
        self._btn_extract.clicked.connect(
            lambda: self._emit_selected(self.extract_requested)
        )
        self._btn_images.clicked.connect(
            lambda: self._emit_selected(self.export_images_requested)
        )
        self._btn_split.clicked.connect(self.split_requested.emit)
        self.grid.reordered.connect(self.reordered.emit)
        self.grid.itemDoubleClicked.connect(self._on_double_click)
        self.grid.itemSelectionChanged.connect(self._update_selection_label)

    # --- 読み込み -------------------------------------------------------
    def load(self, doc: PdfDocument) -> None:
        self.grid.clear()
        if not doc.is_open:
            return
        for i in range(doc.page_count):
            pixmap = doc.render_thumbnail(i, max_width=self.THUMB)
            item = QListWidgetItem(f"ページ {i + 1}")
            item.setIcon(pixmap)
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
            item.setData(ORIG_INDEX_ROLE, i)
            self.grid.addItem(item)

    def apply_theme(self, dark: bool) -> None:
        self.grid.apply_theme(dark)

    def selected_indices(self) -> list[int]:
        return sorted(self.grid.row(it) for it in self.grid.selectedItems())

    def select_positions(self, positions: list[int]) -> None:
        """指定位置のページを選択する（並べ替え後の選択復元に使う）。"""
        self.grid.clearSelection()
        last = None
        for p in positions:
            if 0 <= p < self.grid.count():
                self.grid.item(p).setSelected(True)
                last = p
        if last is not None:
            self.grid.setCurrentRow(last)
            self.grid.scrollToItem(self.grid.item(last))
        self._update_selection_label()

    def _update_selection_label(self) -> None:
        sel = self.selected_indices()
        if not sel:
            self._sel_label.setText("未選択")
        else:
            pages = ", ".join(str(i + 1) for i in sel)
            self._sel_label.setText(f"{len(sel)} ページ選択中（{pages}）")

    # --- 内部 -----------------------------------------------------------
    def _emit_selected(self, signal: Signal) -> None:
        sel = self.selected_indices()
        if sel:
            signal.emit(sel)

    def _emit_rotate(self, delta: int) -> None:
        sel = self.selected_indices()
        if sel:
            self.rotate_requested.emit(sel, delta)

    def _on_double_click(self, item: QListWidgetItem) -> None:
        self.page_activated.emit(self.grid.row(item))
