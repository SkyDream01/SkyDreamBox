"""Material Design 3 light theme. Tonal surfaces and blue semantic color roles."""

from utils import resource_path


STYLESHEET = """
QWidget {
    color: #1a1c20;
    font-family: 'Microsoft YaHei UI';
    font-size: 10pt;
}
QMainWindow, QDialog, QWidget#workArea { background: #f9f9ff; }
QWidget#sidebar { background: #eff0f7; border: 0; }
QWidget#sidebar QLabel#brand { color: #1a1c20; font-size: 15pt; font-weight: 700; }
QWidget#sidebar QLabel#muted { color: #44474f; font-size: 8pt;  }
QLabel#sidebarSection { color: #44474f; font-size: 8pt; font-weight: 600; }
QLabel#title { font-size: 24pt; font-weight: 400; color: #1a1c20; }
QLabel#sectionTitle { color: #1a1c20; font-size: 11pt; font-weight: 700; }
QLabel#muted { color: #44474f; font-size: 9pt; }
QLabel#engineBadge { border: 1px solid transparent; color: #294777; background: #d7e3ff; border-radius: 20px; padding: 7px 12px; font-size: 9pt; }
QLabel#notification { background: #d7e3ff; color: #001b3f; border: 1px solid #d7e3ff; border-radius: 8px; padding: 9px; }
QWidget#card { background: #ffffff; border: 1px solid #ffffff; border-radius: 20px; }
QListWidget#navigation { background: transparent; border: 0; outline: 0; color: #44474f; }
QListWidget#navigation::item { padding: 15px 16px; border-radius: 24px; border: 1px solid transparent; }
QListWidget#navigation::item:hover { background: #e3e5ed; color: #1a1c20; }
QListWidget#navigation::item:selected { background: #dce2f0; color: #151c2b; border: 1px solid #dce2f0; font-weight: 600; }
QListWidget#navigation:focus { border: 0; }
QWidget#sidebar QPushButton { background: transparent; color: #44474f; border: 1px solid #eff0f7; text-align: left; padding-left: 14px; }
QWidget#sidebar QPushButton:hover, QWidget#sidebar QPushButton:checked { background: #dce2f0; color: #151c2b; border-color: #dce2f0; }
QWidget#sidebar QPushButton:focus { border-color: #435e91; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit, QListWidget, QTableWidget {
    background: #f2f3fa; border: 1px solid #74777f; border-radius: 7px;
    selection-background-color: #d7e3ff; selection-color: #001b3f;
    alternate-background-color: #f2f3fa;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { padding: 6px 8px; min-height: 20px; }
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover { border-color: #44474f; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPushButton:focus, QPlainTextEdit:focus, QTextEdit:focus, QListWidget:focus, QTableWidget:focus { border: 1px solid #435e91; }
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { background: #e3e2e6; color: #76777c; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 28px; border: 0; }
QComboBox { combobox-popup: 0; padding-right: 32px; }
QComboBox QAbstractItemView {
    background: #ffffff; color: #1a1c20; border: 1px solid #74777f;
    border-radius: 6px; padding: 4px; outline: 0;
    selection-background-color: #dce2f0; selection-color: #294777;
}
QComboBox QAbstractItemView::item {
    min-height: 30px; padding: 3px 10px; margin: 2px;
    border: 0; border-radius: 4px;
}
QComboBox QAbstractItemView::item:selected { background: #dce2f0; color: #294777; }
QComboBox QAbstractItemView::item:hover { background: #e7e8ef; }
QPushButton { background: #ffffff; color: #435e91; border: 1px solid #74777f; border-radius: 18px; padding: 7px 14px; min-height: 20px; font-weight: 500; }
QPushButton:hover { background: #e7e8ef; border-color: #435e91; color: #294777; }
QPushButton:pressed { background: #d7e3ff; }
QPushButton:checked { background: #dce2f0; color: #151c2b; border-color: #dce2f0; }
QPushButton:disabled { color: #76777c; background: #e3e2e6; border-color: #e3e2e6; }
QPushButton#primary { background: #435e91; color: white; border: 1px solid #435e91; font-weight: 600; }
QPushButton#primary:hover { background: #4f6999; border-color: #4f6999; }
QPushButton#primary:pressed { background: #5b73a0; }
QPushButton#primary:focus { border: 2px solid #001b3f; padding: 6px 11px; }
QPushButton#primary:disabled { background: #e3e2e6; border-color: #e3e2e6; color: #76777c; }
QTableWidget { border: 0; background: #ffffff; gridline-color: #e7e8ef; }
QTableWidget::item { padding: 6px; border-bottom: 1px solid #e7e8ef; }
QTableWidget::item:selected { background: #dce2f0; color: #151c2b; }
QHeaderView::section { background: #eff0f7; color: #44474f; padding: 9px 6px; border: 0; border-bottom: 1px solid #e7e8ef; font-size: 9pt; }
QGroupBox { border: 1px solid #cac4d0; border-radius: 8px; margin-top: 12px; padding: 12px; background: #f2f3fa; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; color: #44474f; }
QScrollArea { border: 0; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollArea QWidget#card { background: #ffffff; }
QSplitter::handle { background: transparent; }
QSplitter::handle:hover { background: #d7e3ff; border-radius: 3px; }
QSplitter::handle:horizontal { width: 12px; }
QSplitter::handle:vertical { height: 12px; }
QTabWidget::pane { background: white; border: 1px solid #e7e8ef; border-radius: 7px; }
QTabBar::tab { background: #eff0f7; padding: 9px 12px; border: 0; }
QTabBar::tab:selected { background: white; color: #435e91; }
QCheckBox, QRadioButton { spacing: 8px; min-height: 28px; }
QCheckBox:disabled, QRadioButton:disabled { color: #76777c; }
QCheckBox::indicator, QGroupBox::indicator { width: 18px; height: 18px; }
QRadioButton::indicator { width: 18px; height: 18px; }
QLabel#preview { background: #1a1c20; color: #e3e2e6; border-radius: 16px; }
QLabel#aboutTitle, QLabel#splashTitle { font-size: 24pt; font-weight: 400; color: #1a1c20; }
QLabel#infoLabel { color: #44474f; font-weight: 600; }
QLabel#warning { color: #7d5260; background: #ffd8e4; border-radius: 8px; padding: 8px; }
QWidget#splashContainer { background: #eff0f7; border-radius: 28px; }
QLabel#splashVersion, QLabel#splashMessage { color: #44474f; }
QProgressBar { border: 0; background: #d7e3ff; border-radius: 4px; min-height: 8px; text-align: center; color: #001b3f; }
QProgressBar::chunk { background: #435e91; border-radius: 4px; }
QMenu, QMenuBar { background: #eff0f7; color: #1a1c20; padding: 4px; }
QMenu::item { padding: 10px 24px; border-radius: 8px; }
QMenu::item:selected, QMenuBar::item:selected { background: #dce2f0; }
QMenu::separator { height: 1px; background: #c4c6d0; margin: 4px 12px; }
QTabBar::tab:selected { border-bottom: 3px solid #435e91; }
QTabBar::tab:hover { background: #e7e8ef; }
QTextEdit#console, QPlainTextEdit#console { font-family: 'Cascadia Code', 'Consolas'; }
QCheckBox:focus, QRadioButton:focus { color: #435e91; }

QToolTip { background: #1a1c20; color: white; border: 0; padding: 6px; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #c4c6d0; border-radius: 4px; min-height: 28px; }
QScrollBar::handle:vertical:hover { background: #74777f; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: transparent; height: 8px; margin: 0; }
QScrollBar::handle:horizontal { background: #c4c6d0; border-radius: 4px; min-width: 28px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
QSlider::groove:horizontal { height: 4px; background: #d7e3ff; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #435e91; border-radius: 2px; }
QSlider::handle:horizontal { background: #435e91; border: 2px solid white; width: 12px; margin: -6px 0; border-radius: 8px; }
"""

