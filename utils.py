# -*- coding: utf-8 -*-
# SkyDreamBox/utils.py

import re
import sys
import os
import datetime

# =============================================================================
# Constants and Configurations (常量与配置)
# =============================================================================

VIDEO_FORMAT_CODECS = {
    "mp4": ["libx264", "libx265", "h264_nvenc", "hevc_nvenc", "copy"],
    "mkv": ["libx264", "libx265", "h264_nvenc", "hevc_nvenc", "vp9", "copy"],
    "avi": ["libx264", "mpeg4"],
    "mov": ["libx264", "libx265", "h264_nvenc", "hevc_nvenc", "copy"],
    "webm": ["vp9", "libvpx-vp9", "copy"]
}
AUDIO_CODECS_FOR_VIDEO_FORMAT = {
    "mp4": ["aac", "mp3", "alac", "copy"],
    "mkv": ["aac", "mp3", "flac", "opus", "copy"],
    "avi": ["mp3", "aac"],
    "mov": ["aac", "mp3", "alac", "copy"],
    "webm": ["opus", "vorbis", "copy"]
}

AUDIO_FORMAT_CODECS = {
    "mp3": ["libmp3lame"],
    "flac": ["flac"],
    "aac": ["aac"],
    "wav": ["pcm"],
    "opus": ["libopus"],
    "alac": ["alac"],
    "m4a": ["aac", "alac", "copy"]
}

WAV_BIT_DEPTH_CODECS = {
    "16-bit (默认)": "pcm_s16le",
    "24-bit": "pcm_s24le",
    "32-bit": "pcm_s32le",
    "8-bit": "pcm_u8"
}

AUDIO_SAMPLE_FORMATS = {
    "(默认)": None,
    "16-bit": "s16",
    "24-bit": "s32",
    "32-bit (float)": "fltp"
}

VIDEO_FORMATS = list(VIDEO_FORMAT_CODECS.keys())
AUDIO_FORMATS = list(AUDIO_FORMAT_CODECS.keys())
AUDIO_BITRATES = ["128k", "192k", "256k", "320k"]
AUDIO_SAMPLE_RATES = ["(默认)", "24000", "44100", "48000", "96000", "192000"]
SUBTITLE_FORMATS = "字幕文件 (*.srt *.ass *.ssa);;所有文件 (*)"
DEFAULT_COMPRESSION_LEVEL = "5"

RESOLUTION_PRESETS = {
    "720p": 1280,
    "1080p": 1920,
    "2k": 2560,
    "4k": 3840
}


# =============================================================================
# Stylesheet
# =============================================================================
STYLESHEET = """
QWidget {
    background-color: #1a1a2e; /* 深邃的太空蓝 */
    color: #e0e0e0; /* 柔和的灰白文字 */
    font-family: 'Segoe UI', 'Microsoft YaHei', 'Arial';
    font-size: 9pt;
}
QMainWindow, QDialog {
    background-color: #1a1a2e;
}
QGroupBox {
    background-color: #1f1f3a; /* 稍亮的背景 */
    border: 1px solid #1a1a2e;
    border-radius: 4px;
    margin-top: 1ex;
    padding: 5px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 1px 5px;
    background-color: #9aace5; /* 柔和的星光蓝 */
    color: #0f0f2d; /* 标题文字使用深色以保证对比度 */
    border-radius: 4px;
    font-weight: bold;
}
QTabWidget::pane {
    border: 1px solid #1f1f3a;
    border-radius: 3px;
    padding: 2px;
}
QTabBar::tab {
    background: #1f1f3a;
    border: 1px solid #1a1a2e;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 6ex;
    padding: 5px 8px;
    margin-right: 2px;
    color: #bdc3c7;
}
QTabBar::tab:selected, QTabBar::tab:hover {
    background: #9aace5;
    color: #0f0f2d;
    font-weight: bold;
}
QTabBar::tab:selected {
    border-color: #8297d9;
}
QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background-color: #1a1a2e;
    border: 1px solid #1f1f3a;
    padding: 3px;
    border-radius: 4px;
    color: #e0e0e0;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #9aace5;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
    border-left-width: 1px;
    border-left-color: #1f1f3a;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}
QComboBox QAbstractItemView {
    background-color: #1f1f3a;
    selection-background-color: #9aace5;
    selection-color: #0f0f2d;
    border-radius: 4px;
    color: #e0e0e0;
}
QPushButton {
    background-color: #9aace5;
    color: #0f0f2d;
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
    min-width: 80px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #b3c1f0;
}
QPushButton:pressed {
    background-color: #8297d9;
}
QPushButton:disabled {
    background-color: #566573;
    color: #aeb6bf;
}
QProgressBar {
    border: 1px solid #1f1f3a;
    border-radius: 5px;
    text-align: center;
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #9aace5;
    border-radius: 4px;
}
QLabel {
    background-color: transparent;
}
#info_label {
    background-color: #1f1f3a;
    padding: 5px;
    border-radius: 5px;
    border: 1px solid #1a1a2e;
}
#console {
    background-color: #0f0f0f; /* 纯黑控制台背景 */
    color: #d4d4d4;
    font-family: 'Consolas', 'Courier New', monospace;
    border-radius: 5px;
}
QSplitter::handle {
    background-color: #566573;
}
QSplitter::handle:hover {
    background-color: #7f8c8d;
}
QSplitter::handle:vertical {
    height: 1px;
}
QScrollArea {
    border: none;
}
QMenuBar {
    background-color: #1f1f3a;
}
QMenuBar::item {
    padding: 4px 8px;
    background: transparent;
}
QMenuBar::item:selected {
    background: #9aace5;
    color: #0f0f2d;
}
QMenu {
    background-color: #1f1f3a;
    border: 1px solid #9aace5;
}
QMenu::item:selected {
    background-color: #9aace5;
    color: #0f0f2d;
}
"""

