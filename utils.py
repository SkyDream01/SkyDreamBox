# -*- coding: utf-8 -*-
import re
import sys
import os

# =============================================================================
# Constants and Configurations (常量与配置)
# =============================================================================
VIDEO_FORMATS = ["mp4", "mkv", "avi", "mov", "webm"]
VIDEO_CODECS = ["libx264", "libx265", "copy", "vp9", "h264_nvenc", "hevc_nvenc"]
AUDIO_CODECS_VIDEO_TAB = ["aac", "mp3", "copy", "flac"] #移除了 'opus'
AUDIO_BITRATES = ["128k", "192k", "256k", "320k"] #新增音频码率选项
AUDIO_FORMATS = ["mp3", "flac", "aac", "wav", "opus", "alac", "m4a"]
AUDIO_CODECS_AUDIO_TAB = ["libmp3lame", "flac", "aac", "pcm_s16le", "libopus", "alac", "copy"]
SUBTITLE_FORMATS = "字幕文件 (*.srt *.ass *.ssa);;所有文件 (*)"
DEFAULT_COMPRESSION_LEVEL = "5"

# =============================================================================
# Stylesheet (样式表)
# =============================================================================
STYLESHEET = """
QWidget {
    background-color: #2e2e2e;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Microsoft YaHei', 'Arial';
    font-size: 10pt;
}
QMainWindow {
    background-color: #2e2e2e;
}
QGroupBox {
    background-color: #383838;
    border: 1px solid #555;
    border-radius: 5px;
    margin-top: 1ex;
    padding: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 3px;
    background-color: #2e2e2e;
    color: #e0e0e0;
}
QTabWidget::pane {
    border: 1px solid #555;
    border-radius: 3px;
    padding: 5px;
}
QTabBar::tab {
    background: #383838;
    border: 1px solid #555;
    border-bottom-color: #383838;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 8ex;
    padding: 8px 12px;
}
QTabBar::tab:selected, QTabBar::tab:hover {
    background: #555;
}
QTabBar::tab:selected {
    border-color: #777;
    border-bottom-color: #555;
}
QLineEdit, QTextEdit, QComboBox {
    background-color: #252525;
    border: 1px solid #555;
    padding: 5px;
    border-radius: 3px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #0078d7;
}
QPushButton {
    background-color: #0078d7;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 3px;
    min-width: 100px;
}
QPushButton:hover {
    background-color: #005a9e;
}
QPushButton:pressed {
    background-color: #003e6e;
}
QPushButton:disabled {
    background-color: #555;
    color: #aaa;
}
QProgressBar {
    border: 1px solid #555;
    border-radius: 5px;
    text-align: center;
    background-color: #252525;
    color: #e0e0e0;
}
QProgressBar::chunk {
    background-color: #0078d7;
    border-radius: 4px;
}
QLabel {
    background-color: transparent;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: #555;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}
#info_label {
    background-color: #383838;
    padding: 10px;
    border-radius: 5px;
    border: 1px solid #555;
}
#console {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: 'Consolas', 'Courier New', monospace;
    border-radius: 5px;
}
QSplitter::handle {
    background-color: #555;
}
QSplitter::handle:hover {
    background-color: #777;
}
QSplitter::handle:vertical {
    height: 4px;
}
QScrollArea {
    border: none;
}
"""

PROGRESS_RE = re.compile(
    r"frame=\s*(?P<frame>\d+)\s+"
    r"fps=\s*(?P<fps>[\d\.]+)\s+"
    r"q=\s*(?P<q>[\d\.-]+)\s+"
    r".*?"
    r"time=\s*(?P<time>[\d:\.]+)\s+"
    r"bitrate=\s*(?P<bitrate>[\d\.]+)kbits/s\s+"
    r"speed=\s*(?P<speed>[\d\.]+)x"
)

# =============================================================================
# Helper Functions (辅助函数)
# =============================================================================
def time_str_to_seconds(time_str):
    try:
        parts = time_str.split(':')
        seconds = float(parts[-1])
        if len(parts) > 1:
            seconds += int(parts[-2]) * 60
        if len(parts) > 2:
            seconds += int(parts[-3]) * 3600
        return seconds
    except (ValueError, IndexError):
        return 0
    
def resource_path(relative_path):
    """ 获取资源的绝对路径, 适用于开发环境和 PyInstaller 打包环境 """
    try:
        # PyInstaller 创建一个临时文件夹, 并将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)