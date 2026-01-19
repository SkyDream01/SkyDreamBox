# -*- coding: utf-8 -*-
# SkyDreamBox/styles.py

# =============================================================================
# Stylesheet
# =============================================================================
STYLESHEET = """
/* Material Design Dark Theme for SkyDreamBox */
QWidget {
    background-color: #121212; /* Material Dark background */
    color: #FFFFFF; /* Primary text */
    font-family: 'Segoe UI', 'Microsoft YaHei', 'Arial';
    font-size: 9pt;
}
QMainWindow, QDialog {
    background-color: #121212;
    border: none;
}
QGroupBox {
    background-color: #1E1E1E; /* Surface color */
    border: 1px solid #333333;
    border-radius: 8px;
    margin-top: 1ex;
    padding: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 4px 12px;
    background-color: #2196F3; /* Primary blue */
    color: #000000;
    border-radius: 6px;
    font-weight: bold;
}
QTabWidget::pane {
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 4px;
    background-color: #1E1E1E;
}
QTabBar::tab {
    background: #1E1E1E;
    border: 1px solid #333333;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    min-width: 8ex;
    padding: 8px 16px;
    margin-right: 2px;
    color: #B3B3B3; /* Secondary text */
}
QTabBar::tab:selected, QTabBar::tab:hover {
    background: #2196F3; /* Primary blue */
    color: #000000;
    font-weight: bold;
}
QTabBar::tab:selected {
    border-color: #2196F3;
}
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #2C2C2C;
    border: 1px solid #333333;
    padding: 8px;
    border-radius: 6px;
    color: #FFFFFF;
    selection-background-color: #2196F3;
    selection-color: #000000;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #2196F3;
    padding: 7px; /* Adjust padding to maintain size */
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: #333333;
    border-left-style: solid;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    background-color: #2C2C2C;
}
QComboBox QAbstractItemView {
    background-color: #2C2C2C;
    selection-background-color: #2196F3;
    selection-color: #000000;
    border-radius: 6px;
    color: #FFFFFF;
    border: 1px solid #333333;
}
QPushButton {
    background-color: #2196F3; /* Primary blue */
    color: #000000;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    min-width: 90px;
    font-weight: bold;
    font-size: 9pt;
}
QPushButton:hover {
    background-color: #64B5F6; /* Lighter blue */
}
QPushButton:pressed {
    background-color: #1976D2; /* Darker blue */
}
QPushButton:disabled {
    background-color: #424242;
    color: #666666;
}
QProgressBar {
    border: 1px solid #333333;
    border-radius: 8px;
    text-align: center;
    background-color: #2C2C2C;
    color: #FFFFFF;
    font-weight: bold;
    height: 20px;
}
QProgressBar::chunk {
    background-color: #03A9F4; /* Secondary blue */
    border-radius: 7px;
}
QLabel {
    background-color: transparent;
    color: #FFFFFF;
}
#info_label {
    background-color: #1E1E1E;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #333333;
    color: #B3B3B3;
}
#console {
    background-color: #0A0A0A;
    color: #03A9F4; /* Console text blue */
    font-family: 'Consolas', 'Courier New', monospace;
    border-radius: 8px;
    padding: 8px;
}
QSplitter::handle {
    background-color: #333333;
}
QSplitter::handle:hover {
    background-color: #424242;
}
QSplitter::handle:vertical {
    height: 3px;
}
QSplitter::handle:horizontal {
    width: 3px;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QMenuBar {
    background-color: #1E1E1E;
    color: #FFFFFF;
}
QMenuBar::item {
    padding: 6px 12px;
    background: transparent;
    color: #FFFFFF;
}
QMenuBar::item:selected {
    background: #2196F3;
    color: #000000;
    border-radius: 4px;
}
QMenu {
    background-color: #2C2C2C;
    border: 1px solid #333333;
    border-radius: 6px;
    color: #FFFFFF;
}
QMenu::item:selected {
    background-color: #2196F3;
    color: #000000;
    border-radius: 4px;
}
QCheckBox, QRadioButton {
    color: #FFFFFF;
    spacing: 8px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 2px solid #666666;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #2196F3;
    border-color: #2196F3;
}
QScrollBar:vertical, QScrollBar:horizontal {
    background-color: #1E1E1E;
    border-radius: 4px;
    width: 12px;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background-color: #424242;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background-color: #666666;
}
QScrollBar::add-line, QScrollBar::sub-line {
    background: none;
}
QToolTip {
    background-color: #2C2C2C;
    color: #FFFFFF;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 6px;
}
"""
