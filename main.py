"""自作 PDF エディタ エントリポイント。

実行: python main.py [開きたい.pdf]
"""
from __future__ import annotations

import getpass
import sys

from PySide6.QtCore import QLibraryInfo, Qt, QTranslator
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

from viewer import theme
from viewer.main_window import MainWindow

# ユーザー毎に一意なサーバー名（同一PCの複数ユーザーでも衝突しない）
try:
    _SERVER_NAME = f"PDFEditor-SingleInstance-{getpass.getuser()}"
except Exception:  # noqa: BLE001
    _SERVER_NAME = "PDFEditor-SingleInstance"


def _install_japanese(app: QApplication) -> list:
    """Qt 標準UI（保存/キャンセル/OK 等のボタン）を日本語化する。"""
    tr_dir = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    keep = []
    for name in ("qtbase_ja", "qt_ja"):
        tr = QTranslator(app)
        if tr.load(name, tr_dir):
            app.installTranslator(tr)
            keep.append(tr)  # GC されないよう参照を保持
    return keep


def _app_icon() -> QIcon:
    """シンプルなアプリアイコン（青い角丸＋PDF）を生成する。"""
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#2563eb"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(6, 6, 52, 52, 12, 12)
    p.setPen(QColor("#ffffff"))
    f = QFont()
    f.setBold(True)
    f.setPointSize(15)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "PDF")
    p.end()
    return QIcon(pm)


def _send_to_running(path: str) -> bool:
    """既に起動中のインスタンスがあれば path を送り、True を返す。"""
    sock = QLocalSocket()
    sock.connectToServer(_SERVER_NAME)
    if not sock.waitForConnected(300):
        return False
    sock.write((path or "").encode("utf-8"))
    sock.flush()
    sock.waitForBytesWritten(1000)
    sock.disconnectFromServer()
    if sock.state() != QLocalSocket.LocalSocketState.UnconnectedState:
        sock.waitForDisconnected(1000)
    return True


def _start_server(window: MainWindow) -> QLocalServer:
    """このインスタンスを主インスタンスとして待ち受ける。"""
    QLocalServer.removeServer(_SERVER_NAME)  # 前回クラッシュ等の残骸を掃除
    server = QLocalServer()
    server.listen(_SERVER_NAME)

    def _on_new_connection() -> None:
        conn = server.nextPendingConnection()
        if conn is None:
            return

        def _on_ready() -> None:
            path = bytes(conn.readAll()).decode("utf-8", "ignore").strip()
            window.activate_and_open(path)
            conn.disconnectFromServer()

        conn.readyRead.connect(_on_ready)

    server.newConnection.connect(_on_new_connection)
    return server


def main() -> int:
    app = QApplication(sys.argv)

    # 既に起動中なら、そのインスタンスにパスを渡して即終了（同一ウィンドウのタブで開く）
    file_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if _send_to_running(file_arg):
        return 0

    app.setApplicationName("PDF Editor")
    app.setOrganizationName("pdfeditor")
    app.setApplicationDisplayName("PDF Editor")
    app.setWindowIcon(_app_icon())
    # ウィンドウを閉じてもアプリは終了させない（トレイ常駐＝次回を高速化）。
    # 実際の終了は MainWindow 側で QApplication.quit() を明示的に呼ぶ。
    app.setQuitOnLastWindowClosed(False)
    app._jp_translators = _install_japanese(app)  # 標準ボタン等を日本語化
    theme.apply_theme(app, dark=False)  # 既定はライト（設定があれば後で切替）

    window = MainWindow()
    window.show()
    app._single_server = _start_server(window)  # GC されないよう参照を保持

    # コマンドライン引数で PDF を渡されたら開く
    if file_arg:
        window.open_path(file_arg)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
