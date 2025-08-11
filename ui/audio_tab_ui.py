# -*- coding: utf-8 -*-
# SkyDreamBox/ui/audio_tab_ui.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QGroupBox, QComboBox, QStyle, QGridLayout
)
from PyQt5.QtCore import Qt

class Ui_AudioTab:
    def setupUi(self, AudioTab):
        # --- 主布局: 垂直布局 ---
        main_layout = QVBoxLayout(AudioTab)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 15, 10, 15)

        # --- 第一部分: 输入与输出 (一栏) ---
        io_group = QGroupBox("输入输出")
        io_layout = QVBoxLayout(io_group)
        io_layout.setSpacing(8)
        
        self.input_edit = QLineEdit()
        self.select_input_button = QPushButton("选择")
        self.select_input_button.setIcon(AudioTab.style().standardIcon(QStyle.SP_DirOpenIcon))
        io_layout.addLayout(self._create_hbox("输入文件:", self.input_edit, self.select_input_button))

        self.output_edit = QLineEdit()
        self.select_output_button = QPushButton("选择")
        self.select_output_button.setIcon(AudioTab.style().standardIcon(QStyle.SP_DriveFDIcon))
        io_layout.addLayout(self._create_hbox("输出文件:", self.output_edit, self.select_output_button))
        
        main_layout.addWidget(io_group)

        # --- 第二部分: 参数设置 (二栏) ---
        options_group = QGroupBox("参数设置")
        # 使用QGridLayout实现灵活的两栏布局
        options_layout = QGridLayout(options_group)
        options_layout.setSpacing(10)

        # 左栏参数
        options_layout.addWidget(QLabel("格式:"), 0, 0)
        self.format_combo = QComboBox()
        options_layout.addWidget(self.format_combo, 0, 1)

        options_layout.addWidget(QLabel("编码器:"), 1, 0)
        self.codec_combo = QComboBox()
        options_layout.addWidget(self.codec_combo, 1, 1)

        options_layout.addWidget(QLabel("采样率:"), 2, 0)
        self.sample_rate_combo = QComboBox()
        options_layout.addWidget(self.sample_rate_combo, 2, 1)

        # 右栏参数
        self.bit_depth_label = QLabel("位深/格式:")
        options_layout.addWidget(self.bit_depth_label, 0, 2)
        self.bit_depth_combo = QComboBox()
        options_layout.addWidget(self.bit_depth_combo, 0, 3)

        self.bitrate_label = QLabel("比特率:")
        options_layout.addWidget(self.bitrate_label, 1, 2)
        self.bitrate_combo = QComboBox()
        options_layout.addWidget(self.bitrate_combo, 1, 3)

        self.compression_label = QLabel("压缩等级:")
        options_layout.addWidget(self.compression_label, 2, 2)
        self.compression_combo = QComboBox()
        options_layout.addWidget(self.compression_combo, 2, 3)

        # 设置列伸展，让两栏宽度均等
        options_layout.setColumnStretch(1, 1)
        options_layout.setColumnStretch(3, 1)
        
        main_layout.addWidget(options_group)

        # --- 第三部分: 执行按钮 ---
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