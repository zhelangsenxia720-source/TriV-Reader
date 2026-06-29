# 依存ライブラリを最新化して再ビルドする（セキュリティ更新の取り込み）
# 使い方:  powershell -ExecutionPolicy Bypass -File update.ps1 [build_exe.py への引数]
#   例:    powershell -File update.ps1 --portable
#          powershell -File update.ps1 --lite --portable
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

Write-Host "[1/3] 依存ライブラリを最新化..." -ForegroundColor Cyan
python -m pip install --upgrade pip
# 描画/PDF エンジンを含め最新へ（脆弱性修正の取り込み）
python -m pip install --upgrade PySide6 PyMuPDF pikepdf Pillow numpy pyinstaller

Write-Host "[2/3] バージョン確認..." -ForegroundColor Cyan
python -c "import fitz, PySide6, pikepdf; print('PyMuPDF', fitz.__doc__.split()[1]); print('PySide6', PySide6.__version__); print('pikepdf', pikepdf.__version__)"

Write-Host "[3/3] 再ビルド..." -ForegroundColor Cyan
python build_exe.py @args

Write-Host "完了: 最新の依存で再ビルドしました。" -ForegroundColor Green
