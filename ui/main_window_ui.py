# -*- coding: utf-8 -*-
# SkyDreamBox/ui/main_window_ui.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QTextEdit,
    QProgressBar, QSplitter, QScrollArea, QMenuBar
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

class Ui_MainWindow:
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")

        self.central_widget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        # 创建垂直分割器
        self.splitter = QSplitter(Qt.Orientation.Vertical)

        # 1. 主功能选项卡区域
        self.tabs = QTabWidget()
        self.splitter.addWidget(self.tabs)

        # 2. 底部信息和控制台区域
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 2, 0, 0)

        self.info_console_tabs = QTabWidget()

        # 2a. 媒体文件信息 Tab
        info_scroll_area = QScrollArea()
        info_scroll_area.setWidgetResizable(True)
        info_scroll_area.setFixedHeight(120)
        self.info_label = QLabel("选择媒体文件以查看信息")
        self.info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.info_label.setObjectName("info_label")
        info_scroll_area.setWidget(self.info_label)
        self.info_console_tabs.addTab(info_scroll_area, "媒体信息")

        # 2b. FFmpeg 输出信息 Tab
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_layout.setSpacing(5)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setObjectName("console")

        # 进度条和状态标签
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("进度:"))
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        self.progress_status_label = QLabel("待机")
        self.progress_status_label.setMinimumWidth(220)
        progress_layout.addWidget(self.progress_status_label)
        progress_layout.setStretch(1, 1)

        console_layout.addWidget(self.console)
        console_layout.addLayout(progress_layout)
        self.info_console_tabs.addTab(console_widget, "FFmpeg 输出")

        bottom_layout.addWidget(self.info_console_tabs)
        self.splitter.addWidget(bottom_widget)

        # 设置分割器初始大小
        self.splitter.setSizes([550, 200])
        self.main_layout.addWidget(self.splitter)