# PDF Editor — .exe 化と PDF 関連付け

## 1. 単体 .exe を作る

> 注意: このプロジェクトは `Documents` 配下にあり、Windows の「コントロールされた
> フォルダー アクセス（フォルダー保護）」が有効だとビルド出力が書けません。
> そのため出力先は既定で **`%USERPROFILE%\PDFEditor_dist`**（Documents の外）です。

```powershell
cd C:\Users\strin\Documents\ClaudeCodeDocs\pdfeditor
python build_exe.py            # フォルダ形式（推奨・起動が速い）
# python build_exe.py --onefile  # 単一 .exe（配布は楽だが起動が少し遅い）
```

- 出力: `%USERPROFILE%\PDFEditor_dist\dist\PDFEditor\PDFEditor.exe`
  （`--onefile` 時は `...\dist\PDFEditor.exe`）
- このフォルダごと配布できます（onedir の場合は `PDFEditor` フォルダ一式が必要）。
- 初回ビルドは数分、サイズは約 210MB（PySide6/PyMuPDF を同梱するため）。

### 必要なもの（開発機）
`pip install -r requirements.txt pyinstaller`

### 補足
- OCR の言語データはアプリが初回利用時に `%LOCALAPPDATA%\pdfeditor\tessdata` へ
  自動ダウンロードします（exe に同梱不要）。
- アイコン・起動スプラッシュはビルド時に自動生成します。

### 起動速度について（重要）
- **onedir（既定）を使ってください。onefile は毎回 200MB超 を一時フォルダに
  展開するため起動が数秒遅くなります。** ポータブルでもたつく場合はまず onedir に。
- アプリ自体の Python 起動は約 1 秒（重い numpy/PIL は使う時だけ読み込む遅延ロード）。
  サイズ・起動時間の大半は PyMuPDF(MuPDF+OCR エンジン)など中核ライブラリです。
- 起動直後に**スプラッシュ画面**が出るので、読み込み中も反応が分かります。
- 初回起動はウイルス対策/SmartScreen のスキャンで遅くなります。2回目以降は
  OS のファイルキャッシュで速くなります。

## 1.2 軽量版（OCR・傾き補正なし）

```powershell
python build_exe.py --lite             # 軽量版
# python build_exe.py --lite --portable  # 軽量＋ポータブル
```

- 出力: `%USERPROFILE%\PDFEditor_Lite_dist\dist\PDFEditor_Lite\PDFEditor_Lite.exe`
- OCR（文字認識）と傾き補正(deskew)の機能を**非表示**にし、それらが使う
  **numpy / Pillow を同梱しません**。
- サイズ: 約 **172MB**（通常版 約 211MB → 約 40MB 減）。タイトルは「PDF Editor (Lite)」。
- exe 隣の `lite.ini` で軽量モードを判定します（消すと通常UIに戻りますが、
  numpy/Pillow が無いため OCR以外の傾き補正は動きません）。

> 補足: OCR エンジン（Tesseract）は PyMuPDF 内部に同梱されているため、
> 「OCR を切る」だけではサイズはほぼ変わりません。軽量化の実体は
> numpy/Pillow（傾き補正用）の非同梱です。残りサイズの大半は PyMuPDF と Qt です。

## 1.5 ポータブル版（インストール不要・持ち運び可）

```powershell
python build_exe.py --portable            # フォルダ形式のポータブル版
# python build_exe.py --onefile --portable  # 単一exeのポータブル版
```

- ビルド時に exe の隣へ `portable.ini`（マーカー）が置かれ、アプリが
  **ポータブルモード**で起動します。
- ポータブルモードでは：
  - 設定（ダークモード/最近のファイル/ツールバー状態など）は
    **exe 隣の `PDFEditor.ini`** に保存（レジストリを汚さない）
  - OCR 言語データは **exe 隣の `PDFEditor_data\tessdata`** に保存
- フォルダ（onedir なら `PDFEditor` フォルダ一式）を **USB メモリ等にコピーして
  どの PC でもそのまま実行**できます。設定もデータも一緒に移動します。
- 既存のポータブルでないビルドをポータブル化するには、`PDFEditor.exe` と同じ
  フォルダに空の `portable.ini` を置くだけでも有効になります。
- exe 隣が書き込み不可の場所（例: Program Files）に置いた場合は、自動的に
  `%LOCALAPPDATA%` にフォールバックします。

> ポータブル運用ではレジストリを使わないため、**関連付け(下記)は行わない**のが
> 一般的です（持ち運び先の PC を汚さないため）。

## 1.8 セキュリティ更新（再ビルドで最新化）

```powershell
powershell -ExecutionPolicy Bypass -File update.ps1            # 依存を最新化して再ビルド
powershell -ExecutionPolicy Bypass -File update.ps1 --portable # 引数は build_exe.py へ渡る
```

