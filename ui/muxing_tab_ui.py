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

        mux_group = QGroupBox("封装 (合并音视频)")
        mux_layout = QVBoxLayout(mux_group)

        self.video_input_edit = QLineEdit()
        self.select_video_button = QPushButton("选择视频")
        self.select_video_button.setIcon(MuxingTab.style().standardIcon(QStyle.SP_DirOpenIcon))
        mux_layout.addLayout(self._create_hbox("视频文件:", self.video_input_edit, self.select_video_button))

        self.audio_input_edit = QLineEdit()
        self.select_audio_button = QPushButton("选择音频")
        self.select_audio_button.setIcon(MuxingTab.style().standardIcon(QStyle.SP_DirOpenIcon))
        mux_layout.addLayout(self._create_hbox("音频文件:", self.audio_input_edit, self.select_audio_button))

        self.subtitle_input_edit = QLineEdit()
        self.select_subtitle_button = QPushButton("选择字幕")
        self.select_subtitle_button.setIcon(MuxingTab.style().standardIcon(QStyle.SP_FileIcon))
        mux_layout.addLayout(self._create_hbox("字幕文件:", self.subtitle_input_edit, self.select_subtitle_button))

        self.output_edit = QLineEdit()
        self.select_output_button = QPushButton("选择输出")
        # --- FIX ---
        self.select_output_button.setIcon(MuxingTab.style().standardIcon(QStyle.SP_DriveFDIcon))
        mux_layout.addLayout(self._create_hbox("输出文件:", self.output_edit, self.select_output_button))

        main_layout.addWidget(mux_group)

        self.run_button = QPushButton("开始封装")
        main_layout.addWidget(self.run_button, 0, Qt.AlignCenter)
        main_layout.addStretch()

    def _create_hbox(self, label_text, widget, button):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(70)
        layout.addWidget(label)
        layout.addWidget(widget)
        layout.addWidget(button)
        return layout