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

    def run_ffmpeg(self, command_list):
        if self.ffmpeg_process.state() == QProcess.Running:
            return False, "错误: 当前已有任务正在运行。"
        
        # 从命令列表中移除 'ffmpeg' (如果存在)，因为 start 方法会自己处理
        if command_list and command_list[0].lower() == 'ffmpeg':
            args = command_list[1:]
        else:
            args = command_list

        self.ffmpeg_process.start(FFMPEG_EXEC, ["-nostdin"] + args)
        return True, f"执行命令: {FFMPEG_EXEC} {' '.join(args)}"

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