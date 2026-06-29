"""Step 5: OCR（透明テキスト層付与）の検証。

テキストを持つページは温存し、画像ページのみ OCR されることを確認する。
tessdata は Temp に用意（Program Files の eng をコピー）。
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

import fitz

sys.path.insert(0, os.path.dirname(__file__))
from viewer.document import PdfDocument

TMP = tempfile.gettempdir()


def build_tessdata() -> str:
    dst = os.path.join(TMP, "pe_tessdata")
    os.makedirs(dst, exist_ok=True)
    src = r"C:\Program Files\Tesseract-OCR\tessdata"
    for f in ("eng.traineddata", "osd.traineddata"):
        s = os.path.join(src, f)
        if os.path.exists(s) and not os.path.exists(os.path.join(dst, f)):
            shutil.copy(s, dst)
    return dst


def build_mixed_pdf(path: str) -> None:
    doc = fitz.open()
    # ページ0: 通常のテキスト（born-digital）
    p0 = doc.new_page(width=420, height=200)
    p0.insert_text((30, 100), "Born Digital Text", fontsize=24)
    # ページ1: 画像のみ（テキスト層なし＝擬似スキャン）
    tmp = fitz.open()
    tp = tmp.new_page(width=420, height=200)
    tp.insert_text((30, 100), "Scanned OCR 99", fontsize=28)
    pix = tp.get_pixmap(dpi=200)
    img_doc = fitz.open("png", pix.tobytes("png"))
    img_pdf = fitz.open("pdf", img_doc.convert_to_pdf())
    doc.insert_pdf(img_pdf)
    doc.save(path)
    doc.close()


def main() -> int:
    tess = build_tessdata()
    assert os.path.exists(os.path.join(tess, "eng.traineddata")), "eng データ無し"

    src = os.path.join(TMP, "_ocr_src.pdf")
    build_mixed_pdf(src)

    # 前提確認：ページ1は元々テキストが無い
    chk = fitz.open(src)
    assert chk.load_page(0).get_text().strip(), "page0 にテキストが無い"
    assert not chk.load_page(1).get_text().strip(), "page1 に最初からテキストがある"
    chk.close()

    doc = PdfDocument()
    doc.open(src)
    out = os.path.join(TMP, "_ocr_out.pdf")
    calls = []
    ok = doc.ocr_to(
        out, language="eng", tessdata=tess, dpi=200,
        progress=lambda done, total: calls.append((done, total)) or True,
    )
    doc.close()
    assert ok is True
    assert calls[-1] == (2, 2), calls

    res = fitz.open(out)
    t0 = res.load_page(0).get_text()
    t1 = res.load_page(1).get_text()
    res.close()
    assert "Born Digital" in t0, repr(t0)          # 元テキストは温存
    assert "Scanned" in t1 or "OCR" in t1, repr(t1)  # 画像ページがOCRで検索可能に
    print("OK: page0(温存)=", repr(t0.strip()))
    print("OK: page1(OCR) =", repr(t1.strip()))

    # キャンセル：progress が False を返すと保存せず False
    doc2 = PdfDocument()
    doc2.open(src)
    out2 = os.path.join(TMP, "_ocr_cancel.pdf")
    ok2 = doc2.ocr_to(
        out2, language="eng", tessdata=tess, dpi=200,
        progress=lambda done, total: False,  # 即キャンセル
    )
    doc2.close()
    assert ok2 is False and not os.path.exists(out2)
    print("OK: キャンセル動作")

    for p in [src, out]:
        if os.path.exists(p):
            os.remove(p)
    print("ALL OK: OCR")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
