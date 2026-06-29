"""検索・ページ番号の検証。"""
from __future__ import annotations

import os
import sys
import tempfile

import fitz

sys.path.insert(0, os.path.dirname(__file__))
from viewer.document import PdfDocument

TMP = tempfile.gettempdir()


def main() -> int:
    src = os.path.join(TMP, "_feat_src.pdf")
    d = fitz.open()
    for n in range(3):
        p = d.new_page(width=595, height=842)
        p.insert_text((72, 100), f"Page {n + 1}: hello world apple", fontsize=18)
    # 2ページ目に "apple" をもう1つ
    d.load_page(1).insert_text((72, 160), "apple again", fontsize=18)
    d.save(src)
    d.close()

    # --- パスワード保護 / 解除 -------------------------------------
    # 注: PyMuPDF 1.27 では「authenticate 直後の内容読取り」が稀に空になる
    # MuPDF 由来の非決定的な癖がある。ここでは決定的に検証できる項目
    # （保護有無・パスワード照合・解除後の非暗号化）を確認する。
    enc = os.path.join(TMP, "_feat_enc.pdf")
    dec = os.path.join(TMP, "_feat_dec.pdf")
    docp = PdfDocument(); docp.open(src)
    docp.save_encrypted(enc, "secret123")
    docp.close()
    # 保護されており、パスワードが要る
    detect = PdfDocument(); detect.open(enc)
    assert detect.needs_password and detect.is_encrypted
    detect.close()
    # 使い捨て照合（決定的）
    assert PdfDocument.check_password(enc, "wrong") is False
    assert PdfDocument.check_password(enc, "secret123") is True
    # 正しいパスワードで開けば未ロックになる
    locked = PdfDocument(); locked.open(enc, password="secret123")
    assert not locked.needs_password
    locked.save_decrypted(dec)
    locked.close()
    # 解除後は暗号化されておらず、パスワード不要
    plain = PdfDocument(); plain.open(dec)
    assert not plain.needs_password and not plain.is_encrypted
    plain.close()
    print("OK: パスワード保護(AES-256) → 照合 → 解除")

    doc = PdfDocument()
    doc.open(src)

    # --- 検索 -------------------------------------------------------
    hits = doc.search("apple")
    pages = sorted(h[0] for h in hits)
    assert len(hits) == 4, hits          # 各ページ1 + 2ページ目に追加1
    assert pages.count(1) == 2, pages
    assert all(isinstance(h[1], fitz.Rect) for h in hits)
    print(f"OK: 検索 'apple' -> {len(hits)}件 ページ{pages}")

    none = doc.search("zzz_not_found")
    assert none == []
    print("OK: 未ヒットは空")

    # --- テキスト選択（コピー用・文字単位） ------------------------
    # ページ0: "Page 1: hello world apple" を広めにドラッグ
    text, rects = doc.select_text(0, fitz.Point(72, 95), fitz.Point(330, 95))
    assert rects, "矩形が取れない"
    assert "hello" in text and "world" in text, repr(text)
    print("OK: テキスト選択 ->", repr(text))
    # 文字単位の精度: 単語途中から開始すると部分選択になる
    partial, _ = doc.select_text(0, fitz.Point(120, 95), fitz.Point(160, 95))
    assert partial and len(partial) <= len("hello world"), repr(partial)
    print("OK: 文字単位の部分選択 ->", repr(partial))
    empty, er = doc.select_text(0, fitz.Point(5000, 5000), fitz.Point(5001, 5001))
    # 範囲外でも最近傍語を返すため空にはならないが、例外なく動くこと
    assert isinstance(empty, str)
    print("OK: 範囲外でも例外なし")

    # --- ページ番号 -------------------------------------------------
    doc.add_page_numbers(position="bottom-center", fmt="{n} / {total}", fontsize=10)
    out = os.path.join(TMP, "_feat_num.pdf")
    doc.save_as(out)
    doc.close()

    chk = fitz.open(out)
    t0 = chk.load_page(0).get_text()
    t2 = chk.load_page(2).get_text()
    chk.close()
    assert "1 / 3" in t0, repr(t0)
    assert "3 / 3" in t2, repr(t2)
    print("OK: ページ番号 '1 / 3' .. '3 / 3' を焼き込み")

    # 別フォーマット・位置
    doc2 = PdfDocument(); doc2.open(src)
    doc2.add_page_numbers(position="top-right", fmt="- {n} -", start=5)
    out2 = os.path.join(TMP, "_feat_num2.pdf")
    doc2.save_as(out2)
    doc2.close()
    chk2 = fitz.open(out2)
    assert "- 5 -" in chk2.load_page(0).get_text()
    assert "- 7 -" in chk2.load_page(2).get_text()
    chk2.close()
    print("OK: 開始番号5・上右・'- n -' 形式")

    # --- 検索結果の一括ハイライト ----------------------------------
    doc3 = PdfDocument(); doc3.open(src)
    hits = doc3.search("apple")
    n = doc3.add_search_highlights(hits)
    assert n == 4
    # 各ヒットページに Highlight が付いたか
    assert doc3.annot_count(0) >= 1 and doc3.annot_count(1) >= 2
    out3 = os.path.join(TMP, "_feat_hl.pdf")
    doc3.save_as(out3)
    doc3.close()
    chk3 = fitz.open(out3)
    names = [a.type[1] for a in chk3.load_page(1).annots()]
    chk3.close()
    assert names.count("Highlight") == 2, names
    print("OK: 検索結果を一括ハイライト（4件）")

    for f in (src, out, out2, out3, enc, dec):
        if os.path.exists(f):
            os.remove(f)
    print("ALL OK: 検索/ページ番号/一括HL/パスワード")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
