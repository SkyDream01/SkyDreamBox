# -*- coding: utf-8 -*-
# SkyDreamBox/main.py

import sys
import os
import json
import datetime
import time

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QWidget
)
from PySide6.QtCore import QProcess, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap

# --- UI 和逻辑分离 ---
from constants import APP_NAME
from ui.main_window_ui import Ui_MainWindow
from ui.splash_screen_ui import CustomSplashScreen
from process_handler import ProcessHandler
from ui_tabs import (
    VideoTab, AudioTab, MuxingTab, DemuxingTab, CommonOperationsTab, ProfessionalTab, SettingsTab, AboutTab
)
from utils import (
    STYLESHEET, PROGRESS_RE, time_str_to_seconds, resource_path, format_media_info
)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, splash=None):
        super().__init__()

        self.splash = splash
        self.update_splash("正在唤醒组件...", 10)

        # 设置UI
        self.setupUi(self)
        self.process_handler = ProcessHandler(self)

        self.update_splash("正在检查 FFmpeg 引擎...", 30)
        is_ffmpeg_ready, message = self.process_handler.check_ffmpeg()
        if not is_ffmpeg_ready:
            self.setWindowTitle("核心组件错误")
            self._show_ffmpeg_error_and_exit(message)
            QTimer.singleShot(100, self.close)
            return

        self.update_splash("正在加载视觉元素...", 50)
        logo_path = resource_path("assets/logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))

        self.setWindowTitle(APP_NAME)
        self.setGeometry(50, 50, 750, 900)

        self.initialized_tabs = {}
        self.tab_constructors = {
            "视频处理": VideoTab, "音频处理": AudioTab, "音视频合并": MuxingTab,
            "音视频分离": DemuxingTab, "常用工具": CommonOperationsTab, "专业命令": ProfessionalTab,
            "设置": SettingsTab, "关于": AboutTab
        }
        
        self.total_duration_sec = 0
        self.last_progress_text = ""

        self.update_splash("正在构建用户界面...", 70)
        self._setup_tabs()

        self.update_splash("正在连接功能模块...", 90)
        self._connect_signals()

        self.update_splash("初始化完成，即将启动!", 100)


    def update_splash(self, message, progress):
        if self.splash:
            self.splash.showMessage(message)
            self.splash.setProgress(progress)
            if progress == 100:
                time.sleep(0.3)

    def _show_ffmpeg_error_and_exit(self, message):
        error_box = QMessageBox(self)
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle("核心组件缺失")
        error_box.setText(message)
        error_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        error_box.exec()

    def _setup_tabs(self):
        for name in self.tab_constructors.keys():
            placeholder_widget = QWidget()
            self.tabs.addTab(placeholder_widget, name)
            
    def _initialize_tab(self, index):
        if index in self.initialized_tabs:
            return

        tab_name = self.tabs.tabText(index)
        if tab_name in self.tab_constructors:
            constructor = self.tab_constructors[tab_name]
            tab_widget = constructor(self)
            
            self.initialized_tabs[index] = tab_widget
            
            self.tabs.removeTab(index)
            self.tabs.insertTab(index, tab_widget, tab_name)
            self.tabs.setCurrentIndex(index)

    def _connect_signals(self):
        self.process_handler.ffmpeg_process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process_handler.ffmpeg_process.readyReadStandardError.connect(self._handle_stderr)
        self.process_handler.ffmpeg_process.finished.connect(self._on_process_finished)
        self.process_handler.ffprobe_process.finished.connect(self._on_probe_finished)
        self.tabs.currentChanged.connect(self._initialize_tab)
        QTimer.singleShot(0, lambda: self._initialize_tab(0))

    def switch_to_console_tab(self):
        self.info_console_tabs.setCurrentIndex(1)

    def select_file(self, target_line_edit):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if not file_name: return

        self.reset_media_info()
        self.reset_progress_display()
        target_line_edit.setText(file_name)
        self.process_handler.run_ffprobe(file_name)

        current_tab_index = self.tabs.currentIndex()
        if current_tab_index in self.initialized_tabs:
            current_tab = self.initialized_tabs[current_tab_index]
            if hasattr(current_tab, 'auto_set_output_path'):
                current_tab.auto_set_output_path(file_name)

    def reset_progress_display(self):
        self.progress_bar.setValue(0)
        self.progress_status_label.setText("待机")
        self.last_progress_text = ""

    def reset_media_info(self):
        self.info_label.setText("正在读取媒体信息...")
        self.total_duration_sec = 0

    def set_buttons_enabled(self, enabled):
        for tab in self.initialized_tabs.values():
            if hasattr(tab, 'set_buttons_enabled'):
                tab.set_buttons_enabled(enabled)

    def _on_probe_finished(self):
        output = self.process_handler.ffprobe_process.readAllStandardOutput().data().decode('utf-8', 'ignore')
        try:
            data = json.loads(output)
            self.info_label.setText(format_media_info(data))
            if 'format' in data and 'duration' in data['format']:
                self.total_duration_sec = float(data['format']['duration'])
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.info_label.setText(f"<font color='#f1c40f'>无法解析媒体信息: {e}</font>")
            self.total_duration_sec = 0

    def _on_process_finished(self, exit_code, exit_status):
        self.set_buttons_enabled(True)
        if exit_status == QProcess.ExitStatus.NormalExit and exit_code == 0:
            if self.progress_bar.value() < 100: self.progress_bar.setValue(100)
            self.console.append("\n<hr><b><font color='#2ecc71'>任务已成功完成！</font></b>")
            self.progress_status_label.setText("任务完成")
        else:
            self.console.append(f"\n<hr><b><font color='#e74c3c'>任务失败 (退出码: {exit_code})</font></b>")
            self.progress_status_label.setText("任务失败")
        self.last_progress_text = ""

    def _handle_stdout(self):
        process = self.process_handler.ffmpeg_process
        if not process: return
        message = process.readAllStandardOutput().data().decode('utf-8', 'ignore')
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
        lines = text.split('\r')
        self.last_progress_text = lines[-1]
        if not lines[:-1]: return
        latest_line = ""
        for line in reversed(lines[:-1]):
            if 'frame=' in line and 'time=' in line:
                latest_line = line
                break
        if not latest_line: return
        match = PROGRESS_RE.search(latest_line)
        if not match: return
        if self.total_duration_sec <= 0:
            self.progress_status_label.setText("处理中 (时长未知)...")
            return
        data = match.groupdict()
        current_time_sec = time_str_to_seconds(data.get('time', '0'))
        percentage = min(100, int((current_time_sec / self.total_duration_sec) * 100))
        self.progress_bar.setValue(percentage)
        speed_str = data.get('speed', '0').replace('x', '')
        try: speed = float(speed_str)
        except (ValueError, TypeError): speed = 0
        eta_str = "未知"
        if speed > 0:
            remaining_sec = (self.total_duration_sec - current_time_sec) / speed
            if remaining_sec > 0:
                eta_str = str(datetime.timedelta(seconds=int(remaining_sec)))
        fps_str = data.get('fps', '0.0')
        try: fps = float(fps_str)
        except (ValueError, TypeError): fps = 0.0
        status_text = (f"{percentage}% | 帧率: {fps:.1f} | 速度: {speed:.2f}x | 剩余: {eta_str}")
        self.progress_status_label.setText(status_text)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    
    logo_path = resource_path("assets/logo.png")
    icon_pixmap = QPixmap(logo_path)
    
    splash = CustomSplashScreen(icon_pixmap, app_name=APP_NAME, version="2.2")
    splash.show()

    main_win = MainWindow(splash)

    if not main_win.centralWidget():
        sys.exit(1)

    main_win.show()
    splash.finish(main_win)

    sys.exit(app.exec())