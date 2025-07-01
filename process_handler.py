# -*- coding: utf-8 -*-
from PyQt5.QtCore import QProcess

# =============================================================================
# Process Handler Module (进程处理模块)
# =============================================================================
FFMPEG_EXEC = "ffmpeg"
FFPROBE_EXEC = "ffprobe"

class ProcessHandler:
    def __init__(self, parent=None):
        self.ffmpeg_process = QProcess(parent)
        self.ffprobe_process = QProcess(parent)

    def check_ffmpeg(self):
        """检查ffmpeg是否在系统路径中可用。"""
        process = QProcess()
        process.start(FFMPEG_EXEC, ['-version'])
        if not process.waitForStarted():
            return False, f"错误: FFmpeg ({FFMPEG_EXEC}) 未找到或无法启动。\n\n请确保您已正确安装FFmpeg，并将其路径添加至系统环境变量中。"

        if not process.waitForFinished(5000):  # 5秒超时
            process.kill()
            return False, "错误: FFmpeg进程超时，无法获取版本信息。"

        if process.exitCode() != 0:
            return False, f"错误: FFmpeg执行出错 (退出码: {process.exitCode()})。\n\n请检查您的FFmpeg安装是否完整。"

        return True, "FFmpeg 已找到。"

    def run_ffmpeg(self, command_list):
        if self.ffmpeg_process.state() == QProcess.Running:
            return False, "错误: 当前已有任务正在运行。"
        
        if command_list and command_list[0].lower() == 'ffmpeg':
            args = command_list[1:].copy()
        else:
            args = command_list.copy()

        has_loglevel_flag = any(arg in ['-loglevel', '-v'] for arg in args)

        if not has_loglevel_flag:
            args.insert(0, 'verbose')
            args.insert(0, '-loglevel')

        self.ffmpeg_process.start(FFMPEG_EXEC, ["-nostdin"] + args)
        
        original_command_to_display = f"{FFMPEG_EXEC} {' '.join(command_list[1:])}"
        return True, f"执行命令: {original_command_to_display}"

    def run_ffprobe(self, file_path):
        if self.ffprobe_process.state() == QProcess.Running:
            self.ffprobe_process.kill()
            
        command = [
            "-v", "quiet", 
            "-print_format", "json", 
            "-show_format", 
            "-show_streams", 
            file_path
        ]
        self.ffprobe_process.start(FFPROBE_EXEC, command)