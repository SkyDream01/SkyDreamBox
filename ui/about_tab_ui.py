# -*- coding: utf-8 -*-
# SkyDreamBox/ui/about_tab_ui.py

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGridLayout, QSizePolicy
)
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt

from constants import APP_NAME, APP_VERSION, AUTHOR, GITHUB_URL
from utils import resource_path

class Ui_AboutTab:
    def setupUi(self, AboutTab):
        """
        初始化关于页面的 UI 组件
        """
        # --- 主布局配置 ---
        main_layout = QVBoxLayout(AboutTab)
        # 设置四周留白 (左, 上, 右, 下) - 保持较宽的边距以获得更好的视觉效果
        main_layout.setContentsMargins(40, 40, 40, 40)
        # 设置模块间的垂直间距
        main_layout.setSpacing(30)
        
        # [布局策略] 顶部添加弹簧，配合底部弹簧实现内容的垂直居中
        main_layout.addStretch(1)

        # --- 1. 头部区域 (Logo + 标题) ---
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(20) 
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Logo设置
        logo_label = QLabel()
        logo_path = resource_path("assets/logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # 缩放 Logo 到 100x100，保持纵横比且平滑缩放
            scaled_pixmap = pixmap.scaled(
                100, 100, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
        
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 标题设置
        title_label = QLabel(APP_NAME)
        title_label.setObjectName("aboutTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 设置字体样式：20pt，加粗，白色，顶部微调
        title_label.setStyleSheet("font-size: 20pt; font-weight: bold; color: #ffffff; margin-top: 5px;")

        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        main_layout.addWidget(header_widget)

        # --- 2. 详细信息区域 (版本、作者、GitHub) ---
        info_widget = QWidget()
        info_layout = QGridLayout(info_widget)
        info_layout.setContentsMargins(20, 10, 20, 10)
        
        # 设置网格间距
        info_layout.setHorizontalSpacing(25)
        info_layout.setVerticalSpacing(20)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 辅助函数：快速创建左侧标签
        def create_label(text):
            lbl = QLabel(text)
            lbl.setObjectName("infoLabel")
            lbl.setStyleSheet("font-weight: bold; color: #bdc3c7;")
            return lbl

        # --- 信息行 ---
        
        # 版本
        info_layout.addWidget(create_label("版本:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        info_layout.addWidget(QLabel(APP_VERSION), 0, 1)

        # 作者
        info_layout.addWidget(create_label("作者:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        info_layout.addWidget(QLabel(AUTHOR), 1, 1)

        # 仓库链接
        info_layout.addWidget(create_label("仓库:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        github_link = f'<a href="{GITHUB_URL}" style="color:#1abc9c; text-decoration: none;">GitHub</a>'
        github_label = QLabel(github_link)
        github_label.setOpenExternalLinks(True)  # 允许点击打开浏览器
        github_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        info_layout.addWidget(github_label, 2, 1)

        # 描述 (支持自动换行)
        info_layout.addWidget(create_label("描述:"), 3, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        
        # 使用 HTML 格式增强描述文本的可读性和行高控制
        description_text = (
            "<p style='line-height: 140%; margin: 0;'>"
            "SkyDreamBox 是一个多功能媒体处理工具箱，<br>"
            "旨在简化视频封装、音频处理及其他常见任务。"
            "</p>"
        )
        description_label = QLabel(description_text)
        description_label.setWordWrap(True)
        # 允许水平方向扩展
        description_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # 占据第3行的第1列，跨1行，跨2列(如果有需要的话，这里目前是放在第2列)
        # 注意：原代码是 info_layout.addWidget(description_label, 3, 1, 1, 2)
        # 如果你希望描述文本占据右侧更宽的空间，可以保持 spanning
        info_layout.addWidget(description_label, 3, 1, 1, 2)

        main_layout.addWidget(info_widget)

        # [布局策略] 底部添加弹簧，确保内容在垂直方向居中显示
        main_layout.addStretch(1)