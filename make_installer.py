"""TriV-Reader の「普通のソフト」用インストーラ (Setup.exe) を作る。

Inno Setup (ISCC.exe) を使い、onedir ビルドを 1 本の Setup.exe にまとめます。
利用者は Setup.exe をダブルクリック → ウィザードでインストールでき、
スタートメニュー/デスクトップのショートカット・PDF 関連付け・
「アプリと機能」からのアンインストールに対応します（管理者不要）。

使い方:
    python make_installer.py            # 既存ビルドからインストーラ生成
    python make_installer.py --build    # 先に build_exe.py でビルドしてから生成

事前準備（最初の一度だけ）:
    winget install JRSoftware.InnoSetup
    （または https://jrsoftware.org/isdl.php から Inno Setup 6 を導入）

出力:
    %USERPROFILE%\\TriVReader_release\\TriVReader-Setup-<版>.exe
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ISS = os.path.join(HERE, "installer", "TriVReader.iss")


def _app_version() -> str:
    """viewer/version.py の APP_VERSION を読み取る。"""
    sys.path.insert(0, HERE)
    try:
        from viewer.version import APP_VERSION  # noqa: PLC0415
        return APP_VERSION
    except Exception:  # noqa: BLE001
        return "1.0.0"


def _find_iscc() -> str | None:
    """ISCC.exe（Inno Setup コンパイラ）を探す。"""
    found = shutil.which("iscc") or shutil.which("ISCC")
    if found:
        return found
    local = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        # winget の既定はユーザー領域へ入ることがある
        os.path.join(local, "Programs", "Inno Setup 6", "ISCC.exe") if local else "",
    ]
    for c in candidates:
        if not c:
            continue
        if os.path.exists(c):
            return c
    return None


def _source_dir() -> str:
    """onedir ビルド（TriVReader.exe と依存一式）のフォルダを返す。"""
    return os.path.join(
        os.path.expanduser("~"), "TriVReader_dist", "dist", "TriVReader"
    )


def main() -> int:
    version = _app_version()

    # 必要なら先にビルド
    if "--build" in sys.argv:
        print("=== build_exe.py でビルド中 ===")
        rc = subprocess.run([sys.executable, os.path.join(HERE, "build_exe.py")]).returncode
        if rc != 0:
            print("ビルドに失敗しました。", file=sys.stderr)
            return rc

    src = _source_dir()
    exe = os.path.join(src, "TriVReader.exe")
    if not os.path.exists(exe):
        print(
            "onedir ビルドが見つかりません:\n  " + exe + "\n"
            "先に `python build_exe.py` を実行するか、`python make_installer.py --build` を使ってください。",
            file=sys.stderr,
        )
        return 1

    iscc = _find_iscc()
    if not iscc:
        print(
            "Inno Setup (ISCC.exe) が見つかりません。\n"
            "  winget install JRSoftware.InnoSetup\n"
            "を実行して導入してから、もう一度お試しください。",
            file=sys.stderr,
        )
        return 1

    icon = os.path.join(os.path.expanduser("~"), "TriVReader_dist", "_build", "trivreader.ico")
    out_dir = os.path.join(os.path.expanduser("~"), "TriVReader_release")
    os.makedirs(out_dir, exist_ok=True)

    args = [
        iscc,
        f"/DMyAppVersion={version}",
        f"/DSourceDir={src}",
        f"/DOutputDir={out_dir}",
    ]
    if os.path.exists(icon):
        args.append(f"/DAppIcon={icon}")
    args.append(ISS)

    print("=== Inno Setup でインストーラを生成中 ===")
    print("ISCC:", iscc)
    rc = subprocess.run(args).returncode
    if rc != 0:
        print("インストーラ生成に失敗しました。", file=sys.stderr)
        return rc

    setup = os.path.join(out_dir, f"TriVReader-Setup-{version}.exe")
    print("\n=== 完了 ===")
    print("インストーラ:", setup)
    print("このファイルを配布 / ダブルクリックでインストールできます。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
