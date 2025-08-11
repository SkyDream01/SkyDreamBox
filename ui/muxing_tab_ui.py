# -*- coding: utf-8 -*-
# SkyDreamBox/ui/muxing_tab_ui.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QGroupBox, QStyle
)
from PyQt5.QtCore import Qt

class Ui_MuxingTab:
    def setupUi(self, MuxingTab):
        main_layout = QVBoxLayout(MuxingTab)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 15, 10, 15)

        mux_group = QGroupBox("音视频合并")
        mux_layout = QVBoxLayout(mux_group)

        self.video_input_edit = QLineEdit()
        self.select_video_button = QPushButton("选择")
        self.select_video_button.setIcon(MuxingTab.style().standardIcon(QStyle.SP_DirOpenIcon))
        mux_layout.addLayout(self._create_hbox("视频:", self.video_input_edit, self.select_video_button))

        self.audio_input_edit = QLineEdit()
        self.select_audio_button = QPushButton("选择")
        self.select_audio_button.setIcon(MuxingTab.style().standardIcon(QStyle.SP_DirOpenIcon))
        mux_layout.addLayout(self._create_hbox("音频:", self.audio_input_edit, self.select_audio_button))

        self.subtitle_input_edit = QLineEdit()
        self.select_subtitle_button = QPushButton("选择")
        self.select_subtitle_button.setIcon(MuxingTab.style().standardIcon(QStyle.SP_FileIcon))
        mux_layout.addLayout(self._create_hbox("字幕:", self.subtitle_input_edit, self.select_subtitle_button))

        self.output_edit = QLineEdit()
        self.select_output_button = QPushButton("选择")
        self.select_output_button.setIcon(MuxingTab.style().standardIcon(QStyle.SP_DriveFDIcon))
        mux_layout.addLayout(self._create_hbox("输出:", self.output_edit, self.select_output_button))

        main_layout.addWidget(mux_group)

        self.run_button = QPushButton("开始合并")
        main_layout.addWidget(self.run_button, 0, Qt.AlignCenter)
        main_layout.addStretch()

    def _create_hbox(self, label_text, widget, button):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        layout.addWidget(label)
        layout.addWidget(widget)
        layout.addWidget(button)
        return layout