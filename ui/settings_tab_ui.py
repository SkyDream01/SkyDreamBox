# -*- coding: utf-8 -*-
# SkyDreamBox/ui/settings_tab_ui.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QGroupBox, QComboBox, QGridLayout, QStyle, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt

class Ui_SettingsTab:
    def setupUi(self, SettingsTab):
        main_layout = QVBoxLayout(SettingsTab)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # --- FFmpeg设置组 ---
        ffmpeg_group = QGroupBox("FFmpeg 设置")
        ffmpeg_layout = QVBoxLayout(ffmpeg_group)
        ffmpeg_layout.setSpacing(8)
        
        # FFmpeg路径
        self.ffmpeg_path_edit = QLineEdit()
        self.ffmpeg_browse_button = QPushButton("浏览")
        self.ffmpeg_browse_button.setIcon(SettingsTab.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        ffmpeg_layout.addLayout(self._create_hbox("FFmpeg 路径:", self.ffmpeg_path_edit, self.ffmpeg_browse_button))
        
        # FFprobe路径
        self.ffprobe_path_edit = QLineEdit()
        self.ffprobe_browse_button = QPushButton("浏览")
        self.ffprobe_browse_button.setIcon(SettingsTab.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        ffmpeg_layout.addLayout(self._create_hbox("FFprobe 路径:", self.ffprobe_path_edit, self.ffprobe_browse_button))
        
        # 路径说明标签
        path_note = QLabel("留空或填写 'ffmpeg'/'ffprobe' 将使用系统PATH中的程序")
        path_note.setStyleSheet("color: #888; font-size: 8pt;")
        ffmpeg_layout.addWidget(path_note)
        
        # 测试按钮
        self.test_button = QPushButton("测试FFmpeg配置")
        self.test_button.setIcon(SettingsTab.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
        ffmpeg_layout.addWidget(self.test_button, alignment=Qt.AlignmentFlag.AlignLeft)
        
        main_layout.addWidget(ffmpeg_group)
        
        # --- 常规设置组 ---
        general_group = QGroupBox("常规设置")
        general_layout = QVBoxLayout(general_group)
        general_layout.setSpacing(8)
        
        self.overwrite_files_check = QCheckBox("覆盖已存在的文件")
        self.overwrite_files_check.setChecked(True)
        general_layout.addWidget(self.overwrite_files_check)
        
        main_layout.addWidget(general_group)
        
        # --- 按钮组 ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("保存设置")
        self.save_button.setIcon(SettingsTab.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        button_layout.addWidget(self.save_button)
        
        self.reset_button = QPushButton("重置为默认")
        self.reset_button.setIcon(SettingsTab.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton))
        button_layout.addWidget(self.reset_button)
        
        main_layout.addLayout(button_layout)
        
        # 底部说明
        note = QLabel("部分设置需要重启应用才能生效")
        note.setStyleSheet("color: #f1c40f; font-size: 8pt; font-style: italic;")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(note)
        
        main_layout.addStretch()
    
    def _create_hbox(self, label_text, line_edit, button):
        """创建水平布局：标签 + 输入框 + 按钮"""
        layout = QHBoxLayout()
        layout.setSpacing(5)
        label = QLabel(label_text)
        label.setMinimumWidth(80)
        layout.addWidget(label)
        layout.addWidget(line_edit)
        layout.addWidget(button)
        return layout
    
    def _create_hbox_widget(self, widget1, widget2):
        """创建水平布局：两个部件"""
        layout = QHBoxLayout()
        layout.setSpacing(5)
        widget1.setMinimumWidth(80)
        layout.addWidget(widget1)
        layout.addWidget(widget2)
        return layout