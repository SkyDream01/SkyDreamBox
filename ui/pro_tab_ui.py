# -*- coding: utf-8 -*-
# SkyDreamBox/ui/pro_tab_ui.py

from PySide6.QtWidgets import (
    QVBoxLayout, QPushButton, QLabel, QTextEdit
)
from PySide6.QtCore import Qt

class Ui_ProfessionalTab:
    def setupUi(self, ProfessionalTab):
        layout = QVBoxLayout(ProfessionalTab)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 15, 10, 15)

        layout.addWidget(QLabel("直接输入FFmpeg命令 (程序会自动添加 `-nostdin` 和 `-loglevel verbose` 参数):"))
        self.command_input = QTextEdit()
        self.command_input.setPlaceholderText("示例: ffmpeg -i input.mp4 -c:v libx264 -crf 22 output.mp4")
        self.command_input.setObjectName("console") # Reuse console style
        layout.addWidget(self.command_input)

        self.run_button = QPushButton("执行")
        layout.addWidget(self.run_button, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()