# -*- coding: utf-8 -*-
# SkyDreamBox/ui/demuxing_tab_ui.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QGroupBox, QStyle
)
from PyQt5.QtCore import Qt

class Ui_DemuxingTab:
    def setupUi(self, DemuxingTab):
        main_layout = QVBoxLayout(DemuxingTab)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 15, 10, 15)

        demux_group = QGroupBox("抽取音/视频")
        demux_layout = QVBoxLayout(demux_group)

        self.input_edit = QLineEdit()
        self.select_input_button = QPushButton("选择文件")
        self.select_input_button.setIcon(DemuxingTab.style().standardIcon(QStyle.SP_DirOpenIcon))
        input_layout = QHBoxLayout()
        input_label = QLabel("输入文件:")
        input_label.setFixedWidth(70)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.select_input_button)
        demux_layout.addLayout(input_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        self.extract_video_button = QPushButton("仅抽取视频流")
        self.extract_audio_button = QPushButton("仅抽取音频流")
        buttons_layout.addWidget(self.extract_video_button)
        buttons_layout.addWidget(self.extract_audio_button)
        buttons_layout.addStretch()
        demux_layout.addLayout(buttons_layout)

        main_layout.addWidget(demux_group)
        main_layout.addStretch()