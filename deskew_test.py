"""傾き補正(deskew)の検証：既知の傾きを与えて推定・補正できるか。"""
from __future__ import annotations

import io
import os
import sys
import tempfile

import fitz
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from viewer import deskew as deskew_mod
from viewer.document import PdfDocument

TMP = tempfile.gettempdir()


def make_skewed_scan(path: str, skew_deg: float) -> None:
    """テキストページを画像化し、skew_deg だけ傾けた『スキャン風』PDFを作る。"""
    d = fitz.open()
    p = d.new_page(width=595, height=842)
    for n in range(12):  # 複数行の文字（行が見えるように）
        p.insert_text((72, 80 + n * 40), "The quick brown fox jumps over", fontsize=16)
    pix = p.get_pixmap(dpi=150)
    d.close()
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    img = img.rotate(skew_deg, resample=Image.Resampling.BICUBIC,
                     fillcolor=(255, 255, 255), expand=False)
    out = fitz.open()
    buf = io.BytesIO(); img.save(buf, format="png")
    with fitz.open("png", buf.getvalue()) as idoc:
        with fitz.open("pdf", idoc.convert_to_pdf()) as ip:
            out.insert_pdf(ip)
    out.save(path)
    out.close()


def page_gray(path, index=0, dpi=150):
    d = fitz.open(path)
    pix = d.load_page(index).get_pixmap(dpi=dpi, alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).convert("L")
    d.close()
    return img


def main() -> int:
    src = os.path.join(TMP, "_dsk_src.pdf")
    make_skewed_scan(src, skew_deg=-5.0)  # 5度傾けた（時計回り）

    # 推定: 元画像の傾きを検出（補正に必要な角度）
    before = deskew_mod.estimate_skew(page_gray(src))
    print(f"推定傾き(補正前): {before:.1f}°")
    assert abs(before) >= 3.0, f"傾きを検出できていない: {before}"

    # 補正
    doc = PdfDocument(); doc.open(src)
    n = doc.deskew_all(dpi=150)
    out = os.path.join(TMP, "_dsk_out.pdf")
    doc.save_as(out); doc.close()
    assert n == 1, n

    # 補正後は残留傾きがほぼ0
    after = deskew_mod.estimate_skew(page_gray(out))
    print(f"残留傾き(補正後): {after:.1f}°")
    assert abs(after) <= 1.5, f"補正しきれていない: {after}"
    print("OK: 傾き検出→補正で残留傾きが減少")

    # テキストページは触らない（born-digital を保持）
    txt = os.path.join(TMP, "_dsk_txt.pdf")
    t = fitz.open(); tp = t.new_page(width=595, height=842)
    tp.insert_text((72, 100), "Born digital text", fontsize=18); t.save(txt); t.close()
    doc2 = PdfDocument(); doc2.open(txt)
    n2 = doc2.deskew_all(dpi=150)
    assert n2 == 0, n2  # テキストページはスキップ
    assert "Born digital" in doc2._doc.load_page(0).get_text()
    doc2.close()
    print("OK: テキストページは補正対象外（原本保持）")

    for f in (src, out, txt):
        if os.path.exists(f):
            os.remove(f)
    print("ALL OK: 傾き補正")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