描画/PDF エンジン(PyMuPDF)等を最新へ更新してから再ビルドします。脆弱性修正を
取り込みたい時に実行してください（凍結 exe は自動更新できないため再ビルド方式）。

## 1.9 コード署名（SmartScreen の「不明な発行元」対策）

```powershell
# 署名付きでビルド（PFX とパスワードを用意）
$env:PDFEDITOR_PFX_PW = "パスワード"
python build_exe.py --sign C:\path\to\cert.pfx
```

- 正式には有料のコード署名証明書（OV/EV）が確実です（EVは即SmartScreen評価あり）。
- 社内/自分のPC向けなら**自己署名証明書**でも警告を消せます:
  1. 証明書作成: `New-SelfSignedCertificate -Type CodeSigning -Subject "CN=MyName" -CertStoreLocation Cert:\CurrentUser\My`
  2. それを PFX に書き出し、配布先PCの「信頼されたルート証明機関／発行元」に取り込む
  3. 上記 `--sign` で署名
- `signtool`（Windows SDK 同梱）が必要です。

## 1.10 自動アップデート（アプリ内で更新→再起動）

アプリの「ヘルプ > 更新を確認」から、新しいビルドをダウンロードして
入れ替え・再起動できます（onedir 配布・Windows 向け）。

### 初回設定（1回だけ）
- `viewer/version.py` の **`GITHUB_REPO = "オーナー/リポジトリ"`** を設定するだけ。
  アプリは `https://github.com/<repo>/releases/latest/download/update.json` を見ます。
  （public リポジトリ推奨。利用者側の設定は不要）

### ★ いちばん簡単な方法（1コマンド公開）
GitHub CLI を使うと、ビルド〜zip化〜GitHub公開まで `release.py` 1つで完結します。

準備（最初の一度だけ）:
```powershell
winget install GitHub.cli   # GitHub CLI を導入
gh auth login               # ブラウザで認証（質問はEnter連打でOK）
# viewer/version.py の GITHUB_REPO = "オーナー/リポジトリ" を設定
```
毎回:
```powershell
# version.py の APP_VERSION を上げてから
python release.py --notes "更新内容"
# ポータブル版なら: python release.py --portable --notes "..."
```
→ ビルド → zip/update.json生成 → タグ作成 → GitHubへアップロードまで自動。
Webでのドラッグ＆ドロップは不要です。

### 手動で出すとき（GitHub Releases）
1. `viewer/version.py` の `APP_VERSION` を上げる（例 1.0.0 → 1.1.0）。
2. ビルド: `python build_exe.py`（必要なら `--portable` 等）。
3. リリース生成: `python make_release.py --notes "更新内容"`
   - `GITHUB_REPO` から URL を自動生成、**SHA256 も自動計算**して
     `%USERPROFILE%\PDFEditor_release\` に `PDFEditor-<版>.zip` と `update.json` を出力。
4. GitHub で **タグ `v<版>`（例 v1.1.0）のリリースを作成**し、上記 2 ファイルを添付。
5. 完了。利用者は「ヘルプ > 更新を確認」で DL→検証→入替→再起動まで自動。

> SHA256 を update.json に載せるので、アプリはダウンロードした zip を**改ざん検証**します。

### 仕組み / 安全性
- バージョン比較で新しい時のみ更新。zip は HTTPS で取得し onedir 一式を入れ替え。
- 入れ替えは「アプリ終了を待つ→robocopy で上書き→再起動」を行うヘルパー(.cmd)で実施。
  **ユーザーデータ（PDFEditor_data, *.ini）は保持**します（robocopy /E、/XD・/XF で除外）。
- 改ざん防止を強化したい場合は zip の SHA256 を update.json に載せて検証する拡張も可能です。

## 2. .pdf に関連付ける（管理者不要・現在のユーザーのみ）

```powershell
# ビルド済みの既定パスを自動検出して登録
python associate_pdf.py

# exe のパスを明示する場合
python associate_pdf.py "C:\Users\<you>\PDFEditor_dist\dist\PDFEditor\PDFEditor.exe"

# 解除
python associate_pdf.py --remove
```

登録すると、PDF を右クリック →「プログラムから開く」に **PDF Editor** が現れます。

### 既定アプリにする
Windows 10/11 は既定アプリの強制設定を OS 側で制限しているため、最後の一手は
手動です:
- PDF を右クリック →「プログラムから開く」→「別のプログラムを選択」→
  **PDF Editor** を選び「常にこのアプリを使う」にチェック、または
- ［設定 > アプリ > 既定のアプリ］で `.pdf` の既定を PDF Editor に変更。

## 3. 配布時の注意
- onedir 形式は `PDFEditor` フォルダ丸ごとが必要です（exe 単体では動きません）。
- インストーラ化したい場合は Inno Setup 等で `dist\PDFEditor` をパッケージし、
  関連付けはインストーラのスクリプトで登録するのが定番です。
