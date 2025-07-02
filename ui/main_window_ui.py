# -*- coding: utf-8 -*-
# SkyDreamBox/ui/main_window_ui.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QTextEdit,
    QProgressBar, QSplitter, QScrollArea, QAction, QMenuBar
)
from PyQt5.QtCore import Qt

class Ui_MainWindow:
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")

        # 创建菜单栏
        self._create_menu_bar(MainWindow)

        self.central_widget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5) # MODIFIED

        # 创建垂直分割器
        self.splitter = QSplitter(Qt.Vertical)

        # 1. 主功能选项卡区域
        self.tabs = QTabWidget()
        self.splitter.addWidget(self.tabs)

        # 2. 底部信息和控制台区域
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 2, 0, 0) # MODIFIED

        self.info_console_tabs = QTabWidget()

        # 2a. 媒体文件信息 Tab
        info_scroll_area = QScrollArea()
        info_scroll_area.setWidgetResizable(True)
        # --- MODIFIED: Reduced height ---
        info_scroll_area.setFixedHeight(120) # MODIFIED
        self.info_label = QLabel("请选择一个媒体文件以查看信息...")
        self.info_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignTop)
        self.info_label.setObjectName("info_label")
        info_scroll_area.setWidget(self.info_label)
        self.info_console_tabs.addTab(info_scroll_area, "媒体文件信息")

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
        progress_layout.addWidget(QLabel("处理进度:"))
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        self.progress_status_label = QLabel("待命")
        self.progress_status_label.setMinimumWidth(220) # MODIFIED
        progress_layout.addWidget(self.progress_status_label)
        progress_layout.setStretch(1, 1)

        console_layout.addWidget(self.console)
        console_layout.addLayout(progress_layout)
        self.info_console_tabs.addTab(console_widget, "FFmpeg 输出信息")

        bottom_layout.addWidget(self.info_console_tabs)
        self.splitter.addWidget(bottom_widget)

        # 设置分割器初始大小
        self.splitter.setSizes([550, 200]) # MODIFIED
        self.main_layout.addWidget(self.splitter)

    def _create_menu_bar(self, MainWindow):
        # QMainWindow 会自动创建 menuBar，我们只需获取并添加菜单
        menu_bar = MainWindow.menuBar()
        help_menu = menu_bar.addMenu("帮助")
        self.about_action = QAction("关于", MainWindow)
        help_menu.addAction(self.about_action)