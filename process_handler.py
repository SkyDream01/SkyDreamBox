# -*- coding: utf-8 -*-
import os
import subprocess

from PySide6.QtCore import QProcess

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

from constants import (
    PROCESS_TERMINATE_TIMEOUT_MS,
    PROCESS_KILL_TIMEOUT_MS,
    PROCESS_START_TIMEOUT_MS,
    FFMPEG_TIMEOUT_MS,
    FFPROBE_TIMEOUT_MS,
)


class ProcessHandler:
    """FFmpeg/FFprobe 进程管理器

    负责管理 FFmpeg 和 FFprobe 进程的创建、执行和清理。
    """

    def __init__(self, parent=None):
        self._parent = parent
        self.ffmpeg_process = QProcess(parent)
        self.ffprobe_process = QProcess(parent)

    def terminate_all(self):
        """终止所有正在运行的进程"""
        for process in [self.ffmpeg_process, self.ffprobe_process]:
            if self._is_process_active(process):
                process.terminate()
                if not process.waitForFinished(PROCESS_TERMINATE_TIMEOUT_MS):
                    process.kill()
                    process.waitForFinished(PROCESS_KILL_TIMEOUT_MS)

            # QProcess 可以在结束后复用；这里仅在应用退出时关闭其 I/O 设备。
            if process.state() == QProcess.ProcessState.NotRunning:
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

    @staticmethod
    def _version_output(process: QProcess) -> str:
        """返回工具的版本输出（不同构建可能写入 stdout 或 stderr）。"""
        output = bytes(process.readAllStandardOutput()) + bytes(
            process.readAllStandardError()
        )
        return output.decode("utf-8", "ignore").lower()

    def check_ffmpeg(self):
        """检查ffmpeg是否可用。"""
        ffmpeg_path = self._get_ffmpeg_path()
        ffprobe_path = self._get_ffprobe_path()

        # 检查FFmpeg
        process = QProcess()
        process.start(ffmpeg_path, ["-version"])

        if not process.waitForStarted(PROCESS_START_TIMEOUT_MS):
            if ffmpeg_path != "ffmpeg":
                return (
                    False,
                    f"错误: FFmpeg在指定路径未找到: {ffmpeg_path}\n\n请检查FFmpeg路径设置，或使用系统PATH中的FFmpeg。",
                )
            else:
                return (
                    False,
                    "错误: FFmpeg未在系统PATH中找到。\n\n请确保您已正确安装FFmpeg，并将其路径添加至系统环境变量中。",
                )

        if not process.waitForFinished(FFMPEG_TIMEOUT_MS):
            process.kill()
            process.waitForFinished(PROCESS_KILL_TIMEOUT_MS)
            return False, "错误: FFmpeg响应超时，无法获取版本信息。"

        if (
            process.exitStatus() != QProcess.ExitStatus.NormalExit
            or process.exitCode() != 0
        ):
            return (
                False,
                f"错误: FFmpeg执行出错 (退出码: {process.exitCode()})。\n\n请检查您的FFmpeg安装是否完整。",
            )

        if "ffmpeg version" not in self._version_output(process):
            return False, "错误: 指定程序不是有效的 FFmpeg 可执行文件。"

        # 检查FFprobe（可选，但建议）
        process2 = QProcess()
        process2.start(ffprobe_path, ["-version"])

        if not process2.waitForStarted(PROCESS_START_TIMEOUT_MS):
            if ffprobe_path != "ffprobe":
                return (
                    True,
                    f"FFmpeg 已找到，但FFprobe在指定路径未找到: {ffprobe_path}\n\n部分功能可能受限。",
                )
            else:
                return (
                    True,
                    "FFmpeg 已找到，但FFprobe未在系统PATH中找到。\n\n媒体信息预览功能可能受限。",
                )

        if not process2.waitForFinished(FFPROBE_TIMEOUT_MS):
            process2.kill()
            process2.waitForFinished(PROCESS_KILL_TIMEOUT_MS)
            return (
                True,
                "FFmpeg 已找到，但FFprobe响应超时。\n\n媒体信息预览功能可能受限。",
            )

        if (
            process2.exitStatus() != QProcess.ExitStatus.NormalExit
            or process2.exitCode() != 0
        ):
            return True, (
                f"FFmpeg 已找到，但FFprobe执行失败 (退出码: {process2.exitCode()})。"
                "\n\n媒体信息预览功能可能受限。"
            )

        if "ffprobe version" not in self._version_output(process2):
            return (
                True,
                "FFmpeg 已找到，但指定程序不是有效的 FFprobe 可执行文件。"
                "\n\n媒体信息预览功能可能受限。",
            )

        return True, "FFmpeg 和 FFprobe 均已找到。"

    def _is_process_active(self, process):
        """检查进程是否处于活动状态（正在启动或运行中）"""
        state = process.state()
        return state in (QProcess.ProcessState.Starting, QProcess.ProcessState.Running)

    def run_ffmpeg(self, command_list):
        """异步运行 FFmpeg 命令。"""
        if self._is_process_active(self.ffmpeg_process):
            return False, "错误: 当前已有任务在运行中。"

        if not command_list:
            return False, "错误: FFmpeg 命令不能为空。"

        command_list = list(command_list)
        if not all(
            isinstance(argument, str) and "\x00" not in argument
            for argument in command_list
        ):
            return False, "错误: FFmpeg 命令包含无效参数。"

        ffmpeg_path = self._get_ffmpeg_path()

        # 专业命令页可使用 ffmpeg 或 ffmpeg.exe；实际可执行文件始终由设置决定。
        command_name = os.path.basename(command_list[0]).lower()
        if command_name in {"ffmpeg", "ffmpeg.exe"}:
            args = command_list[1:].copy()
        else:
            args = command_list.copy()

        has_loglevel_flag = any(arg in ["-loglevel", "-v"] for arg in args)

        if not has_loglevel_flag:
            args.insert(0, "verbose")
            args.insert(0, "-loglevel")

        full_command = ["-nostdin"] + args
        self.ffmpeg_process.start(ffmpeg_path, full_command)
        if not self.ffmpeg_process.waitForStarted(PROCESS_START_TIMEOUT_MS):
            error_message = self.ffmpeg_process.errorString() or "未知错误"
            return False, f"错误: 无法启动 FFmpeg: {error_message}"

        display_command = subprocess.list2cmdline([ffmpeg_path] + full_command)
        return True, f"执行: {display_command}"

    def run_ffprobe(self, file_path):
        """运行 ffprobe 获取媒体信息

        Returns:
            tuple[bool, str]: (是否成功, 错误消息)
        """
        try:
            if self._is_process_active(self.ffprobe_process):
                self.ffprobe_process.terminate()
                if not self.ffprobe_process.waitForFinished(
                    PROCESS_TERMINATE_TIMEOUT_MS
                ):
                    self.ffprobe_process.kill()
                    self.ffprobe_process.waitForFinished(PROCESS_KILL_TIMEOUT_MS)

            if not file_path or not isinstance(file_path, str):
                return False, "无效的文件路径"

            if "\x00" in file_path:
                return False, "路径包含非法空字符"

            ffprobe_path = self._get_ffprobe_path()
            command = [
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                file_path,
            ]
            self.ffprobe_process.start(ffprobe_path, command)
            if not self.ffprobe_process.waitForStarted(PROCESS_START_TIMEOUT_MS):
                error_message = self.ffprobe_process.errorString() or "未知错误"
                return False, f"无法启动 ffprobe: {error_message}"
            return True, ""
        except (OSError, RuntimeError) as e:
            return False, f"启动 ffprobe 失败: {e}"
