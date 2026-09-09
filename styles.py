"""Shared light theme. Native Qt focus/keyboard semantics remain intact."""

STYLESHEET = """
QWidget {
    color: #243248;
    font-family: 'Microsoft YaHei UI', 'Microsoft YaHei', 'Segoe UI';
    font-size: 10pt;
}
QMainWindow, QDialog { background: #f4f6fa; }
QWidget#sidebar { background: #eaf0f8; border-right: 1px solid #dae2ef; }
QLabel#brand { color: #215ed3; font-size: 14pt; font-weight: 700; }
QLabel#title { font-size: 22pt; font-weight: 700; color: #14243c; }
QLabel#muted { color: #63758d; font-size: 9pt; }
QLabel#notification { background: #e8f0ff; color: #204f9e; border: 1px solid #cbdcfa; border-radius: 6px; padding: 8px; }
QListWidget#navigation { background: transparent; border: 0; outline: 0; }
QListWidget#navigation::item { padding: 13px 8px; margin: 3px 0; border-radius: 7px; }
QListWidget#navigation::item:selected { background: #d7e5ff; color: #175ac9; font-weight: 600; }
QListWidget#navigation::item:hover { background: #e0e9f7; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit, QListWidget, QTableWidget {
    background: white; border: 1px solid #dce3ee; border-radius: 5px;
    selection-background-color: #dce9ff; selection-color: #173e78;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { padding: 6px; min-height: 20px; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPushButton:focus { border: 1px solid #367bf0; }
QLineEdit:disabled, QComboBox:disabled { background: #edf0f5; color: #8793a5; }
QComboBox QAbstractItemView { background: white; color: #243248; selection-background-color: #dce9ff; }
QPushButton { background: white; border: 1px solid #d3ddeb; border-radius: 5px; padding: 7px 10px; min-height: 19px; }
QPushButton:hover { background: #edf3ff; border-color: #9ab8ef; }
QPushButton:pressed { background: #dae8ff; }
QPushButton:checked { background: #d7e5ff; color: #175ac9; border-color: #bed2f5; }
QPushButton:disabled { color: #929cab; background: #eef1f5; }
QPushButton#primary { background: #2869df; color: white; border: 1px solid #2869df; font-weight: 600; }
QPushButton#primary:hover { background: #1859c9; }
QTableWidget { gridline-color: #eff2f7; }
QTableWidget::item { padding: 5px; }
QHeaderView::section { background: #f0f4fa; color: #60728a; padding: 7px; border: 0; border-bottom: 1px solid #dce3ee; }
QGroupBox { border: 1px solid #dce3ee; border-radius: 7px; margin-top: 12px; padding: 12px; background: #fafcff; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #496381; }
QScrollArea { border: 0; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QSplitter::handle { background: #e6ebf3; }
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:vertical { height: 3px; }
QTabWidget::pane { border: 1px solid #dce3ee; border-radius: 5px; }
QTabBar::tab { background: #e9eef6; padding: 8px 12px; border: 0; }
QTabBar::tab:selected { background: white; color: #215ed3; }
QCheckBox { spacing: 6px; }
QToolTip { background: #243248; color: white; border: 0; padding: 5px; }
QScrollBar:vertical { background: #f0f3f8; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #c5d0df; border-radius: 4px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""
