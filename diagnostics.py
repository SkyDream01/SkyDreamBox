"""Opt-in installation check using the same window, engine and queue as the app."""
import json
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QProcess, QTimer
from PySide6.QtMultimedia import QMediaPlayer

from config import Config
from core.models import TaskStatus
from workbench import Workbench


class InstallationCheck:
    def __init__(self, app, destination):
        self.app = app
        app.setQuitOnLastWindowClosed(False)
        self.destination = Path(destination).resolve()
        self.destination.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="SkyDreamBox-check-")
        self.folder = Path(self.temporary.name)
        self.source = self.folder / "installation-sample.mp4"
        self.window = Workbench(config=Config(self.folder))
        self.window.forms["trim"].preview.audio.setMuted(True)
        self.window.show()
        self.state = "generate"
        self.started = time.monotonic()
        self.result = {"success": False, "checks": []}
        self.generator = QProcess(self.window)
        self.generator.finished.connect(self._generated)
        self.generator.errorOccurred.connect(self._generator_error)
        self.generator.start(self.window.config.get_ffmpeg_path(), ["-v", "error", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=25", "-f", "lavfi", "-i", "sine=frequency=440", "-t", "2", "-c:v", "libx264", "-c:a", "aac", "-n", str(self.source)])
        self.timer = QTimer(self.window)
        self.timer.timeout.connect(self.tick)
        self.timer.start(50)

    def _generated(self, code, status):
        if code or status != QProcess.ExitStatus.NormalExit:
            self.fail(bytes(self.generator.readAllStandardError()).decode("utf-8", "replace"))
            return
        self.window.add_files([str(self.source)])
        self.state = "probe"

    def _generator_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.fail("无法启动 FFmpeg：" + self.generator.errorString())

    def fail(self, error):
        if self.state == "closing":
            return
        self.result["error"] = str(error)
        self.result["success"] = False
        self.finish()

    def finish(self):
        self.state = "closing"
        self.generator.kill()
        self.window.queue.pause()
        self.window.close()

    def tick(self):
        try:
            if self.state == "closing":
                if self.window.isVisible() or self.generator.state() != QProcess.ProcessState.NotRunning:
                    return
                self.timer.stop()
                self.result["checks"].append("窗口关闭与进程收尾")
                self.result["hardware"] = self.window.engine.hardware
                (self.destination / "verification.json").write_text(json.dumps(self.result, ensure_ascii=False, indent=2), encoding="utf-8")
                self.temporary.cleanup()
                self.app.exit(0 if self.result["success"] else 1)
                return
            if time.monotonic() - self.started > 60:
                self.fail("安装检查超时：" + self.state)
                return
            if self.state == "probe" and self.window.engine.ready and str(self.source) in self.window.probe.cache:
                self.result["checks"].append("FFmpeg/FFprobe 检测与媒体探测")
                self.window.enqueue()
                if not self.window.queue.tasks:
                    self.fail(self.window.notification.text())
                    return
                self.window.queue.start()
                self.state = "encode"
            elif self.state == "encode":
                task = self.window.queue.tasks[0]
                if task.status == TaskStatus.FAILED:
                    self.fail(task.error)
                elif task.status == TaskStatus.COMPLETED:
                    self.result["checks"].append("队列压制、输出发布与进度完成")
                    self.window.notification.hide()
                    self.window.grab().save(str(self.destination / "workbench.png"))
                    self.window.navigation.setCurrentRow(1)
                    self.state = "preview"
            elif self.state == "preview":
                preview = self.window.forms["trim"].preview
                if preview.player.error() != QMediaPlayer.Error.NoError:
                    self.fail(preview.player.errorString())
                elif preview.player.duration() > 0:
                    preview.player.setPosition(500)
                    preview.player.play()
                    self.state = "play"
            elif self.state == "play":
                preview = self.window.forms["trim"].preview
                if preview.player.position() > 700 and preview.video.image is not None:
                    preview.player.pause()
                    self.result["checks"].append("Qt Multimedia 视频解码、定位、播放与暂停")
                    self.window.grab().save(str(self.destination / "preview.png"))
                    self.result["success"] = True
                    self.finish()
        except (OSError, ValueError, RuntimeError) as error:
            self.fail(str(error))
