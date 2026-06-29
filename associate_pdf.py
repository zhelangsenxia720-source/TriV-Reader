"""PDF Editor を .pdf に関連付ける（管理者不要・現在のユーザーのみ）。

使い方:
    python associate_pdf.py "C:\\path\\to\\PDFEditor.exe"
    python associate_pdf.py            # 既定パス(%USERPROFILE%\\PDFEditor_dist)を探す
    python associate_pdf.py --remove   # 関連付けを解除

「プログラムから開く」に PDF Editor が追加されます。既定アプリにするには
Windows の［設定 > アプリ > 既定のアプリ］、または PDF を右クリック →
「プログラムから開く > 別のプログラムを選択」から PDF Editor を選んでください。
（Windows 10/11 では既定アプリの強制設定はOS側で制限されているため）
"""
from __future__ import annotations

import ctypes
import os
import sys
import winreg

PROGID = "PDFEditor.Document"
APP_NAME = "PDF Editor"


def _default_exe() -> str | None:
    root = os.path.join(os.path.expanduser("~"), "PDFEditor_dist", "dist")
    candidates = [
        os.path.join(root, "PDFEditor", "PDFEditor.exe"),  # onedir
        os.path.join(root, "PDFEditor.exe"),               # onefile
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def _set(key_path: str, name, value) -> None:
    k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
    winreg.SetValueEx(k, name, 0, winreg.REG_SZ, value)
    winreg.CloseKey(k)


def register(exe: str) -> None:
    icon = f'"{exe}",0'
    cmd = f'"{exe}" "%1"'
    classes = r"Software\Classes"
    # ProgID（このアプリの "ファイルの種類"）
    _set(rf"{classes}\{PROGID}", None, "PDF ドキュメント")
    _set(rf"{classes}\{PROGID}\DefaultIcon", None, icon)
    _set(rf"{classes}\{PROGID}\shell\open\command", None, cmd)
    # 「プログラムから開く」候補に追加
    _set(rf"{classes}\.pdf\OpenWithProgids", PROGID, "")
    # Applications にも登録（「別のプログラムを選択」に表示）
    appkey = rf"{classes}\Applications\PDFEditor.exe"
    _set(rf"{appkey}\shell\open\command", None, cmd)
    _set(rf"{appkey}\DefaultIcon", None, icon)
    _set(rf"{appkey}\SupportedTypes", ".pdf", "")
    _notify()
    print("関連付けを登録しました:", exe)
    print("PDF を右クリック →「プログラムから開く」に PDF Editor が出ます。")
    print("既定にするには Windows の［既定のアプリ］から PDF Editor を選択してください。")


def unregister() -> None:
    classes = r"Software\Classes"
    _delete_tree(rf"{classes}\{PROGID}")
    _delete_tree(rf"{classes}\Applications\PDFEditor.exe")
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"{classes}\.pdf\OpenWithProgids",
                           0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(k, PROGID)
        winreg.CloseKey(k)
    except FileNotFoundError:
        pass
    _notify()
    print("関連付けを解除しました。")


def _delete_tree(path: str) -> None:
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0,
                           winreg.KEY_ALL_ACCESS)
    except FileNotFoundError:
        return
    while True:
        try:
            sub = winreg.EnumKey(k, 0)
        except OSError:
            break
        _delete_tree(path + "\\" + sub)
    winreg.CloseKey(k)
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
    except FileNotFoundError:
        pass


def _notify() -> None:
    # SHCNE_ASSOCCHANGED でシェルに変更を通知
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)


def main() -> int:
    args = [a for a in sys.argv[1:]]
    if "--remove" in args:
        unregister()
        return 0
    exe = next((a for a in args if a.lower().endswith(".exe")), None) or _default_exe()
    if not exe or not os.path.exists(exe):
        print("PDFEditor.exe が見つかりません。先に build_exe.py でビルドするか、"
              "exe のパスを引数で指定してください。", file=sys.stderr)
        return 1
    register(os.path.abspath(exe))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
