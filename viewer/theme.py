"""ライト/ダークのUIテーマ（パレット＋モダンなスタイルシート）。"""
from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

# テーマごとの色トークン
_LIGHT = {
    "window": "#f3f4f6", "base": "#ffffff", "alt": "#f7f8fa",
    "text": "#1f2328", "muted": "#9aa0a6", "border": "#d7dbe0",
    "toolbar": "#fbfcfd", "hover": "#eef0f3", "accent": "#2563eb",
    "accent_text": "#ffffff", "canvas": "#5a5d63",
}
_DARK = {
    "window": "#2b2d31", "base": "#1e1f22", "alt": "#26282c",
    "text": "#e4e6eb", "muted": "#80858c", "border": "#3a3d42",
    "toolbar": "#303236", "hover": "#3a3d42", "accent": "#3b82f6",
    "accent_text": "#ffffff", "canvas": "#202225",
}


def _palette(c: dict) -> QPalette:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(c["window"]))
    p.setColor(QPalette.ColorRole.WindowText, QColor(c["text"]))
    p.setColor(QPalette.ColorRole.Base, QColor(c["base"]))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(c["alt"]))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(c["base"]))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(c["text"]))
    p.setColor(QPalette.ColorRole.Text, QColor(c["text"]))
    p.setColor(QPalette.ColorRole.Button, QColor(c["base"]))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(c["text"]))
    p.setColor(QPalette.ColorRole.Highlight, QColor(c["accent"]))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(c["accent_text"]))
    p.setColor(QPalette.ColorRole.Link, QColor(c["accent"]))
    grp = QPalette.ColorGroup.Disabled
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText,
                 QPalette.ColorRole.WindowText):
        p.setColor(grp, role, QColor(c["muted"]))
    return p


def _qss(c: dict) -> str:
    return f"""
    QMainWindow, QDialog {{ background: {c['window']}; }}
    QToolBar {{ background: {c['toolbar']}; border: 0; border-bottom: 1px solid {c['border']};
        spacing: 3px; padding: 4px; }}
    QToolBar::separator {{ background: {c['border']}; width: 1px; margin: 4px 5px; }}
    QToolButton {{ color: {c['text']}; background: transparent; border: 1px solid transparent;
        border-radius: 6px; padding: 5px 9px; }}
    QToolButton:hover {{ background: {c['hover']}; }}
    QToolButton:pressed {{ background: {c['hover']}; }}
    QToolButton:checked {{ background: {c['accent']}; color: {c['accent_text']}; }}
    QToolButton:disabled {{ color: {c['muted']}; }}
    QMenuBar {{ background: {c['toolbar']}; color: {c['text']}; border-bottom: 1px solid {c['border']}; }}
    QMenuBar::item {{ padding: 5px 10px; background: transparent; border-radius: 4px; }}
    QMenuBar::item:selected {{ background: {c['hover']}; }}
    QMenu {{ background: {c['base']}; color: {c['text']}; border: 1px solid {c['border']};
        padding: 4px; }}
    QMenu::item {{ padding: 6px 26px; border-radius: 4px; }}
    QMenu::item:selected {{ background: {c['accent']}; color: {c['accent_text']}; }}
    QMenu::separator {{ height: 1px; background: {c['border']}; margin: 4px 8px; }}
    QStatusBar {{ background: {c['toolbar']}; border-top: 1px solid {c['border']}; color: {c['text']}; }}
    QStatusBar QLabel {{ color: {c['text']}; }}
    QPushButton {{ background: {c['base']}; border: 1px solid {c['border']}; border-radius: 6px;
        padding: 6px 14px; color: {c['text']}; }}
    QPushButton:hover {{ background: {c['hover']}; }}
    QPushButton:pressed {{ background: {c['hover']}; }}
    QPushButton:disabled {{ color: {c['muted']}; }}
    QPushButton#primary {{ background: {c['accent']}; color: {c['accent_text']}; border: 0;
        padding: 9px 22px; font-weight: 600; }}
    QPushButton#primary:hover {{ background: {c['accent']}; }}
    QLineEdit, QComboBox, QSpinBox {{ background: {c['base']}; border: 1px solid {c['border']};
        border-radius: 6px; padding: 4px 7px; color: {c['text']}; selection-background-color: {c['accent']}; }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border: 1px solid {c['accent']}; }}
    QComboBox::drop-down {{ border: 0; width: 18px; }}
    QDockWidget {{ color: {c['text']}; titlebar-close-icon: none; }}
    QDockWidget::title {{ background: {c['toolbar']}; padding: 7px 10px;
        border-bottom: 1px solid {c['border']}; }}
    QListWidget, QTreeWidget {{ background: {c['base']}; color: {c['text']};
        border: 1px solid {c['border']}; border-radius: 6px; outline: 0; }}
    QListWidget::item, QTreeWidget::item {{ padding: 3px; border-radius: 4px; }}
    QListWidget::item:selected, QTreeWidget::item:selected {{ background: {c['accent']};
        color: {c['accent_text']}; }}
    QTabBar::tab {{ background: transparent; color: {c['text']}; padding: 6px 14px;
        border-radius: 6px; margin: 2px; }}
    QTabBar::tab:selected {{ background: {c['accent']}; color: {c['accent_text']}; }}
    QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 5px; min-height: 36px; }}
    QScrollBar::handle:vertical:hover {{ background: {c['muted']}; }}
    QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
    QScrollBar::handle:horizontal {{ background: {c['border']}; border-radius: 5px; min-width: 36px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
    QSlider::groove:horizontal {{ height: 4px; background: {c['border']}; border-radius: 2px; }}
    QSlider::handle:horizontal {{ background: {c['accent']}; width: 14px; height: 14px;
        border-radius: 7px; margin: -6px 0; }}
    QToolTip {{ background: {c['base']}; color: {c['text']}; border: 1px solid {c['border']};
        padding: 4px 6px; }}
    QProgressDialog {{ background: {c['window']}; }}
    QWidget#welcomeCard {{ background: {c['base']}; border: 1px solid {c['border']};
        border-radius: 14px; }}
    """


def canvas_color(dark: bool) -> str:
    """ページ表示エリアの背景色（テーマ別）。"""
    return (_DARK if dark else _LIGHT)["canvas"]


def apply_theme(app: QApplication, dark: bool) -> None:
    """アプリ全体のテーマを切り替える。"""
    c = _DARK if dark else _LIGHT
    app.setStyle("Fusion")
    app.setPalette(_palette(c))
    app.setStyleSheet(_qss(c))
