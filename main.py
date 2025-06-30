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
from utils import STYLESHEET, PROGRESS_RE, time_str_to_seconds, resource_path

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
            # 如果图标仍然没有找到，可以在控制台打印路径以帮助调试
            print(f"DEBUG: Logo not found at path: {logo_path}")
            self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.setWindowTitle("天梦工具箱 V1.0")
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
        self._wrap_run_commands()

    def _setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 使用QSplitter来分隔上下部分
        splitter = QSplitter(Qt.Vertical)

        # 上半部分：主功能选项卡
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

        # 下半部分：信息和控制台
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 5, 0, 0)
        
        # 将信息和控制台放入另一个TabWidget
        info_console_tabs = QTabWidget()
        
        # --- 媒体信息 Tab (使用QScrollArea并限定高度) ---
        info_scroll_area = QScrollArea()
        info_scroll_area.setWidgetResizable(True)
        info_scroll_area.setFixedHeight(150)  # 限定高度为150px

        self.info_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignTop)
        info_scroll_area.setWidget(self.info_label)

        info_console_tabs.addTab(info_scroll_area, "媒体文件信息")
        
        # --- FFmpeg 输出 Tab (包含进度条) ---
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        console_layout.setContentsMargins(0,0,0,0)
        console_layout.setSpacing(5)
        self.console.setReadOnly(True)
        
        # 创建进度条相关控件
        self.progress_bar = QProgressBar()
        self.progress_status_label = QLabel("待命")
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("处理进度:"))
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_status_label)
        progress_layout.setStretch(1, 1)

        # 将控制台和进度条添加到布局中
        console_layout.addWidget(self.console)
        console_layout.addLayout(progress_layout)
        
        info_console_tabs.addTab(console_widget, "FFmpeg 输出信息")
        
        bottom_layout.addWidget(info_console_tabs)
        splitter.addWidget(bottom_widget)

        # 设置初始大小比例
        splitter.setSizes([600, 250])

        main_layout.addWidget(splitter)

    def _connect_signals(self):
        self.process_handler.ffmpeg_process.readyReadStandardOutput.connect(self._update_console)
        self.process_handler.ffmpeg_process.readyReadStandardError.connect(self._update_console)
        self.process_handler.ffmpeg_process.readyReadStandardError.connect(self._update_progress)
        self.process_handler.ffmpeg_process.finished.connect(self._on_process_finished)
        self.process_handler.ffprobe_process.finished.connect(self._on_probe_finished)

    def _wrap_run_commands(self):
        for tab in self.all_tabs:
            if hasattr(tab, '_run_command'):
                original_run = tab._run_command
                def new_run_factory(original_run_method):
                    def new_run():
                        self.reset_progress()
                        original_run_method()
                    return new_run
                tab._run_command = new_run_factory(original_run)

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
            self.info_label.setText(self.format_media_info(data))
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
        if process.canReadLine():
            message = codec.toUnicode(process.readLine())
        else:
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
        progress_lines = lines[:-1]
        if not progress_lines: return
        latest_line = progress_lines[-1]
        match = PROGRESS_RE.search(latest_line)
        if match and self.total_duration_sec > 0:
            data = match.groupdict()
            current_time_sec = time_str_to_seconds(data['time'])
            percentage = int((current_time_sec / self.total_duration_sec) * 100)
            self.progress_bar.setValue(min(percentage, 100))
            speed = float(data.get('speed', 0))
            eta_str = "N/A"
            if speed > 0:
                remaining_sec = (self.total_duration_sec - current_time_sec) / speed
                eta_str = str(datetime.timedelta(seconds=int(remaining_sec)))
            status_text = (f"{percentage}% | "
                           f"FPS: {float(data['fps']):.1f} | "
                           f"速度: {speed:.2f}x | "
                           f"剩余: {eta_str}")
            self.progress_status_label.setText(status_text)

    @staticmethod
    def format_media_info(data):
        try:
            fmt = data.get('format', {})
            filename = os.path.basename(fmt.get('filename', 'N/A'))
            duration_sec = float(fmt.get('duration', 0))
            duration_str = str(datetime.timedelta(seconds=int(duration_sec)))
            bit_rate_kbps = int(float(fmt.get('bit_rate', 0)) / 1000)
            info = f"""
            <style>
                b {{ color: #00aaff; }}
                td {{ padding: 2px 8px 2px 0; vertical-align: top; }}
            </style>
            <table>
                <tr><td><b>文件名:</b></td><td>{filename}</td></tr>
                <tr><td><b>格式:</b></td><td>{fmt.get('format_long_name', 'N/A')}</td></tr>
                <tr><td><b>时长:</b></td><td>{duration_str}</td></tr>
                <tr><td><b>总比特率:</b></td><td>{bit_rate_kbps:.0f} kb/s</td></tr>
            </table><hr>
            """
            for stream in data.get('streams', []):
                stream_type = stream.get('codec_type')
                info += f"<b>{stream_type.capitalize()} 流 #{stream.get('index')}:</b><br>"
                info += "<table>"
                if stream_type == 'video':
                    info += (f"<tr><td>&nbsp;&nbsp;编码:</td><td>{stream.get('codec_long_name', 'N/A')}</td></tr>"
                             f"<tr><td>&nbsp;&nbsp;分辨率:</td><td>{stream.get('width')}x{stream.get('height')}</td></tr>"
                             f"<tr><td>&nbsp;&nbsp;帧率:</td><td>{eval(stream.get('r_frame_rate', '0/1')):.2f} fps</td></tr>")
                elif stream_type == 'audio':
                    info += (f"<tr><td>&nbsp;&nbsp;编码:</td><td>{stream.get('codec_long_name', 'N/A')}</td></tr>"
                             f"<tr><td>&nbsp;&nbsp;采样率:</td><td>{stream.get('sample_rate')} Hz</td></tr>"
                             f"<tr><td>&nbsp;&nbsp;通道:</td><td>{stream.get('channel_layout', 'N/A')}</td></tr>")
                info += "</table><br>"
            return info.strip().removesuffix("<br>")
        except Exception as e:
            return f"<font color='red'>格式化信息时出错: {e}</font>"

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