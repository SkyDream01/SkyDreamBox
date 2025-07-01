# -*- coding: utf-8 -*-
# SkyDreamBox/utils.py

import re
import sys
import os
import datetime

# =============================================================================
# Constants and Configurations (常量与配置)
# =============================================================================

# --- 【修改】格式与编码器的映射关系 ---

# 视频格式 -> 兼容的视频编码器列表
VIDEO_FORMAT_CODECS = {
    "mp4": ["libx264", "libx265", "h264_nvenc", "hevc_nvenc"],
    "mkv": ["libx264", "libx265", "h264_nvenc", "hevc_nvenc", "vp9", "copy"],
    "avi": ["libx264", "mpeg4"],
    "mov": ["libx264", "libx265", "h264_nvenc", "hevc_nvenc"],
    "webm": ["vp9", "libvpx-vp9"]
}

# 视频格式 -> 兼容的音频编码器列表 (用于视频处理选项卡)
AUDIO_CODECS_FOR_VIDEO_FORMAT = {
    "mp4": ["aac", "mp3", "alac", "copy"],
    "mkv": ["aac", "mp3", "flac", "opus", "copy"],
    "avi": ["mp3", "aac"],
    "mov": ["aac", "mp3", "alac", "copy"],
    "webm": ["opus", "vorbis", "copy"]
}

# 音频格式 -> 兼容的音频编码器列表
AUDIO_FORMAT_CODECS = {
    "mp3": ["libmp3lame"],
    "flac": ["flac"],
    "aac": ["aac"],
    "wav": ["pcm_s16le (16-bit)", "pcm_s24le (24-bit)", "pcm_s32le (32-bit)", "pcm_u8 (8-bit)"],
    "opus": ["libopus"],
    "alac": ["alac"],
    "m4a": ["aac", "alac", "copy"]
}

# --- 原有常量列表 (现在由上面的映射关系动态生成) ---
VIDEO_FORMATS = list(VIDEO_FORMAT_CODECS.keys())
VIDEO_CODECS = sorted(list(set(codec for codecs in VIDEO_FORMAT_CODECS.values() for codec in codecs)))
AUDIO_CODECS_VIDEO_TAB = sorted(list(set(codec for codecs in AUDIO_CODECS_FOR_VIDEO_FORMAT.values() for codec in codecs)))
AUDIO_FORMATS = list(AUDIO_FORMAT_CODECS.keys())
AUDIO_CODECS_AUDIO_TAB = sorted(list(set(codec for codecs in AUDIO_FORMAT_CODECS.values() for codec in codecs)))

# --- 其他常量 ---
AUDIO_BITRATES = ["128k", "192k", "256k", "320k"]
AUDIO_SAMPLE_RATES = ["(默认)", "24000", "44100", "48000", "96000", "192000"]
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