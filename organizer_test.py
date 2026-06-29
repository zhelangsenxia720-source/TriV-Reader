"""ページ整理画面のボタン並べ替え・選択表示を検証する。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import fitz
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(__file__))
from viewer.document import PdfDocument
from viewer.organizer import ORIG_INDEX_ROLE, PageOrganizer


def grid_order(grid) -> list:
    return [grid.item(r).data(ORIG_INDEX_ROLE) for r in range(grid.count())]


def main() -> int:
    app = QApplication(sys.argv)
    sample = os.path.join(tempfile.gettempdir(), "_org_sample.pdf")
    d = fitz.open()
    for n in range(6):
        p = d.new_page(width=595, height=842)
        p.insert_text((72, 144), f"P{n + 1}", fontsize=40)
    d.save(sample)
    d.close()

    doc = PdfDocument()
    doc.open(sample)

    org = PageOrganizer()
    org.load(doc)
    org.resize(800, 600)
    org.show()
    app.processEvents()
    grid = org.grid
    assert grid.count() == 6

    captured = {}
    grid.reordered.connect(
        lambda order, sel: captured.update(order=order, sel=sel)
    )

    # 右へ：P2(index1)を1つ右へ
    grid.clearSelection()
    grid.item(1).setSelected(True)
    grid.move_selected(1)
    assert grid_order(grid) == [0, 2, 1, 3, 4, 5], grid_order(grid)
    assert captured["order"] == [0, 2, 1, 3, 4, 5]
    # 移動後に選択すべき位置（新しい位置=2）が通知される
    assert captured["sel"] == [2], captured["sel"]
    grid.move_selected(-1)  # 左へ戻す
    assert grid_order(grid) == [0, 1, 2, 3, 4, 5], grid_order(grid)
    assert captured["sel"] == [1], captured["sel"]
    print("OK: 左へ/右へ（選択位置も通知）")

    # 選択復元 → 連続移動できることの確認
    org.select_positions([1])
    assert org.selected_indices() == [1]
    grid.move_selected(1)  # 続けて右へ
    assert grid_order(grid) == [0, 2, 1, 3, 4, 5], grid_order(grid)
    assert captured["sel"] == [2]
    org.select_positions([2])  # MainWindow が行う復元を模擬
    assert org.selected_indices() == [2]
    print("OK: 選択復元で連続移動が可能")
    grid.clearSelection()
    org.load(doc)  # 並びを元へ戻して以降のテストへ
    app.processEvents()

    # 先頭へ／末尾へ
    grid.clearSelection()
    grid.item(4).setSelected(True)  # P5
    grid.move_to_edge(True)
    assert grid_order(grid) == [4, 0, 1, 2, 3, 5], grid_order(grid)
    grid.clearSelection()
    grid.item(0).setSelected(True)  # 今は P5
    grid.move_to_edge(False)
    assert grid_order(grid) == [0, 1, 2, 3, 5, 4], grid_order(grid)
    print("OK: 先頭へ/末尾へ")

    # 端での移動は何も起きない（先頭をさらに左へ）
    grid.clearSelection()
    grid.item(0).setSelected(True)
    before = grid_order(grid)
    grid.move_selected(-1)
    assert grid_order(grid) == before
    print("OK: 端では移動しない")

    # 複数選択をまとめて右へ（連続2枚）
    grid.clearSelection()
    grid.item(0).setSelected(True)
    grid.item(1).setSelected(True)
    pre = grid_order(grid)
    grid.move_selected(1)
    post = grid_order(grid)
    # 連続2枚が揃って1つ右へ（pos0,1 → pos1,2）
    assert post[1] == pre[0] and post[2] == pre[1], (pre, post)
    print("OK: 複数選択をまとめて移動")

    # 選択数ラベル
    grid.clearSelection()
    org._update_selection_label()
    assert org._sel_label.text() == "未選択"
    grid.item(0).setSelected(True)
    grid.item(2).setSelected(True)
    app.processEvents()
    assert "2 ページ選択中" in org._sel_label.text(), org._sel_label.text()
    print("OK: 選択数ラベル =", org._sel_label.text())

    doc.close()
    os.remove(sample)
    print("ALL OK: ボタン並べ替え・選択表示")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