# =============================================================================
# Regular Expression for Progress Parsing (进度解析正则表达式)
# =============================================================================
PROGRESS_RE = re.compile(
    r"frame=\s*(?P<frame>\d+)\s+"
    r"fps=\s*(?P<fps>[\d\.]+)\s+"
    r".*?"
    r"time=\s*(?P<time>[\d:\.]+)\s+"
    r".*?"
    r"speed=\s*(?P<speed>[\d\.]+)x"
)

# =============================================================================
# Helper Functions (辅助函数)
# =============================================================================
def time_str_to_seconds(time_str):
    try:
        parts = time_str.split(':')
        seconds = float(parts[-1])
        if len(parts) > 1: seconds += int(parts[-2]) * 60
        if len(parts) > 2: seconds += int(parts[-3]) * 3600
        return seconds
    except (ValueError, IndexError):
        return 0

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def format_media_info(data):
    try:
        fmt = data.get('format', {})
        filename = os.path.basename(fmt.get('filename', 'N/A'))
        duration_sec = float(fmt.get('duration', 0))
        duration_str = str(datetime.timedelta(seconds=int(duration_sec)))
        bit_rate_kbps = int(float(fmt.get('bit_rate', 0)) / 1000)
        info = f"""
        <style>
            b {{ color: #9aace5; }}
            td {{ padding: 2px 8px 2px 0; vertical-align: top; }}
        </style>
        <table>
            <tr><td><b>文件:</b></td><td>{filename}</td></tr>
            <tr><td><b>格式:</b></td><td>{fmt.get('format_long_name', 'N/A')}</td></tr>
            <tr><td><b>时长:</b></td><td>{duration_str}</td></tr>
            <tr><td><b>总比特率:</b></td><td>{bit_rate_kbps:.0f} kb/s</td></tr>
        </table><hr>
        """
        for stream in data.get('streams', []):
            stream_type = stream.get('codec_type')
            info += f"<b>{stream_type.capitalize()} #{stream.get('index')}:</b><br>"
            info += "<table>"
            if stream_type == 'video':
                info += (f"<tr><td>&nbsp;&nbsp;编码:</td><td>{stream.get('codec_long_name', 'N/A')}</td></tr>"
                         f"<tr><td>&nbsp;&nbsp;分辨率:</td><td>{stream.get('width')}x{stream.get('height')}</td></tr>"
                         f"<tr><td>&nbsp;&nbsp;帧率:</td><td>{eval(stream.get('r_frame_rate', '0/1')):.2f} fps</td></tr>")
            elif stream_type == 'audio':
                info += (f"<tr><td>&nbsp;&nbsp;编码:</td><td>{stream.get('codec_long_name', 'N/A')}</td></tr>"
                         f"<tr><td>&nbsp;&nbsp;采样率:</td><td>{stream.get('sample_rate')} Hz</td></tr>"
                         f"<tr><td>&nbsp;&nbsp;声道:</td><td>{stream.get('channel_layout', 'N/A')}</td></tr>")
            info += "</table><br>"
        return info.strip().removesuffix("<br>")
    except Exception as e:
        return f"<font color='#f1c40f'>解析媒体信息出错: {e}</font>"