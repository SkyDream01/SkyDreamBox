"""Asynchronous media and engine inspection for the desktop UI."""
import json
import re
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from core.models import MediaInfo


class ProbeService(QObject):
    ready = Signal(str, object)
    failed = Signal(str, str)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.cache = {}
        self.pending = []
        self.current = ""
        self.process = QProcess(self)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._timeout)

    def request(self, path, refresh=False):
        path = str(Path(path).resolve())
        if path in self.cache and not refresh:
            QTimer.singleShot(0, lambda: self.ready.emit(path, self.cache[path]))
        elif path != self.current and path not in self.pending:
            self.pending.append(path)
            self._next()

    def _next(self):
        if self.current or not self.pending:
            return
        self.current = self.pending.pop(0)
        self.process.start(self.config.get_ffprobe_path(), ["-v", "error", "-show_format", "-show_streams", "-of", "json", self.current])
        self.timer.start(15000)

    def _finish(self, error="", media=None):
        path, self.current = self.current, ""
        self.timer.stop()
        if not path:
            return
        if error:
            self.failed.emit(path, error)
        else:
            self.cache[path] = media
            self.ready.emit(path, media)
        QTimer.singleShot(0, self._next)

    def _finished(self, code, status):
        if not self.current:
            return
        try:
            if code or status != QProcess.ExitStatus.NormalExit:
                raise ValueError(bytes(self.process.readAllStandardError()).decode("utf-8", "replace")[-1000:] or "媒体探测失败")
            media = MediaInfo.from_probe(self.current, json.loads(bytes(self.process.readAllStandardOutput())))
            self._finish(media=media)
        except (ValueError, KeyError, TypeError) as error:
            self._finish(str(error))

    def _error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self._finish("无法启动 FFprobe，请检查设置：" + self.process.errorString())

    def _timeout(self):
        self.process.kill()

    def shutdown(self):
        self.pending.clear()
        self.current = ""
        self.timer.stop()
        self.process.kill()


class EngineService(QObject):
    updated = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.encoders = set()
        self.hardware = {}
        self.message = "正在检测 FFmpeg…"
        self.ready = False
        self.processes = []
        self.generation = 0

    def _run(self, program, args, callback, timeout=10000):
        process = QProcess(self)
        self.processes.append(process)
        timer = QTimer(process)
        timer.setSingleShot(True)
        done = False
        generation = self.generation

        def finish(code=-1, status=QProcess.ExitStatus.CrashExit):
            nonlocal done
            if done:
                return
            done = True
            timer.stop()
            output = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
            error = bytes(process.readAllStandardError()).decode("utf-8", "replace")
            self.processes.remove(process)
            if generation == self.generation:
                callback(code == 0 and status == QProcess.ExitStatus.NormalExit, output, error or process.errorString())
            process.deleteLater()
        process.finished.connect(finish)
        process.errorOccurred.connect(lambda e: finish() if e == QProcess.ProcessError.FailedToStart else None)
        timer.timeout.connect(process.kill)
        process.start(program, args)
        timer.start(timeout)

    def refresh(self):
        self.generation += 1
        self.ready = False
        self.encoders.clear()
        self.hardware.clear()
        self.message = "正在检测引擎及硬件编码…"
        self.updated.emit()

        def probe_checked(ok, out, err):
            if not ok or not out.lower().startswith("ffprobe version"):
                self.message = "FFprobe 不可用，请到设置修复"
            else:
                self.ready = True
                self.message = f"引擎就绪 · {len(self.encoders)} 个编码器"
            self.updated.emit()

        def checked(ok, out, err):
            if not ok or "Encoders:" not in out:
                self.message = "FFmpeg 不可用，请到设置修复"
                self.updated.emit()
                return
            self.encoders = set(re.findall(r"^\s*[VAS][A-Z.]{5}\s+(\S+)", out, re.MULTILINE))
            self._run(self.config.get_ffprobe_path(), ["-version"], probe_checked)
            candidates = [c for c in sorted(self.encoders) if c in {"h264_nvenc", "hevc_nvenc", "h264_qsv", "hevc_qsv", "h264_amf", "hevc_amf"}]

            def next_hardware():
                if not candidates:
                    return
                codec = candidates.pop(0)
                def tested(success, output, error):
                    self.hardware[codec] = success
                    self.updated.emit()
                    next_hardware()
                self._run(self.config.get_ffmpeg_path(), ["-v", "error", "-f", "lavfi", "-i", "color=size=128x128:rate=1", "-frames:v", "1", "-c:v", codec, "-f", "null", "-"], tested)
            next_hardware()
        self._run(self.config.get_ffmpeg_path(), ["-hide_banner", "-encoders"], checked)

    def shutdown(self):
        self.generation += 1
        for process in self.processes[:]:
            process.kill()
