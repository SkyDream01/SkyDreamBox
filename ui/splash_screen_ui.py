# -*- coding: utf-8 -*-
# SkyDreamBox/ui/splash_screen_ui.py

from PyQt5.QtWidgets import (
    QApplication, QSplashScreen, QWidget, QVBoxLayout, QLabel, QProgressBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

class CustomSplashScreen(QSplashScreen):
    """
    自定义启动画面，具有纯色背景和独立的Logo图标。
    """
    def __init__(self, icon_pixmap: QPixmap, version="", width=450, height=350):
        # 创建一个透明的父级Pixmap，因为我们将通过样式表控制背景
        super().__init__(QPixmap(width, height))
        self.setWindowFlag(Qt.FramelessWindowHint) # 确保无边框

        self.version = version
        
        # 创建一个将容纳所有UI元素的中央小部件
        self.container = QWidget(self)
        self.container.setFixedSize(width, height)
        self.container.setObjectName("splashContainer")
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # --- 1. Logo 图标 ---
        icon_label = QLabel()
        # 将传入的pixmap缩放为合适的图标尺寸
        icon_label.setPixmap(icon_pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        
        # --- 2. 标题和版本号 ---
        title_label = QLabel("天梦工具箱")
        title_label.setObjectName("splashTitle")
        title_label.setAlignment(Qt.AlignCenter)
        
        version_label = QLabel(f"版本 {self.version}")
        version_label.setObjectName("splashVersion")
        version_label.setAlignment(Qt.AlignCenter)

        # --- 3. 状态信息和进度条 ---
        self.message_label = QLabel("正在启动...")
        self.message_label.setObjectName("splashMessage")
        self.message_label.setAlignment(Qt.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("splashProgressBar")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # --- 将所有组件添加到布局中 ---
        layout.addStretch(2)
        layout.addWidget(icon_label)
        layout.addSpacing(10)
        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addStretch(3)
        layout.addWidget(self.message_label)
        layout.addWidget(self.progress_bar)
        layout.addStretch(1)

        # --- 4. 应用样式表 ---
        self.container.setStyleSheet("""
            #splashContainer {
                background-color: #34495e;
                border-radius: 8px; /* 轻微的圆角 */
            }
            #splashTitle {
                font-size: 26pt;
                font-weight: bold;
                color: #ffffff;
            }
            #splashVersion {
                font-size: 10pt;
                color: #bdc3c7;
                padding-bottom: 20px;
            }
            #splashMessage {
                font-size: 9pt;
                color: #ecf0f1;
            }
            #splashProgressBar {
                min-height: 4px;
                max-height: 4px;
                border-radius: 2px;
                background-color: #2c3e50; /* 进度条背景色 */
            }
            #splashProgressBar::chunk {
                background-color: #1abc9c;
                border-radius: 2px;
            }
        """)

    def showMessage(self, message, alignment=Qt.AlignLeft, color=Qt.black):
        self.message_label.setText(message)
        QApplication.processEvents()

    def setProgress(self, value):
        self.progress_bar.setValue(value)
        QApplication.processEvents()