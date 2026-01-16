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
    "mp4": ["libx264", "h264_nvenc", "h264_amf", "h264_qsv", "libx265", "hevc_nvenc", "hevc_amf", "hevc_qsv", "libaom-av1", "copy"],
    "mkv": ["libx264", "h264_nvenc", "h264_amf", "h264_qsv", "libx265", "hevc_nvenc", "hevc_amf", "hevc_qsv", "vp9", "libaom-av1", "copy"],
    "avi": ["libx264", "mpeg4"],
    "mov": ["libx264", "h264_nvenc", "h264_amf", "h264_qsv", "libx265", "hevc_nvenc", "hevc_amf", "hevc_qsv", "copy"],
    "webm": ["vp9", "libvpx-vp9", "libaom-av1", "copy"]
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
/* Material Design Dark Theme for SkyDreamBox */
QWidget {
    background-color: #121212; /* Material Dark background */
    color: #FFFFFF; /* Primary text */
    font-family: 'Segoe UI', 'Microsoft YaHei', 'Arial';
    font-size: 9pt;
}
QMainWindow, QDialog {
    background-color: #121212;
    border: none;
}
QGroupBox {
    background-color: #1E1E1E; /* Surface color */
    border: 1px solid #333333;
    border-radius: 8px;
    margin-top: 1ex;
    padding: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 4px 12px;
    background-color: #2196F3; /* Primary blue */
    color: #000000;
    border-radius: 6px;
    font-weight: bold;
}
QTabWidget::pane {
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 4px;
    background-color: #1E1E1E;
}
QTabBar::tab {
    background: #1E1E1E;
    border: 1px solid #333333;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    min-width: 8ex;
    padding: 8px 16px;
    margin-right: 2px;
    color: #B3B3B3; /* Secondary text */
}
QTabBar::tab:selected, QTabBar::tab:hover {
    background: #2196F3; /* Primary blue */
    color: #000000;
    font-weight: bold;
}
QTabBar::tab:selected {
    border-color: #2196F3;
}
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #2C2C2C;
    border: 1px solid #333333;
    padding: 8px;
    border-radius: 6px;
    color: #FFFFFF;
    selection-background-color: #2196F3;
    selection-color: #000000;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #2196F3;
    padding: 7px; /* Adjust padding to maintain size */
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: #333333;
    border-left-style: solid;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    background-color: #2C2C2C;
}
QComboBox QAbstractItemView {
    background-color: #2C2C2C;
    selection-background-color: #2196F3;
    selection-color: #000000;
    border-radius: 6px;
    color: #FFFFFF;
    border: 1px solid #333333;
}
QPushButton {
    background-color: #2196F3; /* Primary blue */
    color: #000000;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    min-width: 90px;
    font-weight: bold;
    font-size: 9pt;
}
QPushButton:hover {
    background-color: #64B5F6; /* Lighter blue */
}
QPushButton:pressed {
    background-color: #1976D2; /* Darker blue */
}
QPushButton:disabled {
    background-color: #424242;
    color: #666666;
}
QProgressBar {
    border: 1px solid #333333;
    border-radius: 8px;
    text-align: center;
    background-color: #2C2C2C;
    color: #FFFFFF;
    font-weight: bold;
    height: 20px;
}
QProgressBar::chunk {
    background-color: #03A9F4; /* Secondary blue */
    border-radius: 7px;
}
QLabel {
    background-color: transparent;
    color: #FFFFFF;
}
#info_label {
    background-color: #1E1E1E;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #333333;
    color: #B3B3B3;
}
#console {
    background-color: #0A0A0A;
    color: #03A9F4; /* Console text blue */
    font-family: 'Consolas', 'Courier New', monospace;
    border-radius: 8px;
    padding: 8px;
}
QSplitter::handle {
    background-color: #333333;
}
QSplitter::handle:hover {
    background-color: #424242;
}
QSplitter::handle:vertical {
    height: 3px;
}
QSplitter::handle:horizontal {
    width: 3px;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QMenuBar {
    background-color: #1E1E1E;
    color: #FFFFFF;
}
QMenuBar::item {
    padding: 6px 12px;
    background: transparent;
    color: #FFFFFF;
}
QMenuBar::item:selected {
    background: #2196F3;
    color: #000000;
    border-radius: 4px;
}
QMenu {
    background-color: #2C2C2C;
    border: 1px solid #333333;
    border-radius: 6px;
    color: #FFFFFF;
}
QMenu::item:selected {
    background-color: #2196F3;
    color: #000000;
    border-radius: 4px;
}
QCheckBox, QRadioButton {
    color: #FFFFFF;
    spacing: 8px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 2px solid #666666;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #2196F3;
    border-color: #2196F3;
}
QScrollBar:vertical, QScrollBar:horizontal {
    background-color: #1E1E1E;
    border-radius: 4px;
    width: 12px;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background-color: #424242;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background-color: #666666;
}
QScrollBar::add-line, QScrollBar::sub-line {
    background: none;
}
QToolTip {
    background-color: #2C2C2C;
    color: #FFFFFF;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 6px;
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
        def _safe_parse_fraction(frac_str):
            try:
                parts = frac_str.split('/')
                if len(parts) == 2:
                    numerator = float(parts[0])
                    denominator = float(parts[1])
                    if denominator != 0:
                        return numerator / denominator
                return 0.0
            except (ValueError, ZeroDivisionError):
                return 0.0
        
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
                          f"<tr><td>&nbsp;&nbsp;帧率:</td><td>{_safe_parse_fraction(stream.get('r_frame_rate', '0/1')):.2f} fps</td></tr>")
            elif stream_type == 'audio':
                info += (f"<tr><td>&nbsp;&nbsp;编码:</td><td>{stream.get('codec_long_name', 'N/A')}</td></tr>"
                         f"<tr><td>&nbsp;&nbsp;采样率:</td><td>{stream.get('sample_rate')} Hz</td></tr>"
                         f"<tr><td>&nbsp;&nbsp;声道:</td><td>{stream.get('channel_layout', 'N/A')}</td></tr>")
            info += "</table><br>"
        return info.strip().removesuffix("<br>")
    except Exception as e:
        return f"<font color='#f1c40f'>解析媒体信息出错: {e}</font>"