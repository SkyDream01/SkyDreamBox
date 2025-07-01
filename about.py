# -*- coding: utf-8 -*-
# SkyDreamBox/about.py

import os
import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QWidget, QGridLayout
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QPixmap, QDesktopServices

def resource_path(relative_path):
    """ 获取资源的绝对路径，兼容打包后的应用 """
    try:
        # PyInstaller 创建的临时文件夹
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AboutWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 天梦工具箱")
        self.setFixedSize(450, 400) # 调整了窗口大小以适应新布局

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Logo 和标题 ---
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0,0,0,0)
        
        logo_label = QLabel()
        logo_path = resource_path("assets/logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_label.setAlignment(Qt.AlignCenter)
        
        title_label = QLabel("天梦工具箱 (SkyDreamBox)")
        title_label.setObjectName("aboutTitle")
        title_label.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        main_layout.addWidget(header_widget)
        
        # --- 详细信息 ---
        info_widget = QWidget()
        info_layout = QGridLayout(info_widget)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setHorizontalSpacing(15)
        info_layout.setVerticalSpacing(12)

        # 创建并添加标签
        info_layout.addWidget(self._create_info_label("版本:"), 0, 0, Qt.AlignRight)
        info_layout.addWidget(QLabel("1.2"), 0, 1)

        info_layout.addWidget(self._create_info_label("作者:"), 1, 0, Qt.AlignRight)
        info_layout.addWidget(QLabel("Tensin"), 1, 1)

        info_layout.addWidget(self._create_info_label("仓库:"), 2, 0, Qt.AlignRight)
        github_label = QLabel('<a href="https://github.com/SkyDream01/SkyDreamBox">GitHub</a>')
        github_label.setOpenExternalLinks(True) # 允许打开外部链接
        info_layout.addWidget(github_label, 2, 1)
        
        info_layout.addWidget(self._create_info_label("描述:"), 3, 0, Qt.AlignRight | Qt.AlignTop)
        description_label = QLabel("一个基于 PyQt5 和 FFmpeg 构建的模块化音视频处理工具。")
        description_label.setWordWrap(True)
        info_layout.addWidget(description_label, 3, 1)
        
        main_layout.addWidget(info_widget)
        main_layout.addStretch()

        # --- 关闭按钮 ---
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.addWidget(close_button, 0, Qt.AlignCenter)
        main_layout.addWidget(button_container)

        self.setStyleSheet("""
            QDialog {
                background-color: #3c3c3c;
            }
            #aboutTitle {
                font-size: 16pt;
                font-weight: bold;
                color: #00aaff;
                padding-top: 5px;
            }
            QLabel {
                font-size: 10pt;
                color: #e0e0e0;
            }
            #infoLabel {
                font-weight: bold;
                color: #a0a0a0;
            }
            QPushButton {
                min-width: 120px;
            }
        """)

    def _create_info_label(self, text):
        label = QLabel(text)
        label.setObjectName("infoLabel")
        return label