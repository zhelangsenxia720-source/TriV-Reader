"""しおり/目次・最適化(圧縮)・PDF/A 化の検証。"""
from __future__ import annotations

import os
import sys
import tempfile

import fitz

sys.path.insert(0, os.path.dirname(__file__))
from viewer.document import PdfDocument

TMP = tempfile.gettempdir()


def build(path: str, pages: int = 4) -> None:
    d = fitz.open()
    for n in range(pages):
        p = d.new_page(width=595, height=842)
        p.insert_text((72, 100), f"Chapter {n + 1}", fontsize=24)
    d.save(path)
    d.close()


def main() -> int:
    src = os.path.join(TMP, "_meta_src.pdf")
    build(src, 4)

    # --- しおり / 目次 ---------------------------------------------
    doc = PdfDocument()
    doc.open(src)
    assert doc.get_toc() == []
    doc.set_toc([[1, "表紙", 1], [1, "本文", 2], [2, "節1", 3], [1, "付録", 4]])
    out = os.path.join(TMP, "_meta_toc.pdf")
    doc.save_as(out)
    doc.close()

    chk = fitz.open(out)
    toc = chk.get_toc(simple=True)
    chk.close()
    assert len(toc) == 4 and toc[0][1] == "表紙" and toc[2][0] == 2, toc
    print("OK: しおり/目次が標準アウトラインとして保存 ->", [t[1] for t in toc])

    # 追加
    doc2 = PdfDocument(); doc2.open(out)
    doc2.add_bookmark("追記", 4)
    assert len(doc2.get_toc()) == 5
    doc2.close()
    print("OK: しおり追加")

    # --- 最適化（圧縮） --------------------------------------------
    # 冗長な大きめPDFを作る（同じ画像を多数）
    big = os.path.join(TMP, "_meta_big.pdf")
    bd = fitz.open()
    for _ in range(5):
        pg = bd.new_page(width=595, height=842)
        pg.insert_text((72, 100), "x " * 2000, fontsize=8)  # 大量テキスト
    bd.save(big)
    bd.close()
    doc3 = PdfDocument(); doc3.open(big)
    comp = os.path.join(TMP, "_meta_comp.pdf")
    doc3.compress_to(comp)
    doc3.close()
    s_before = os.path.getsize(big)
    s_after = os.path.getsize(comp)
    assert s_after <= s_before, (s_before, s_after)
    print(f"OK: 最適化 {s_before}B -> {s_after}B（{100*s_after//s_before}%）")

    # --- PDF/A-2b 化 -----------------------------------------------
    doc4 = PdfDocument(); doc4.open(src)
    pdfa = os.path.join(TMP, "_meta_pdfa.pdf")
    doc4.export_pdfa(pdfa)
    doc4.close()
    # OutputIntent と pdfaid を確認
    import pikepdf
    with pikepdf.open(pdfa) as pdf:
        assert "/OutputIntents" in pdf.Root, "OutputIntents が無い"
        oi = pdf.Root.OutputIntents[0]
        assert str(oi.S) == "/GTS_PDFA1", oi.S
        xmp = pdf.open_metadata()
        assert xmp.get("pdfaid:part") == "2", dict(xmp)
        assert xmp.get("pdfaid:conformance") == "B"
    # PyMuPDF でも開けること（壊れていない）
    v = fitz.open(pdfa); assert v.page_count == 4; v.close()
    print("OK: PDF/A-2b 化（OutputIntent + pdfaid:2B）")

    for f in (src, out, big, comp, pdfa):
        if os.path.exists(f):
            os.remove(f)
    print("ALL OK: しおり/最適化/PDF-A")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
