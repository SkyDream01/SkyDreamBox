# -*- coding: utf-8 -*-
# SkyDreamBox/ui/about_tab_ui.py

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGridLayout
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from constants import APP_NAME, APP_VERSION, AUTHOR, GITHUB_URL
from utils import resource_path

class Ui_AboutTab:
    def setupUi(self, AboutTab):
        # --- 主布局 ---
        main_layout = QVBoxLayout(AboutTab)
        
        # 1. 加大四周留白 (左, 上, 右, 下) - 原为 20
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # 2. 加大模块间的垂直间距 - 原为 10
        main_layout.setSpacing(30)
        
        # [核心修改] 移除 AlignTop，改用弹簧 (Stretch) 实现垂直居中
        # 顶部加一个弹簧，把内容往下顶
        main_layout.addStretch(1)

        # --- Logo 和标题区域 ---
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        # 内部元素间距也加大
        header_layout.setSpacing(20) 
        header_layout.setContentsMargins(0, 0, 0, 0)

        logo_label = QLabel()
        logo_path = resource_path("assets/logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # 稍微放大 Logo 尺寸 (80 -> 100)
            logo_label.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(APP_NAME)
        title_label.setObjectName("aboutTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 稍微加大字号和顶部外边距
        title_label.setStyleSheet("font-size: 20pt; font-weight: bold; color: #ffffff; margin-top: 5px;")

        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        main_layout.addWidget(header_widget)

        # --- 详细信息区域 ---
        info_widget = QWidget()
        info_layout = QGridLayout(info_widget)
        info_layout.setContentsMargins(20, 10, 20, 10)
        
        # 3. 加大网格内的行列间距 - 原为 15/12
        info_layout.setHorizontalSpacing(25)
        info_layout.setVerticalSpacing(20)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_layout.addWidget(self._create_info_label("版本:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        info_layout.addWidget(QLabel(APP_VERSION), 0, 1)

        info_layout.addWidget(self._create_info_label("作者:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        info_layout.addWidget(QLabel(AUTHOR), 1, 1)

        info_layout.addWidget(self._create_info_label("仓库:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        github_label = QLabel(f'<a href="{GITHUB_URL}" style="color:#1abc9c; text-decoration: none;">GitHub</a>')
        github_label.setOpenExternalLinks(True)
        info_layout.addWidget(github_label, 2, 1)

        info_layout.addWidget(self._create_info_label("描述:"), 3, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        description_label = QLabel("......")
        description_label.setWordWrap(True)
        description_label.setStyleSheet("line-height: 120%;") # 增加行高，防止多行文字挤在一起
        info_layout.addWidget(description_label, 3, 1, 1, 2)

        main_layout.addWidget(info_widget)

        # [核心修改] 底部加一个弹簧，与顶部弹簧配合，使内容垂直居中
        main_layout.addStretch(1)

    def _create_info_label(self, text):
        label = QLabel(text)
        label.setObjectName("infoLabel")
        label.setStyleSheet("font-weight: bold; color: #bdc3c7;")
        return label