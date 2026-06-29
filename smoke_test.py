"""GUI を起動せずに描画パイプラインだけを検証するスモークテスト。

QPixmap の生成には QApplication が必要なため offscreen で起動する。
"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import fitz
from PySide6.QtWidgets import QApplication

from viewer.document import PdfDocument


def build_sample_pdf(path: str) -> None:
    doc = fitz.open()
    for n in range(3):
        page = doc.new_page(width=595, height=842)  # A4
        page.insert_text((72, 144), f"テスト用ページ {n + 1}", fontsize=24)
    doc.save(path)
    doc.close()


def main() -> int:
    app = QApplication(sys.argv)  # noqa: F841  QPixmap に必要
    # Documents 配下は Windows のフォルダー保護で書込不可のことがあるため temp を使う
    sample = os.path.join(tempfile.gettempdir(), "_trivreader_sample.pdf")
    build_sample_pdf(sample)

    doc = PdfDocument()
    doc.open(sample)
    assert doc.page_count == 3, doc.page_count

    page_px = doc.render_page(0, zoom=1.5)
    assert not page_px.isNull(), "ページ描画に失敗"
    assert page_px.width() > 0 and page_px.height() > 0

    thumb = doc.render_thumbnail(1, max_width=120)
    assert not thumb.isNull(), "サムネイル描画に失敗"
    assert thumb.width() <= 121, thumb.width()

    # --- Step 2: 回転の保存が標準 /Rotate に書かれるか検証 ----------
    import pikepdf

    doc.rotate_page(0, 90)
    doc.rotate_page(1, -90)  # = 270
    out = os.path.join(tempfile.gettempdir(), "_trivreader_rotated.pdf")
    doc.save_as(out)
    doc.close()

    # 別ライブラリ(pikepdf)で開き直し、/Rotate が想定どおりか確認。
    # = Adobe 以外のビューワーでも同じ向きで表示される、ということ。
    with pikepdf.open(out) as pdf:
        r0 = int(pdf.pages[0].get("/Rotate", 0))
        r1 = int(pdf.pages[1].get("/Rotate", 0))
        r2 = int(pdf.pages[2].get("/Rotate", 0))
    assert r0 == 90, r0
    assert r1 == 270, r1
    assert r2 == 0, r2

    # 再オープンして回転が保持されているか（往復確認）
    reopened = PdfDocument()
    reopened.open(out)
    assert reopened.rotation(0) == 90
    assert reopened.rotation(1) == 270
    reopened.close()

    os.remove(sample)
    os.remove(out)
    print(f"OK: pages={3}, page_px={page_px.width()}x{page_px.height()}, "
          f"thumb={thumb.width()}x{thumb.height()}")
    print(f"OK: /Rotate saved -> p0={r0}, p1={r1}, p2={r2} (標準準拠で永続化)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
