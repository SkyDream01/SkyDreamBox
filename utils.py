# -*- coding: utf-8 -*-
# SkyDreamBox/utils.py

import re
import sys
import os
import datetime
import html

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
        filename = html.escape(os.path.basename(fmt.get('filename', 'N/A')))
        duration_sec = float(fmt.get('duration', 0))
        duration_str = str(datetime.timedelta(seconds=int(duration_sec)))
        bit_rate_kbps = int(float(fmt.get('bit_rate', 0)) / 1000)
        format_long_name = html.escape(fmt.get('format_long_name', 'N/A'))
        info = f"""
        <style>
            b {{ color: #9aace5; }}
            td {{ padding: 2px 8px 2px 0; vertical-align: top; }}
        </style>
        <table>
            <tr><td><b>文件:</b></td><td>{filename}</td></tr>
            <tr><td><b>格式:</b></td><td>{format_long_name}</td></tr>
            <tr><td><b>时长:</b></td><td>{duration_str}</td></tr>
            <tr><td><b>总比特率:</b></td><td>{bit_rate_kbps:.0f} kb/s</td></tr>
        </table><hr>
        """
        for stream in data.get('streams', []):
            stream_type = stream.get('codec_type')
            codec_long_name = html.escape(stream.get('codec_long_name', 'N/A'))
            info += f"<b>{stream_type.capitalize()} #{stream.get('index')}:</b><br>"
            info += "<table>"
            if stream_type == 'video':
                info += (f"<tr><td>&nbsp;&nbsp;编码:</td><td>{codec_long_name}</td></tr>"
                         f"<tr><td>&nbsp;&nbsp;分辨率:</td><td>{stream.get('width')}x{stream.get('height')}</td></tr>"
                          f"<tr><td>&nbsp;&nbsp;帧率:</td><td>{_safe_parse_fraction(stream.get('r_frame_rate', '0/1')):.2f} fps</td></tr>")
            elif stream_type == 'audio':
                channel_layout = html.escape(str(stream.get('channel_layout', 'N/A')))
                info += (f"<tr><td>&nbsp;&nbsp;编码:</td><td>{codec_long_name}</td></tr>"
                         f"<tr><td>&nbsp;&nbsp;采样率:</td><td>{stream.get('sample_rate')} Hz</td></tr>"
                         f"<tr><td>&nbsp;&nbsp;声道:</td><td>{channel_layout}</td></tr>")
            info += "</table><br>"
        return info.strip().removesuffix("<br>")
    except Exception as e:
        return f"<font color='#f1c40f'>解析媒体信息出错: {e}</font>"
