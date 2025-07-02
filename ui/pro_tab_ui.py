# -*- coding: utf-8 -*-
# SkyDreamBox/ui/pro_tab_ui.py

from PyQt5.QtWidgets import (
    QVBoxLayout, QPushButton, QLabel, QTextEdit
)
from PyQt5.QtCore import Qt

class Ui_ProfessionalTab:
    def setupUi(self, ProfessionalTab):
        layout = QVBoxLayout(ProfessionalTab)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 15, 10, 15)

        layout.addWidget(QLabel("在此处输入完整的FFmpeg命令 (程序会自动添加 `-nostdin` 和 `-loglevel verbose` 参数):"))
        self.command_input = QTextEdit()
        self.command_input.setPlaceholderText("例如: ffmpeg -i input.mp4 -c:v libx264 -crf 22 output.mp4")
        self.command_input.setObjectName("console") # Reuse console style
        layout.addWidget(self.command_input)

        self.run_button = QPushButton("执行命令")
        layout.addWidget(self.run_button, 0, Qt.AlignCenter)
        layout.addStretch()