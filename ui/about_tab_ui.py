# -*- coding: utf-8 -*-
# SkyDreamBox/ui/about_tab_ui.py

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGridLayout
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from constants import APP_NAME, APP_VERSION, AUTHOR, GITHUB_URL
from utils import resource_path

class Ui_AboutTab:
    def setupUi(self, AboutTab):
        main_layout = QVBoxLayout(AboutTab)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignTop)

        # --- Logo 和标题 ---
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        logo_label = QLabel()
        logo_path = resource_path("assets/logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_label.setAlignment(Qt.AlignCenter)

        title_label = QLabel(APP_NAME)
        title_label.setObjectName("aboutTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #ffffff;")

        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        main_layout.addWidget(header_widget)

        # --- 详细信息 ---
        info_widget = QWidget()
        info_layout = QGridLayout(info_widget)
        info_layout.setContentsMargins(10, 20, 10, 10)
        info_layout.setHorizontalSpacing(15)
        info_layout.setVerticalSpacing(12)
        info_layout.setAlignment(Qt.AlignCenter)

        info_layout.addWidget(self._create_info_label("版本:"), 0, 0, Qt.AlignRight)
        info_layout.addWidget(QLabel(APP_VERSION), 0, 1)

        info_layout.addWidget(self._create_info_label("作者:"), 1, 0, Qt.AlignRight)
        info_layout.addWidget(QLabel(AUTHOR), 1, 1)

        info_layout.addWidget(self._create_info_label("仓库:"), 2, 0, Qt.AlignRight)
        github_label = QLabel(f'<a href="{GITHUB_URL}" style="color:#1abc9c;">GitHub</a>')
        github_label.setOpenExternalLinks(True)
        info_layout.addWidget(github_label, 2, 1)

        info_layout.addWidget(self._create_info_label("描述:"), 3, 0, Qt.AlignRight | Qt.AlignTop)
        description_label = QLabel("一个基于 PyQt5 和 FFmpeg 构建的模块化音视频处理工具。")
        description_label.setWordWrap(True)
        info_layout.addWidget(description_label, 3, 1, 1, 2)  # Span across 2 columns

        main_layout.addWidget(info_widget)
        main_layout.addStretch()

    def _create_info_label(self, text):
        label = QLabel(text)
        label.setObjectName("infoLabel")
        label.setStyleSheet("font-weight: bold; color: #bdc3c7;")
        return label