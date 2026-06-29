"""Step 3 のページ操作と、fitz 保存での /Rotate 互換を検証する。"""
from __future__ import annotations

import os
import sys
import tempfile

import fitz
import pikepdf

sys.path.insert(0, os.path.dirname(__file__))
from viewer.document import PdfDocument

TMP = tempfile.gettempdir()


def build(path: str, pages: int, tag: str = "P") -> None:
    doc = fitz.open()
    for n in range(pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 144), f"{tag}{n + 1}", fontsize=40)
    doc.save(path)
    doc.close()


def order(path: str) -> list[str]:
    """各ページ先頭テキストを並べて、ページ順を可視化する。"""
    doc = fitz.open(path)
    out = [doc.load_page(i).get_text().strip() for i in range(doc.page_count)]
    doc.close()
    return out


def page_count(path: str) -> int:
    doc = fitz.open(path)
    n = doc.page_count
    doc.close()
    return n


def main() -> int:
    src = os.path.join(TMP, "_ops_src.pdf")
    build(src, 5, "P")  # P1..P5

    # --- 回転 + fitz 保存で /Rotate 互換が保たれるか ----------------
    d = PdfDocument()
    d.open(src)
    d.rotate_page(0, 90)
    rot_out = os.path.join(TMP, "_ops_rot.pdf")
    d.save_as(rot_out)
    with pikepdf.open(rot_out) as pdf:
        assert int(pdf.pages[0].get("/Rotate", 0)) == 90
    print("OK: fitz保存でも /Rotate=90 を維持（互換性OK）")

    # --- 並べ替え move_page ----------------------------------------
    d2 = PdfDocument()
    d2.open(src)
    d2.move_page(0, 3)  # P1 を 4 番目付近へ
    mv_out = os.path.join(TMP, "_ops_mv.pdf")
    d2.save_as(mv_out)
    print("OK: move_page 後の順序 =", order(mv_out))
    assert "P1" in order(mv_out)
    assert len(order(mv_out)) == 5

    # --- 削除 -------------------------------------------------------
    d3 = PdfDocument()
    d3.open(src)
    d3.delete_page(1)  # P2 を削除
    del_out = os.path.join(TMP, "_ops_del.pdf")
    d3.save_as(del_out)
    res = order(del_out)
    assert res == ["P1", "P3", "P4", "P5"], res
    print("OK: delete_page 後 =", res)

    # --- 統合 insert_pdf -------------------------------------------
    other = os.path.join(TMP, "_ops_other.pdf")
    build(other, 2, "Q")  # Q1,Q2
    d4 = PdfDocument()
    d4.open(src)
    n = d4.insert_pdf(other)  # 末尾に追加
    assert n == 2
    assert d4.page_count == 7
    mrg_out = os.path.join(TMP, "_ops_merge.pdf")
    d4.save_as(mrg_out)
    res = order(mrg_out)
    assert res == ["P1", "P2", "P3", "P4", "P5", "Q1", "Q2"], res
    print("OK: insert_pdf 後 =", res)

    # --- 抽出 -------------------------------------------------------
    d5 = PdfDocument()
    d5.open(src)
    ext_out = os.path.join(TMP, "_ops_ext.pdf")
    d5.extract_to([4, 0, 2], ext_out)  # P5,P1,P3 を任意順で抽出
    res = order(ext_out)
    assert res == ["P5", "P1", "P3"], res
    print("OK: extract_to 後 =", res)

    # --- 分割 -------------------------------------------------------
    d6 = PdfDocument()
    d6.open(src)
    outs = d6.split_every(2, TMP, "_ops_split")
    counts = [page_count(p) for p in outs]
    assert counts == [2, 2, 1], counts
    print(f"OK: split_every(2) -> {len(outs)} ファイル, ページ数 {counts}")

    # 開いているドキュメントを閉じてから後始末
    for d in (d, d2, d3, d4, d5, d6):
        d.close()

    for p in [src, rot_out, mv_out, del_out, other, mrg_out, ext_out, *outs]:
        if os.path.exists(p):
            os.remove(p)
    print("ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
