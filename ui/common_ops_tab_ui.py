# -*- coding: utf-8 -*-
# SkyDreamBox/ui/common_ops_tab_ui.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QGroupBox, QStyle
)
from PyQt5.QtCore import Qt

class Ui_CommonOpsTab:
    def setupUi(self, CommonOpsTab):
        main_layout = QVBoxLayout(CommonOpsTab)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(10, 15, 10, 15)

        # --- 视频截取组 ---
        trim_group = QGroupBox("视频截取 (快速，无损)")
        trim_layout = QVBoxLayout(trim_group)

        self.trim_input_edit = QLineEdit()
        self.select_trim_input_button = QPushButton("选择输入")
        self.select_trim_input_button.setIcon(CommonOpsTab.style().standardIcon(QStyle.SP_DirOpenIcon))
        trim_layout.addLayout(self._create_hbox("输入文件:", self.trim_input_edit, self.select_trim_input_button))

        self.trim_output_edit = QLineEdit()
        self.select_trim_output_button = QPushButton("选择输出")
        # --- FIX ---
        self.select_trim_output_button.setIcon(CommonOpsTab.style().standardIcon(QStyle.SP_DriveFDIcon))
        trim_layout.addLayout(self._create_hbox("输出文件:", self.trim_output_edit, self.select_trim_output_button))

        time_layout = QHBoxLayout()
        self.start_time_edit = QLineEdit("00:00:00")
        self.end_time_edit = QLineEdit()
        self.end_time_edit.setPlaceholderText("HH:MM:SS 或留空至结尾")
        time_layout.addWidget(QLabel("开始时间:"))
        time_layout.addWidget(self.start_time_edit)
        time_layout.addSpacing(20)
        time_layout.addWidget(QLabel("结束时间:"))
        time_layout.addWidget(self.end_time_edit)
        trim_layout.addLayout(time_layout)

        self.trim_button = QPushButton("开始截取")
        trim_layout.addWidget(self.trim_button, 0, Qt.AlignCenter)
        main_layout.addWidget(trim_group)

        # --- 图声合成组 ---
        img_audio_group = QGroupBox("图声合成")
        img_audio_layout = QVBoxLayout(img_audio_group)

        self.img_input_edit = QLineEdit()
        self.select_img_button = QPushButton("选择图片")
        self.select_img_button.setIcon(CommonOpsTab.style().standardIcon(QStyle.SP_FileIcon))
        img_audio_layout.addLayout(self._create_hbox("图片文件:", self.img_input_edit, self.select_img_button))

        self.audio_input_edit = QLineEdit()
        self.select_audio_button = QPushButton("选择音频")
        self.select_audio_button.setIcon(CommonOpsTab.style().standardIcon(QStyle.SP_FileIcon))
        img_audio_layout.addLayout(self._create_hbox("音频文件:", self.audio_input_edit, self.select_audio_button))

        self.img_audio_output_edit = QLineEdit()
        self.select_img_audio_output_button = QPushButton("选择输出")
        # --- FIX ---
        self.select_img_audio_output_button.setIcon(CommonOpsTab.style().standardIcon(QStyle.SP_DriveFDIcon))
        img_audio_layout.addLayout(self._create_hbox("输出视频:", self.img_audio_output_edit, self.select_img_audio_output_button))

        self.img_audio_button = QPushButton("开始合成")
        img_audio_layout.addWidget(self.img_audio_button, 0, Qt.AlignCenter)
        main_layout.addWidget(img_audio_group)

        main_layout.addStretch()

    def _create_hbox(self, label_text, widget, button):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(70)
        layout.addWidget(label)
        layout.addWidget(widget)
        layout.addWidget(button)
        return layout