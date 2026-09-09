"""Sky-inspired workbench theme with a quiet canvas and a dark navigation rail."""

STYLESHEET = """
QWidget {
    color: #253650;
    font-family: 'Microsoft YaHei UI', 'Microsoft YaHei', 'Segoe UI';
    font-size: 10pt;
}
QMainWindow, QDialog, QWidget#workArea { background: #f1f5fa; }
QWidget#sidebar { background: #101e36; border: 0; }
QWidget#sidebar QLabel#brand { color: #f4f8ff; font-size: 15pt; font-weight: 700; }
QWidget#sidebar QLabel#muted { color: #9bacc6; font-size: 8pt; line-height: 1.5; }
QLabel#sidebarSection { color: #7187a8; font-size: 8pt; font-weight: 600; }
QLabel#title { font-size: 24pt; font-weight: 700; color: #172943; }
QLabel#sectionTitle { color: #203754; font-size: 11pt; font-weight: 700; }
QLabel#muted { color: #73839a; font-size: 9pt; }
QLabel#engineBadge { color: #476888; background: #e5edf7; border-radius: 12px; padding: 7px 12px; font-size: 9pt; }
QLabel#notification { background: #e8f2ff; color: #245a99; border: 1px solid #c4dcf7; border-radius: 8px; padding: 9px; }
QWidget#card { background: #ffffff; border: 1px solid #dde5ef; border-radius: 12px; }
QListWidget#navigation { background: transparent; border: 0; outline: 0; color: #adbed6; }
QListWidget#navigation::item { padding: 13px 12px; border-radius: 8px; border: 1px solid transparent; }
QListWidget#navigation::item:hover { background: #1c304e; color: #ffffff; }
QListWidget#navigation::item:selected { background: #284975; color: #ffffff; border: 1px solid #365e8f; font-weight: 600; }
QListWidget#navigation::item:focus { border: 1px solid #87bfff; }
QWidget#sidebar QPushButton { background: transparent; color: #aebfd8; border: 1px solid #2b3d59; text-align: left; padding-left: 14px; }
QWidget#sidebar QPushButton:hover, QWidget#sidebar QPushButton:checked { background: #284975; color: white; border-color: #4775a8; }
QWidget#sidebar QPushButton:focus { border-color: #87bfff; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit, QListWidget, QTableWidget {
    background: #f8fafd; border: 1px solid #dfe6ef; border-radius: 7px;
    selection-background-color: #dcecff; selection-color: #194f8e;
    alternate-background-color: #f3f7fc;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { padding: 6px 8px; min-height: 20px; }
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover { border-color: #aabed8; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPushButton:focus, QPlainTextEdit:focus, QTextEdit:focus, QListWidget:focus, QTableWidget:focus { border: 1px solid #428ce8; }
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { background: #edf1f6; color: #8793a5; }
QComboBox { combobox-popup: 0; padding-right: 32px; }
QComboBox QAbstractItemView {
    background: #ffffff; color: #253650; border: 1px solid #d8e2ee;
    border-radius: 6px; padding: 4px; outline: 0;
    selection-background-color: #e7f1ff; selection-color: #195cae;
}
QComboBox QAbstractItemView::item {
    min-height: 30px; padding: 3px 10px; margin: 2px;
    border: 0; border-radius: 4px;
}
QComboBox QAbstractItemView::item:selected { background: #e7f1ff; color: #195cae; }
QComboBox QAbstractItemView::item:hover { background: #f0f6ff; }
QPushButton { background: #ffffff; border: 1px solid #d8e2ee; border-radius: 7px; padding: 7px 12px; min-height: 19px; }
QPushButton:hover { background: #eef6ff; border-color: #9bbfeb; color: #195cae; }
QPushButton:pressed { background: #dcecff; }
QPushButton:checked { background: #e3efff; color: #175ac9; border-color: #a5c5ef; }
QPushButton:disabled { color: #929cab; background: #eef1f5; border-color: #e0e5ed; }
QPushButton#primary { background: #2875df; color: white; border: 1px solid #2875df; font-weight: 600; }
QPushButton#primary:hover { background: #1b64c8; border-color: #1b64c8; }
QPushButton#primary:pressed { background: #1552a7; }
QPushButton#primary:focus { border: 2px solid #91c5ff; padding: 6px 11px; }
QPushButton#primary:disabled { background: #adc8ec; border-color: #adc8ec; color: #f5f8fd; }
QTableWidget { background: #fbfcfe; gridline-color: #eff2f7; }
QTableWidget::item { padding: 6px; border-bottom: 1px solid #edf2f8; }
QTableWidget::item:selected { background: #e2efff; color: #1a4c88; }
QHeaderView::section { background: #eef3f9; color: #637791; padding: 9px 6px; border: 0; border-bottom: 1px solid #dfe7f1; font-size: 9pt; }
QGroupBox { border: 1px solid #e0e7f0; border-radius: 8px; margin-top: 12px; padding: 12px; background: #f8fafd; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; color: #496381; }
QScrollArea { border: 0; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QSplitter::handle { background: transparent; }
QSplitter::handle:hover { background: #c8dcf4; border-radius: 3px; }
QSplitter::handle:horizontal { width: 12px; }
QSplitter::handle:vertical { height: 12px; }
QTabWidget::pane { background: white; border: 1px solid #dce3ee; border-radius: 7px; }
QTabBar::tab { background: #e8eef7; padding: 9px 12px; border: 0; }
QTabBar::tab:selected { background: white; color: #215ed3; }
QCheckBox { spacing: 7px; }
QToolTip { background: #203754; color: white; border: 0; padding: 6px; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #c2cede; border-radius: 4px; min-height: 28px; }
QScrollBar::handle:vertical:hover { background: #91a9c7; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: transparent; height: 8px; margin: 0; }
QScrollBar::handle:horizontal { background: #c2cede; border-radius: 4px; min-width: 28px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
QSlider::groove:horizontal { height: 4px; background: #dae4f0; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #428ce8; border-radius: 2px; }
QSlider::handle:horizontal { background: #2875df; border: 2px solid white; width: 12px; margin: -6px 0; border-radius: 8px; }
"""
