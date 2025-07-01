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
        
        # 从原始命令列表中创建参数副本，以防意外修改
        if command_list and command_list[0].lower() == 'ffmpeg':
            args = command_list[1:].copy()
        else:
            args = command_list.copy()

        # 检查用户是否在“专业命令”等模式下自己定义了日志级别
        has_loglevel_flag = any(arg in ['-loglevel', '-v'] for arg in args)

        # 如果用户没有自定义，则自动插入 -loglevel verbose 参数
        # '-loglevel' 是一个全局参数，应放在输入文件 '-i' 之前
        # 增加日志详细度有助于打破进程输出缓冲，从而实现实时进度更新
        if not has_loglevel_flag:
            args.insert(0, 'verbose')
            args.insert(0, '-loglevel')

        # 使用添加了新参数的列表来启动进程
        self.ffmpeg_process.start(FFMPEG_EXEC, ["-nostdin"] + args)
        
        # 为了避免用户困惑，在控制台回显的命令仍然是用户输入的原始命令
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