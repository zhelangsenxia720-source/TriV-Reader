"""Step 4: 画像変換（PDF→画像 / 画像→PDF）の検証。"""
from __future__ import annotations

import os
import sys
import tempfile

import fitz

sys.path.insert(0, os.path.dirname(__file__))
from viewer.document import PdfDocument

TMP = tempfile.gettempdir()


def main() -> int:
    src = os.path.join(TMP, "_img_src.pdf")
    d = fitz.open()
    for n in range(3):
        p = d.new_page(width=595, height=842)  # A4
        p.insert_text((72, 144), f"P{n + 1}", fontsize=40)
    d.save(src)
    d.close()

    doc = PdfDocument()
    doc.open(src)

    # --- PDF → 画像（PNG, 72dpi）-----------------------------------
    pngs = doc.export_page_images([0, 1], TMP, fmt="png", dpi=72, stem="_img")
    assert len(pngs) == 2 and all(os.path.exists(p) for p in pngs)
    px = fitz.Pixmap(pngs[0])
    assert (px.width, px.height) == (595, 842), (px.width, px.height)
    print(f"OK: PDF→PNG 72dpi -> {px.width}x{px.height}, {len(pngs)}枚")

    # --- 解像度指定（150dpi で約2倍）------------------------------
    pngs_hi = doc.export_page_images([0], TMP, fmt="png", dpi=150, stem="_imghi")
    px_hi = fitz.Pixmap(pngs_hi[0])
    assert px_hi.width > 1200, px_hi.width
    print(f"OK: 150dpi -> {px_hi.width}x{px_hi.height}")

    # --- JPEG 書き出し ---------------------------------------------
    jpgs = doc.export_page_images([2], TMP, fmt="jpeg", dpi=72, stem="_imgj")
    assert jpgs[0].endswith(".jpg") and os.path.exists(jpgs[0])
    print("OK: JPEG 書き出し ->", os.path.basename(jpgs[0]))

    # --- 画像 → PDF -------------------------------------------------
    out_pdf = os.path.join(TMP, "_img_out.pdf")
    PdfDocument.images_to_pdf(pngs, out_pdf)
    chk = fitz.open(out_pdf)
    assert chk.page_count == 2, chk.page_count
    # ページの物理サイズは画像の DPI 由来だが、縦横比は元(A4)を保持する
    r = chk.load_page(0).rect
    chk.close()
    ratio = r.width / r.height
    assert abs(ratio - 595 / 842) < 0.01, ratio
    print(f"OK: 画像→PDF -> 2ページ, 比 {ratio:.3f} (A4縦={595/842:.3f})")

    # --- 画像をページとして取り込み --------------------------------
    before = doc.page_count
    added = doc.insert_images_as_pages([jpgs[0]])
    assert added == 1 and doc.page_count == before + 1
    print(f"OK: 画像をページ追加 -> {before}→{doc.page_count}ページ")

    doc.close()
    for p in [src, out_pdf, *pngs, *pngs_hi, *jpgs]:
        if os.path.exists(p):
            os.remove(p)
    print("ALL OK: 画像変換")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