# Resolve bundled assets for both source runs and the standalone application.
STYLESHEET += """
QComboBox::down-arrow { image: url("EXPAND"); width: 16px; height: 16px; }
QCheckBox::indicator, QGroupBox::indicator {
    width: 16px; height: 16px; border: 2px solid #74777f;
    border-radius: 3px; background: transparent;
}
QCheckBox::indicator:checked, QGroupBox::indicator:checked {
    background: #435e91; border-color: #435e91; image: url("CHECK");
}
QCheckBox::indicator:indeterminate { background: #435e91; border-color: #435e91; image: url("MINUS"); }
QCheckBox::indicator:hover, QGroupBox::indicator:hover { border-color: #435e91; }
QCheckBox::indicator:disabled, QGroupBox::indicator:disabled { border-color: #c4c6d0; background: #e3e2e6; }
QRadioButton::indicator { border: 2px solid #74777f; border-radius: 10px; background: transparent; }
QRadioButton::indicator:checked { border: 5px solid #435e91; width: 12px; height: 12px; background: white; }
""".replace("EXPAND", resource_path("assets/material/expand.svg").replace("\\", "/")).replace(
    "CHECK", resource_path("assets/material/check.svg").replace("\\", "/")
).replace("MINUS", resource_path("assets/material/minus.svg").replace("\\", "/"))
