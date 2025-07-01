# -*- coding: utf-8 -*-
import sys
import os
import json
import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFileDialog, QLabel, QTabWidget, QTextEdit, QProgressBar, QStyle, QSplitter,
    QScrollArea
)
from PyQt5.QtCore import QProcess, QTextCodec, Qt
from PyQt5.QtGui import QIcon

from process_handler import ProcessHandler
from ui_tabs import (
    VideoTab, AudioTab, MuxingTab, DemuxingTab, CommonOperationsTab, ProfessionalTab
)
# 导入重构后的工具函数
from utils import STYLESHEET, PROGRESS_RE, time_str_to_seconds, resource_path, format_media_info

# =============================================================================
# Main Application Window (主程序窗口)
# =============================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logo_path = resource_path("assets/logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        else:
            print(f"DEBUG: Logo not found at path: {logo_path}")
            self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        self.setWindowTitle("天梦工具箱 V1.1")
        self.setGeometry(100, 100, 850, 850)
        self.console = QTextEdit()
        self.console.setObjectName("console")
        self.process_handler = ProcessHandler(self)
        self.info_label = QLabel("请选择一个媒体文件以查看信息...")
        self.info_label.setObjectName("info_label")
        self.all_tabs = []
        self.total_duration_sec = 0
        self.last_progress_text = ""
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Vertical)

        self.tabs = QTabWidget()
        self.video_tab = VideoTab(self.process_handler, self.console, self)
        self.audio_tab = AudioTab(self.process_handler, self.console, self)
        self.muxing_tab = MuxingTab(self.process_handler, self.console, self)
        self.demuxing_tab = DemuxingTab(self.process_handler, self.console, self)
        self.common_tab = CommonOperationsTab(self.process_handler, self.console, self)
        self.pro_tab = ProfessionalTab(self.process_handler, self.console, self)
        self.all_tabs = [self.video_tab, self.audio_tab, self.muxing_tab, self.demuxing_tab, self.common_tab, self.pro_tab]
        self.tabs.addTab(self.video_tab, "视频处理")
        self.tabs.addTab(self.audio_tab, "音频处理")
        self.tabs.addTab(self.muxing_tab, "封装合并")
        self.tabs.addTab(self.demuxing_tab, "抽取音视频")
        self.tabs.addTab(self.common_tab, "常用操作")
        self.tabs.addTab(self.pro_tab, "专业命令")
        splitter.addWidget(self.tabs)

        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 5, 0, 0)
        info_console_tabs = QTabWidget()

        info_scroll_area = QScrollArea()
        info_scroll_area.setWidgetResizable(True)
        info_scroll_area.setFixedHeight(150)
        self.info_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignTop)
        info_scroll_area.setWidget(self.info_label)
        info_console_tabs.addTab(info_scroll_area, "媒体文件信息")

        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        console_layout.setContentsMargins(0,0,0,0)
        console_layout.setSpacing(5)
        self.console.setReadOnly(True)

        self.progress_bar = QProgressBar()
        self.progress_status_label = QLabel("待命")
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("处理进度:"))
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_status_label)
        progress_layout.setStretch(1, 1)

        console_layout.addWidget(self.console)
        console_layout.addLayout(progress_layout)
        info_console_tabs.addTab(console_widget, "FFmpeg 输出信息")

        bottom_layout.addWidget(info_console_tabs)
        splitter.addWidget(bottom_widget)
        splitter.setSizes([600, 250])
        main_layout.addWidget(splitter)

    def _connect_signals(self):
        self.process_handler.ffmpeg_process.readyReadStandardOutput.connect(self._update_console)
        self.process_handler.ffmpeg_process.readyReadStandardError.connect(self._update_console)
        self.process_handler.ffmpeg_process.readyReadStandardError.connect(self._update_progress)
        self.process_handler.ffmpeg_process.finished.connect(self._on_process_finished)
        self.process_handler.ffprobe_process.finished.connect(self._on_probe_finished)

    def select_file(self, target_line_edit):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择输入文件")
        if not file_name: return
        self.reset_progress()
        target_line_edit.setText(file_name)
        self.process_handler.run_ffprobe(file_name)
        current_tab = self.tabs.currentWidget()
        if hasattr(current_tab, 'output_edit') and hasattr(current_tab, 'format_combo'):
            output_edit = getattr(current_tab, 'output_edit', None)
            format_combo = getattr(current_tab, 'format_combo', None)
            if output_edit and format_combo:
                base_path, _ = os.path.splitext(file_name)
                selected_format = format_combo.currentText()
                output_edit.setText(f"{base_path}_output.{selected_format}")

    def reset_progress(self):
        self.progress_bar.setValue(0)
        self.progress_status_label.setText("待命")
        self.total_duration_sec = 0
        self.last_progress_text = ""

    def set_buttons_enabled(self, enabled):
        for tab in self.all_tabs:
            if hasattr(tab, 'run_button') and tab.run_button:
                tab.run_button.setEnabled(enabled)
            if isinstance(tab, DemuxingTab):
                tab.extract_video_button.setEnabled(enabled)
                tab.extract_audio_button.setEnabled(enabled)
            if isinstance(tab, CommonOperationsTab):
                tab.trim_button.setEnabled(enabled)
                tab.img_audio_button.setEnabled(enabled)

    def _on_probe_finished(self):
        output = self.process_handler.ffprobe_process.readAllStandardOutput().data().decode('utf-8', 'ignore')
        try:
            data = json.loads(output)
            # 调用从 utils.py 导入的函数
            self.info_label.setText(format_media_info(data))
            if 'format' in data and 'duration' in data['format']:
                self.total_duration_sec = float(data['format']['duration'])
        except (json.JSONDecodeError, KeyError, TypeError):
            self.info_label.setText("<font color='red'>无法解析文件信息或获取时长。</font>")
            self.total_duration_sec = 0

    def _on_process_finished(self, exit_code, exit_status):
        self.set_buttons_enabled(True)
        if exit_status == QProcess.NormalExit and exit_code == 0:
            self.console.append("\n<hr><b><font color='#4CAF50'>处理成功完成!</font></b>")
            self.progress_bar.setValue(100)
            self.progress_status_label.setText("处理成功!")
        else:
            self.console.append(f"\n<hr><b><font color='#F44336'>处理失败! (退出码: {exit_code})</font></b>")
            self.progress_status_label.setText("处理失败!")
        self.last_progress_text = ""

    def _update_console(self):
        process = self.sender()
        if not process: return
        codec = QTextCodec.codecForLocale()
        message = codec.toUnicode(process.readAll())
        self.console.insertPlainText(message)
        self.console.ensureCursorVisible()

    def _update_progress(self):
        process = self.process_handler.ffmpeg_process
        if not process: return
        output = process.readAllStandardError().data().decode('utf-8', 'ignore')
        text = self.last_progress_text + output
        lines = text.split('\r')
        self.last_progress_text = lines[-1]
        if not lines[:-1]: return
        latest_line = lines[-2] # Get the last complete line
        match = PROGRESS_RE.search(latest_line)
        if match and self.total_duration_sec > 0:
            data = match.groupdict()
            current_time_sec = time_str_to_seconds(data.get('time', '0'))
            percentage = int((current_time_sec / self.total_duration_sec) * 100)
            self.progress_bar.setValue(min(percentage, 100))
            speed_str = data.get('speed', '0').replace('x', '')
            speed = float(speed_str) if speed_str else 0
            eta_str = "N/A"
            if speed > 0:
                remaining_sec = (self.total_duration_sec - current_time_sec) / speed
                eta_str = str(datetime.timedelta(seconds=int(remaining_sec)))
            fps_str = data.get('fps', '0.0')
            status_text = (f"{percentage}% | "
                           f"FPS: {float(fps_str):.1f} | "
                           f"速度: {speed:.2f}x | "
                           f"剩余: {eta_str}")
            self.progress_status_label.setText(status_text)

# =============================================================================
# Main Execution (主程序入口)
# =============================================================================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    QTextCodec.setCodecForLocale(QTextCodec.codecForName("UTF-8"))
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())