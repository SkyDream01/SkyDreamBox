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

from constants import (PROCESS_TERMINATE_TIMEOUT_MS, PROCESS_KILL_TIMEOUT_MS,
                       FFMPEG_TIMEOUT_MS, FFPROBE_TIMEOUT_MS)

class ProcessHandler:
    """FFmpeg/FFprobe 进程管理器
    
    负责管理 FFmpeg 和 FFprobe 进程的创建、执行和清理。
    确保进程资源正确释放，避免僵尸进程。
    """
    
    def __init__(self, parent=None):
        self._parent = parent
        self.ffmpeg_process = QProcess(parent)
        self.ffprobe_process = QProcess(parent)
        self._setup_process_cleanup(self.ffmpeg_process)
        self._setup_process_cleanup(self.ffprobe_process)
    
    def _setup_process_cleanup(self, process):
        """设置进程清理机制"""
        process.finished.connect(lambda: self._on_process_finished(process))
    
    def _on_process_finished(self, process):
        """进程结束时的清理工作"""
        # 确保进程资源被释放
        if process.state() == QProcess.ProcessState.NotRunning:
            process.close()
    
    def terminate_all(self):
        """终止所有正在运行的进程"""
        for process in [self.ffmpeg_process, self.ffprobe_process]:
            if self._is_process_active(process):
                process.terminate()
                if not process.waitForFinished(PROCESS_TERMINATE_TIMEOUT_MS):
                    process.kill()
                    process.waitForFinished(PROCESS_KILL_TIMEOUT_MS)
                process.close()
    
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

        if not process.waitForFinished(FFMPEG_TIMEOUT_MS):
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

        if not process2.waitForFinished(FFPROBE_TIMEOUT_MS):
            process2.kill()
            return True, "FFmpeg 已找到，但FFprobe响应超时。\n\n媒体信息预览功能可能受限。"
        
        return True, "FFmpeg 和 FFprobe 均已找到。"

    def _is_process_active(self, process):
        """检查进程是否处于活动状态（正在启动或运行中）"""
        state = process.state()
        return state in (QProcess.ProcessState.Starting, QProcess.ProcessState.Running)
    
    def run_ffmpeg(self, command_list):
        if self._is_process_active(self.ffmpeg_process):
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
        """运行 ffprobe 获取媒体信息

        Returns:
            tuple[bool, str]: (是否成功, 错误消息)
        """
        try:
            if self._is_process_active(self.ffprobe_process):
                self.ffprobe_process.terminate()
                if not self.ffprobe_process.waitForFinished(PROCESS_TERMINATE_TIMEOUT_MS):
                    self.ffprobe_process.kill()
                    self.ffprobe_process.waitForFinished(PROCESS_KILL_TIMEOUT_MS)

            if not file_path or not isinstance(file_path, str):
                return False, "无效的文件路径"

            if '\x00' in file_path:
                return False, "路径包含非法空字符"

            ffprobe_path = self._get_ffprobe_path()
            command = [
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path
            ]
            self.ffprobe_process.start(ffprobe_path, command)
            return True, ""
        except (OSError, RuntimeError) as e:
            return False, f"启动 ffprobe 失败: {e}"