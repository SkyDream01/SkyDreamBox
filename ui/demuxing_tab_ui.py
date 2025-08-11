# -*- coding: utf-8 -*-
# SkyDreamBox/ui/demuxing_tab_ui.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QGroupBox, QStyle
)
from PySide6.QtCore import Qt

class Ui_DemuxingTab:
    def setupUi(self, DemuxingTab):
        main_layout = QVBoxLayout(DemuxingTab)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 15, 10, 15)

        demux_group = QGroupBox("音视频分离")
        demux_layout = QVBoxLayout(demux_group)

        self.input_edit = QLineEdit()
        self.select_input_button = QPushButton("选择文件")
        self.select_input_button.setIcon(DemuxingTab.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        input_layout = QHBoxLayout()
        input_label = QLabel("输入文件:")
        input_label.setFixedWidth(70)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.select_input_button)
        demux_layout.addLayout(input_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        self.extract_video_button = QPushButton("仅视频")
        self.extract_audio_button = QPushButton("仅音频")
        buttons_layout.addWidget(self.extract_video_button)
        buttons_layout.addWidget(self.extract_audio_button)
        buttons_layout.addStretch()
        demux_layout.addLayout(buttons_layout)

        main_layout.addWidget(demux_group)
        main_layout.addStretch()