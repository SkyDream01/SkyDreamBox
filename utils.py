# -*- coding: utf-8 -*-
# SkyDreamBox/utils.py

import re
import sys
import os
import datetime
import html
from typing import Optional, Dict, Any, Union

from logger import get_logger

logger = get_logger()

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
def time_str_to_seconds(time_str: str) -> float:
    """
    将时间字符串转换为秒数
    
    Args:
        time_str: 时间字符串 (格式: HH:MM:SS 或 MM:SS 或 SS)
        
    Returns:
        float: 转换后的秒数
    """
    if not time_str or not isinstance(time_str, str):
        return 0.0
    
    try:
        parts = time_str.split(':')
        seconds = float(parts[-1])
        if len(parts) > 1:
            seconds += int(parts[-2]) * 60
        if len(parts) > 2:
            seconds += int(parts[-3]) * 3600
        return seconds
    except (ValueError, IndexError, TypeError) as e:
        logger.debug(f"时间解析失败 '{time_str}': {e}")
        return 0.0


def resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径
    
    支持 PyInstaller 打包后的环境
    
    Args:
        relative_path: 相对路径
        
    Returns:
        str: 绝对路径
    """
    try:
        # PyInstaller 创建临时文件夹，将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def format_media_info(data: Dict[str, Any]) -> str:
    """
    格式化媒体信息为 HTML 字符串
    
    Args:
        data: FFprobe 输出的 JSON 数据
        
    Returns:
        str: 格式化的 HTML 字符串
    """
    if not isinstance(data, dict):
        logger.warning("无效的媒体数据格式")
        return "<font color='#f1c40f'>无效的媒体数据格式</font>"
    
    def _safe_parse_fraction(frac_str: Optional[str]) -> float:
        """安全解析分数字符串"""
        if not frac_str or not isinstance(frac_str, str):
            return 0.0
        try:
            parts = frac_str.split('/')
            if len(parts) == 2:
                numerator = float(parts[0])
                denominator = float(parts[1])
                if denominator != 0:
                    return numerator / denominator
            return 0.0
        except (ValueError, ZeroDivisionError, TypeError) as e:
            logger.debug(f"分数解析失败 '{frac_str}': {e}")
            return 0.0
    
    def _safe_get_float(data_dict: Dict[str, Any], key: str, default: float = 0.0) -> float:
        """安全获取浮点数值"""
        try:
            value = data_dict.get(key, default)
            return float(value) if value is not None else default
        except (ValueError, TypeError) as e:
            logger.debug(f"浮点数解析失败 '{key}': {e}")
            return default
    
    try:
        fmt = data.get('format', {})
        if not fmt:
            logger.warning("无法获取媒体格式信息")
            return "<font color='#f1c40f'>无法获取媒体格式信息</font>"
        
        filename = html.escape(os.path.basename(fmt.get('filename', 'N/A')))
        duration_sec = _safe_get_float(fmt, 'duration', 0)
        duration_str = str(datetime.timedelta(seconds=int(duration_sec)))
        bit_rate_kbps = int(_safe_get_float(fmt, 'bit_rate', 0) / 1000)
        format_long_name = html.escape(fmt.get('format_long_name', 'N/A'))
        
        info_parts = [
            "<style>",
            "    b { color: #9aace5; }",
            "    td { padding: 2px 8px 2px 0; vertical-align: top; }",
            "</style>",
            "<table>",
            f"    <tr><td><b>文件:</b></td><td>{filename}</td></tr>",
            f"    <tr><td><b>格式:</b></td><td>{format_long_name}</td></tr>",
            f"    <tr><td><b>时长:</b></td><td>{duration_str}</td></tr>",
            f"    <tr><td><b>总比特率:</b></td><td>{bit_rate_kbps:.0f} kb/s</td></tr>",
            "</table><hr>"
        ]
        
        streams = data.get('streams', [])
        if not streams:
            info_parts.append("<font color='#f1c40f'>未检测到媒体流</font>")
        else:
            for stream in streams:
                if not isinstance(stream, dict):
                    continue
                    
                stream_type = stream.get('codec_type')
                if not stream_type:
                    continue
                    
                codec_long_name = html.escape(stream.get('codec_long_name', 'N/A'))
                info_parts.append(f"<b>{stream_type.capitalize()} #{stream.get('index', '?')}:</b><br>")
                info_parts.append("<table>")
                
                if stream_type == 'video':
                    width = stream.get('width', '?')
                    height = stream.get('height', '?')
                    fps = _safe_parse_fraction(stream.get('r_frame_rate', '0/1'))
                    info_parts.append(
                        f"<tr><td>&nbsp;&nbsp;编码:</td><td>{codec_long_name}</td></tr>"
                        f"<tr><td>&nbsp;&nbsp;分辨率:</td><td>{width}x{height}</td></tr>"
                        f"<tr><td>&nbsp;&nbsp;帧率:</td><td>{fps:.2f} fps</td></tr>"
                    )
                elif stream_type == 'audio':
                    channel_layout = html.escape(str(stream.get('channel_layout', 'N/A')))
                    sample_rate = stream.get('sample_rate', 'N/A')
                    info_parts.append(
                        f"<tr><td>&nbsp;&nbsp;编码:</td><td>{codec_long_name}</td></tr>"
                        f"<tr><td>&nbsp;&nbsp;采样率:</td><td>{sample_rate} Hz</td></tr>"
                        f"<tr><td>&nbsp;&nbsp;声道:</td><td>{channel_layout}</td></tr>"
                    )
                info_parts.append("</table><br>")
        
        result = ''.join(info_parts).rstrip().removesuffix("<br>")
        return result if result else "<font color='#f1c40f'>无法解析媒体信息</font>"
        
    except (AttributeError, KeyError, TypeError) as e:
        logger.error(f"解析媒体信息时发生数据格式错误: {e}")
        return f"<font color='#f1c40f'>解析媒体信息出错: 数据格式错误 ({e})</font>"
    except Exception as e:
        logger.exception(f"解析媒体信息时发生未知错误: {e}")
        return f"<font color='#f1c40f'>解析媒体信息出错: 未知错误 ({e})</font>"
