# -*- coding: utf-8 -*-
# SkyDreamBox/ui/video_tab_ui.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QGroupBox, QComboBox, QGridLayout, QStyle
)
from PyQt5.QtCore import Qt

class Ui_VideoTab:
    def setupUi(self, VideoTab):
        main_layout = QVBoxLayout(VideoTab)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # --- 输入输出组 ---
        io_group = QGroupBox("输入输出")
        io_layout = QVBoxLayout(io_group)

        self.input_edit = QLineEdit()
        self.select_input_button = QPushButton("选择")
        self.select_input_button.setIcon(VideoTab.style().standardIcon(QStyle.SP_DirOpenIcon))
        io_layout.addLayout(self._create_hbox("输入:", self.input_edit, self.select_input_button))

        self.output_edit = QLineEdit()
        self.select_output_button = QPushButton("选择")
        self.select_output_button.setIcon(VideoTab.style().standardIcon(QStyle.SP_DriveFDIcon))
        io_layout.addLayout(self._create_hbox("输出:", self.output_edit, self.select_output_button))
        main_layout.addWidget(io_group)

        # --- 操作设置组 ---
        options_group = QGroupBox("参数设置")
        options_layout = QVBoxLayout(options_group)

        # 格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("格式:"))
        self.format_combo = QComboBox()
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        options_layout.addLayout(format_layout)

        # 视频
        video_group = QGroupBox("视频")
        video_layout = QVBoxLayout(video_group)
        codec_v_layout = QHBoxLayout()
        codec_v_layout.addWidget(QLabel("视频编码:"))
        self.video_codec_combo = QComboBox()
        codec_v_layout.addWidget(self.video_codec_combo)
        codec_v_layout.addStretch()

        video_grid = QGridLayout()
        video_grid.setSpacing(10)
        self.crf_edit = QLineEdit(); self.crf_edit.setPlaceholderText("推荐: 23")
        self.cq_edit = QLineEdit(); self.cq_edit.setPlaceholderText("推荐: 23")
        self.fps_edit = QLineEdit(); self.fps_edit.setPlaceholderText("选填")
        self.resolution_edit = QLineEdit(); self.resolution_edit.setPlaceholderText("选填")
        self.video_bitrate_edit = QLineEdit(); self.video_bitrate_edit.setPlaceholderText("选填")
        self.resolution_preset_combo = QComboBox()

        self.crf_label = QLabel("CRF:")
        self.cq_label = QLabel("CQ:")
        self.video_bitrate_label = QLabel("比特率:")

        video_grid.addWidget(self.crf_label, 0, 0); video_grid.addWidget(self.crf_edit, 0, 1)
        video_grid.addWidget(self.cq_label, 0, 2); video_grid.addWidget(self.cq_edit, 0, 3)
        video_grid.addWidget(QLabel("帧率:"), 1, 0); video_grid.addWidget(self.fps_edit, 1, 1)
        
        video_grid.addWidget(QLabel("分辨率预设:"), 1, 2); video_grid.addWidget(self.resolution_preset_combo, 1, 3)
        
        video_grid.addWidget(QLabel("分辨率:"), 2, 0); video_grid.addWidget(self.resolution_edit, 2, 1, 1, 3)
        
        video_grid.addWidget(self.video_bitrate_label, 3, 0)
        video_grid.addWidget(self.video_bitrate_edit, 3, 1, 1, 3)


        video_layout.addLayout(codec_v_layout)
        video_layout.addLayout(video_grid)
        options_layout.addWidget(video_group)

        # 音频
        audio_group = QGroupBox("音频")
        audio_layout = QHBoxLayout(audio_group)
        audio_layout.addWidget(QLabel("音频编码:"))
        self.audio_codec_combo = QComboBox()
        audio_layout.addWidget(self.audio_codec_combo)
        self.audio_bitrate_label = QLabel("比特率:")
        self.audio_bitrate_combo = QComboBox()
        audio_layout.addWidget(self.audio_bitrate_label)
        audio_layout.addWidget(self.audio_bitrate_combo)
        audio_layout.addStretch()
        options_layout.addWidget(audio_group)

        # 字幕
        self.subtitle_edit = QLineEdit()
        self.select_subtitle_button = QPushButton("选择")
        self.select_subtitle_button.setIcon(VideoTab.style().standardIcon(QStyle.SP_FileIcon))
        options_layout.addLayout(self._create_hbox("字幕:", self.subtitle_edit, self.select_subtitle_button))

        main_layout.addWidget(options_group)

        self.run_button = QPushButton("开始处理")
        main_layout.addWidget(self.run_button, 0, Qt.AlignCenter)
        main_layout.addStretch()

    def _create_hbox(self, label_text, widget, button):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        layout.addWidget(label)
        layout.addWidget(widget)
        layout.addWidget(button)
        return layout