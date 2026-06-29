"""墨消し・追加注釈・透かし・ヘッダー/フッター・ページ操作・メタデータ・抽出の検証。"""
from __future__ import annotations

import os
import sys
import tempfile

import fitz

sys.path.insert(0, os.path.dirname(__file__))
from viewer.document import PdfDocument

TMP = tempfile.gettempdir()
R = fitz.Rect


def build(path, pages=3):
    d = fitz.open()
    for n in range(pages):
        p = d.new_page(width=595, height=842)
        p.insert_text((72, 100), f"Page {n + 1} secret apple", fontsize=18)
    d.save(path)
    d.close()


def names(path, idx=0):
    doc = fitz.open(path)
    out = [a.type[1] for a in doc.load_page(idx).annots()]
    doc.close()
    return out


def main() -> int:
    src = os.path.join(TMP, "_e2_src.pdf")
    build(src)

    # --- 追加注釈 ---------------------------------------------------
    doc = PdfDocument(); doc.open(src)
    assert doc.add_underline(0, fitz.Point(72, 95), fitz.Point(200, 95)) is True
    assert doc.add_strikeout(0, fitz.Point(72, 95), fitz.Point(200, 95)) is True
    doc.add_line(0, fitz.Point(72, 200), fitz.Point(300, 200), arrow=True)
    doc.add_circle(0, R(72, 250, 200, 330))
    out = os.path.join(TMP, "_e2_annot.pdf")
    doc.save_as(out); doc.close()
    ns = names(out)
    for ex in ("Underline", "StrikeOut", "Line", "Circle"):
        assert ex in ns, (ex, ns)
    print("OK: 下線/取消線/直線(矢印)/円 ->", ns)

    # --- 墨消し -----------------------------------------------------
    docr = PdfDocument(); docr.open(src)
    # "secret" の位置を取得して墨消し
    page0 = docr._doc.load_page(0)
    rects = page0.search_for("secret")
    assert rects
    docr.add_redaction(0, rects[0])
    assert docr.pending_redactions(0) == 1
    docr.apply_redactions()
    red = os.path.join(TMP, "_e2_red.pdf")
    docr.save_as(red); docr.close()
    chk = fitz.open(red)
    assert "secret" not in chk.load_page(0).get_text(), "墨消し後も文字が残存"
    chk.close()
    print("OK: 墨消しで 'secret' を完全削除")

    # --- 透かし -----------------------------------------------------
    docw = PdfDocument(); docw.open(src)
    docw.add_watermark("CONFIDENTIAL")
    wm = os.path.join(TMP, "_e2_wm.pdf")
    docw.save_as(wm); docw.close()
    assert "CONFIDENTIAL" in fitz.open(wm).load_page(0).get_text()
    print("OK: 透かし挿入")

    # --- ヘッダー/フッター ------------------------------------------
    doch = PdfDocument(); doch.open(src)
    doch.add_header_footer(left="{filename}", center="社外秘",
                           right="{page}/{total}", top=False)
    hf = os.path.join(TMP, "_e2_hf.pdf")
    doch.save_as(hf); doch.close()
    t = fitz.open(hf).load_page(0).get_text()
    assert "社外秘" in t and "1/3" in t, repr(t)
    print("OK: ヘッダー/フッター ({page}/{total} 展開)")

    # --- ページ操作 -------------------------------------------------
    docp = PdfDocument(); docp.open(src)
    before = docp.page_count
    docp.insert_blank_page(1)
    assert docp.page_count == before + 1
    docp.duplicate_page(0)
    assert docp.page_count == before + 2
    crop = docp.auto_crop_rect(0)
    assert crop is not None
    docp.set_crop(0, crop)
    assert docp._doc.load_page(0).rect.width <= 595
    docp.close()
    print(f"OK: 白紙挿入/複製 {before}→{before + 2}, 自動クロップ")

    # --- メタデータ -------------------------------------------------
    docm = PdfDocument(); docm.open(src)
    docm.set_metadata({"title": "テスト文書", "author": "山田"})
    md = os.path.join(TMP, "_e2_md.pdf")
    docm.save_as(md)
    assert docm.get_metadata().get("title") == "テスト文書"
    docm.clear_metadata()
    assert not docm.get_metadata().get("title")
    docm.close()
    print("OK: メタデータ 設定→取得→一括削除")

    # --- 抽出 -------------------------------------------------------
    doct = PdfDocument(); doct.open(src)
    txt = os.path.join(TMP, "_e2.txt")
    htm = os.path.join(TMP, "_e2.html")
    doct.export_text(txt)
    doct.export_html(htm)
    doct.close()
    assert "Page 1" in open(txt, encoding="utf-8").read()
    assert "<" in open(htm, encoding="utf-8").read()
    print("OK: 全文テキスト/HTML 書き出し")

    # --- 差分(full_text + difflib) / バッチ(圧縮ループ) ------------
    import difflib
    a = os.path.join(TMP, "_e2_a.pdf"); b = os.path.join(TMP, "_e2_b.pdf")
    da = fitz.open(); da.new_page().insert_text((72, 100), "alpha beta", fontsize=14); da.save(a); da.close()
    db = fitz.open(); db.new_page().insert_text((72, 100), "alpha gamma", fontsize=14); db.save(b); db.close()
    d1 = PdfDocument(); d1.open(a); ta = d1.full_text(); d1.close()
    d2 = PdfDocument(); d2.open(b); tb = d2.full_text(); d2.close()
    diff = list(difflib.unified_diff(ta.splitlines(), tb.splitlines(), lineterm=""))
    assert any("beta" in d for d in diff) and any("gamma" in d for d in diff), diff
    print("OK: 2PDF差分(difflib)")

    # バッチ相当: 2ファイルを順に最適化
    outs = []
    for p in (a, b):
        dd = PdfDocument(); dd.open(p)
        o = p.replace(".pdf", "_opt.pdf"); dd.compress_to(o); dd.close()
        outs.append(o)
        assert os.path.exists(o)
    print(f"OK: バッチ相当 最適化 {len(outs)} 件")

    for f in (src, out, red, wm, hf, md, txt, htm, a, b, *outs):
        if os.path.exists(f):
            os.remove(f)
    print("ALL OK: 編集拡充/ページ操作/メタ/抽出/差分/バッチ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
