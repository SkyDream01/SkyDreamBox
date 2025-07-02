# -*- coding: utf-8 -*-
# SkyDreamBox/main.py

import sys
import os
import json
import datetime
import time

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QSplashScreen
)
from PyQt5.QtCore import QProcess, QTextCodec, Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap

# UI 和逻辑分离
from ui.main_window_ui import Ui_MainWindow
from process_handler import ProcessHandler
from ui_tabs import (
    VideoTab, AudioTab, MuxingTab, DemuxingTab, CommonOperationsTab, ProfessionalTab
)
from about import AboutWindow
from utils import (
    STYLESHEET, PROGRESS_RE, time_str_to_seconds, resource_path, format_media_info
)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, splash=None):
        super().__init__()

        self.splash = splash
        self.update_splash("正在初始化组件...")

        # 设置UI
        self.setupUi(self)

        self.process_handler = ProcessHandler(self)

        self.update_splash("正在检查核心组件 FFmpeg...")
        is_ffmpeg_ready, message = self.process_handler.check_ffmpeg()
        if not is_ffmpeg_ready:
            self.setWindowTitle("错误")
            self._show_ffmpeg_error_and_exit(message)
            # Use QTimer to allow the event loop to start before closing
            QTimer.singleShot(100, self.close)
            return

        self.update_splash("正在加载应用图标...")
        logo_path = resource_path("assets/logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))

        self.setWindowTitle("天梦工具箱 (SkyDreamBox)")
        # --- MODIFIED: Reduced window size ---
        self.setGeometry(100, 100, 100, 100) # 减小了窗口大小

        self.all_tabs = []
        self.total_duration_sec = 0
        self.last_progress_text = ""
        self.about_window = None

        self.update_splash("正在构建用户界面...")
        self._setup_tabs()

        self.update_splash("正在连接信号与槽...")
        self._connect_signals()

        self.update_splash("初始化完成!", 100)

    def update_splash(self, message, progress=None):
        if self.splash:
            self.splash.showMessage(
                message,
                Qt.AlignBottom | Qt.AlignHCenter,
                Qt.white
            )
            if progress is not None:
                # Give some time for the message to be visible
                time.sleep(0.5)
            QApplication.processEvents()

    def _show_ffmpeg_error_and_exit(self, message):
        error_box = QMessageBox(self)
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("核心组件缺失")
        error_box.setText(message)
        error_box.setStandardButtons(QMessageBox.Ok)
        error_box.exec_()

    def _setup_tabs(self):
        self.video_tab = VideoTab(self)
        self.audio_tab = AudioTab(self)
        self.muxing_tab = MuxingTab(self)
        self.demuxing_tab = DemuxingTab(self)
        self.common_tab = CommonOperationsTab(self)
        self.pro_tab = ProfessionalTab(self)

        self.all_tabs = [
            self.video_tab, self.audio_tab, self.muxing_tab,
            self.demuxing_tab, self.common_tab, self.pro_tab
        ]

        self.tabs.addTab(self.video_tab, "视频处理")
        self.tabs.addTab(self.audio_tab, "音频处理")
        self.tabs.addTab(self.muxing_tab, "封装合并")
        self.tabs.addTab(self.demuxing_tab, "抽取音视频")
        self.tabs.addTab(self.common_tab, "常用操作")
        self.tabs.addTab(self.pro_tab, "专业命令")

    def _connect_signals(self):
        # 进程信号
        self.process_handler.ffmpeg_process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process_handler.ffmpeg_process.readyReadStandardError.connect(self._handle_stderr)
        self.process_handler.ffmpeg_process.finished.connect(self._on_process_finished)
        self.process_handler.ffprobe_process.finished.connect(self._on_probe_finished)

        # 菜单栏信号
        self.about_action.triggered.connect(self._show_about_dialog)

    def _show_about_dialog(self):
        if self.about_window is None:
            self.about_window = AboutWindow(self)
        self.about_window.exec_()

    def switch_to_console_tab(self):
        self.info_console_tabs.setCurrentIndex(1)

    def select_file(self, target_line_edit):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择输入文件")
        if not file_name:
            return

        self.reset_media_info()
        self.reset_progress_display()

        target_line_edit.setText(file_name)
        self.process_handler.run_ffprobe(file_name)

        # Auto-populate output path for relevant tabs
        current_tab = self.tabs.currentWidget()
        if hasattr(current_tab, 'auto_set_output_path'):
            current_tab.auto_set_output_path(file_name)

    def reset_progress_display(self):
        self.progress_bar.setValue(0)
        self.progress_status_label.setText("待命")
        self.last_progress_text = ""

    def reset_media_info(self):
        self.info_label.setText("正在获取媒体文件信息...")
        self.total_duration_sec = 0

    def set_buttons_enabled(self, enabled):
        for tab in self.all_tabs:
            tab.set_buttons_enabled(enabled)

    def _on_probe_finished(self):
        output = self.process_handler.ffprobe_process.readAllStandardOutput().data().decode('utf-8', 'ignore')
        try:
            data = json.loads(output)
            self.info_label.setText(format_media_info(data))
            if 'format' in data and 'duration' in data['format']:
                self.total_duration_sec = float(data['format']['duration'])
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.info_label.setText(f"<font color='#f1c40f'>无法解析文件信息或获取时长: {e}</font>")
            self.total_duration_sec = 0

    def _on_process_finished(self, exit_code, exit_status):
        self.set_buttons_enabled(True)
        if exit_status == QProcess.NormalExit and exit_code == 0:
            if self.progress_bar.value() < 100:
                self.progress_bar.setValue(100)
            self.console.append("\n<hr><b><font color='#2ecc71'>处理成功完成!</font></b>")
            self.progress_status_label.setText("处理成功!")
        else:
            self.console.append(f"\n<hr><b><font color='#e74c3c'>处理失败! (退出码: {exit_code})</font></b>")
            self.progress_status_label.setText("处理失败!")
        self.last_progress_text = ""

    def _handle_stdout(self):
        process = self.process_handler.ffmpeg_process
        if not process: return
        codec = QTextCodec.codecForLocale()
        message = codec.toUnicode(process.readAllStandardOutput())
        self.console.insertPlainText(message)
        self.console.ensureCursorVisible()

    def _handle_stderr(self):
        process = self.process_handler.ffmpeg_process
        if not process: return
        error_output = process.readAllStandardError().data().decode('utf-8', 'ignore')
        self.console.insertPlainText(error_output)
        self.console.ensureCursorVisible()
        self._parse_and_update_progress(error_output)

    def _parse_and_update_progress(self, output):
        text = self.last_progress_text + output
        # Use '\r' as the primary splitter for progress lines
        lines = text.split('\r')
        self.last_progress_text = lines[-1]

        if not lines[:-1]: return

        latest_line = ""
        # Find the last complete progress line
        for line in reversed(lines[:-1]):
            if 'frame=' in line and 'time=' in line:
                latest_line = line
                break

        if not latest_line: return

        match = PROGRESS_RE.search(latest_line)
        if not match: return

        if self.total_duration_sec <= 0:
            self.progress_status_label.setText("正在处理 (时长未知)...")
            return

        data = match.groupdict()
        current_time_sec = time_str_to_seconds(data.get('time', '0'))
        percentage = min(100, int((current_time_sec / self.total_duration_sec) * 100))
        self.progress_bar.setValue(percentage)

        speed_str = data.get('speed', '0').replace('x', '')
        try:
            speed = float(speed_str)
        except (ValueError, TypeError):
            speed = 0

        eta_str = "N/A"
        if speed > 0:
            remaining_sec = (self.total_duration_sec - current_time_sec) / speed
            if remaining_sec > 0:
                eta_str = str(datetime.timedelta(seconds=int(remaining_sec)))

        fps_str = data.get('fps', '0.0')
        try:
            fps = float(fps_str)
        except (ValueError, TypeError):
            fps = 0.0

        status_text = (f"{percentage}% | "
                       f"FPS: {fps:.1f} | "
                       f"速度: {speed:.2f}x | "
                       f"剩余: {eta_str}")
        self.progress_status_label.setText(status_text)


if __name__ == '__main__':
    # Enable High DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    QTextCodec.setCodecForLocale(QTextCodec.codecForName("UTF-8"))

    # --- Create and display splash screen ---
    logo_path = resource_path("assets/logo.png")
    pixmap = QPixmap(logo_path)
    # --- MODIFIED: Changed logo size ---
    scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    splash = QSplashScreen(scaled_pixmap, Qt.WindowStaysOnTopHint)
    splash.show()
    # ---

    main_win = MainWindow(splash)

    # Ensure main window was initialized correctly before proceeding
    if not main_win.centralWidget():
        sys.exit(1)

    main_win.show()
    splash.finish(main_win)

    sys.exit(app.exec_())