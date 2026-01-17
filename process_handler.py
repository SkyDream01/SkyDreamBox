# -*- coding: utf-8 -*-
from PySide6.QtCore import QProcess
import os

# =============================================================================
# Process Handler Module (进程处理模块)
# =============================================================================
# 导入配置模块
try:
    from config import get_config
    CONFIG = get_config()
except ImportError:
    # 回退到默认值（兼容性）
    CONFIG = None

class ProcessHandler:
    def __init__(self, parent=None):
        self.ffmpeg_process = QProcess(parent)
        self.ffprobe_process = QProcess(parent)
    
    def _get_ffmpeg_path(self):
        """获取FFmpeg可执行文件路径"""
        if CONFIG:
            return CONFIG.get_ffmpeg_path()
        return "ffmpeg"
    
    def _get_ffprobe_path(self):
        """获取FFprobe可执行文件路径"""
        if CONFIG:
            return CONFIG.get_ffprobe_path()
        return "ffprobe"

    def check_ffmpeg(self):
        """检查ffmpeg是否可用。"""
        ffmpeg_path = self._get_ffmpeg_path()
        ffprobe_path = self._get_ffprobe_path()
        
        # 检查FFmpeg
        process = QProcess()
        process.start(ffmpeg_path, ['-version'])
        
        if not process.waitForStarted():
            if ffmpeg_path != "ffmpeg":
                return False, f"错误: FFmpeg在指定路径未找到: {ffmpeg_path}\n\n请检查FFmpeg路径设置，或使用系统PATH中的FFmpeg。"
            else:
                return False, "错误: FFmpeg未在系统PATH中找到。\n\n请确保您已正确安装FFmpeg，并将其路径添加至系统环境变量中。"

        if not process.waitForFinished(5000):  # 5秒超时
            process.kill()
            return False, "错误: FFmpeg响应超时，无法获取版本信息。"

        if process.exitCode() != 0:
            return False, f"错误: FFmpeg执行出错 (退出码: {process.exitCode()})。\n\n请检查您的FFmpeg安装是否完整。"

        # 检查FFprobe（可选，但建议）
        process2 = QProcess()
        process2.start(ffprobe_path, ['-version'])
        
        if not process2.waitForStarted():
            if ffprobe_path != "ffprobe":
                return True, f"FFmpeg 已找到，但FFprobe在指定路径未找到: {ffprobe_path}\n\n部分功能可能受限。"
            else:
                return True, "FFmpeg 已找到，但FFprobe未在系统PATH中找到。\n\n媒体信息预览功能可能受限。"
        
        if not process2.waitForFinished(5000):
            process2.kill()
            return True, "FFmpeg 已找到，但FFprobe响应超时。\n\n媒体信息预览功能可能受限。"
        
        return True, "FFmpeg 和 FFprobe 均已找到。"

    def run_ffmpeg(self, command_list):
        if self.ffmpeg_process.state() == QProcess.ProcessState.Running:
            return False, "错误: 当前已有任务在运行中。"
        
        ffmpeg_path = self._get_ffmpeg_path()
        
        # 如果命令列表以'ffmpeg'开头，移除它
        if command_list and command_list[0].lower() == 'ffmpeg':
            args = command_list[1:].copy()
        else:
            args = command_list.copy()

        has_loglevel_flag = any(arg in ['-loglevel', '-v'] for arg in args)

        if not has_loglevel_flag:
            args.insert(0, 'verbose')
            args.insert(0, '-loglevel')

        self.ffmpeg_process.start(ffmpeg_path, ["-nostdin"] + args)
        
        # 显示给用户的命令（使用实际路径）
        if ffmpeg_path != "ffmpeg":
            display_path = f'"{ffmpeg_path}"'
        else:
            display_path = "ffmpeg"
        
        original_command_to_display = f"{display_path} {' '.join(args)}"
        return True, f"执行: {original_command_to_display}"

    def run_ffprobe(self, file_path):
        if self.ffprobe_process.state() == QProcess.ProcessState.Running:
            self.ffprobe_process.kill()
            
        ffprobe_path = self._get_ffprobe_path()
        command = [
            "-v", "quiet", 
            "-print_format", "json", 
            "-show_format", 
            "-show_streams", 
            file_path
        ]
        self.ffprobe_process.start(ffprobe_path, command)