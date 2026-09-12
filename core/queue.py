"""Sequential task execution, persistence, cancellation and atomic publication."""
import copy
import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from core.commands import build_plan
from core.models import MediaInfo, TaskSpec, TaskStatus


class TaskQueue(QObject):
    changed = Signal()
    log = Signal(str, str)
    storage_error = Signal(str)
    idle = Signal()

    def __init__(self, config, probe, engine=None, storage=None, parent=None):
        super().__init__(parent)
        self.config, self.probe, self.engine = config, probe, engine
        self.storage = Path(storage) if storage else config.config_dir / "queue.json"
        self.tasks = []
        self.current = None
        self.plan = None
        self.paused = True
        self.stopping = False
        self.step = 0
        self.buffer = ""
        self.errors = ""
        self.load_error = ""
        self.waiting = set()
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._stdout)
        self.process.readyReadStandardError.connect(self._stderr)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)
        self.kill_timer = QTimer(self)
        self.kill_timer.setSingleShot(True)
        self.kill_timer.timeout.connect(self.process.kill)
        self.probe.ready.connect(self._probed)
        self.probe.failed.connect(self._probe_failed)
        self._load()

    def _load(self):
        if not self.storage.exists():
            return
        try:
            data = json.loads(self.storage.read_text(encoding="utf-8"))
            if data.get("version") != 1 or not isinstance(data.get("tasks"), list):
                raise ValueError("不支持的队列格式")
            self.tasks = [TaskSpec.from_dict(item) for item in data["tasks"]]
        except (OSError, ValueError, TypeError, KeyError) as error:
            self.load_error = f"队列读取失败，原文件保留：{error}"

    def save(self):
        if self.load_error:
            self.storage_error.emit(self.load_error)
            return False
        try:
            self.storage.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.storage.with_suffix(".tmp")
            temporary.write_text(json.dumps({"version": 1, "tasks": [t.to_dict() for t in self.tasks]}, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temporary, self.storage)
            return True
        except OSError as error:
            self.storage_error.emit(f"队列保存失败：{error}")
            return False

    def _changed(self):
        self.save()
        self.changed.emit()

    def add(self, task):
        task = copy.deepcopy(task)
        self.tasks.append(task)
        self._changed()
        return task

    def update(self, task_id, replacement):
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                if task is self.current or task.status == TaskStatus.COMPLETED:
                    raise ValueError("只能编辑待办或未完成任务")
                replacement = copy.deepcopy(replacement)
                replacement.id = task.id
                self.tasks[i] = replacement
                self._changed()
                return

    def remove(self, task_id):
        self.tasks = [t for t in self.tasks if t.id != task_id or t is self.current]
        self._changed()

    def clear(self):
        """Remove queue records while keeping the active task and its process."""
        self.tasks = [t for t in self.tasks if t is self.current]
        self._changed()

    def move(self, task_id, offset):
        index = next((i for i, t in enumerate(self.tasks) if t.id == task_id), -1)
        target = index + offset
        if index >= 0 and 0 <= target < len(self.tasks) and self.tasks[index] is not self.current:
            self.tasks.insert(target, self.tasks.pop(index))
            self._changed()

    def retry(self, task_id):
        task = next((t for t in self.tasks if t.id == task_id), None)
        if task and task.status in {TaskStatus.FAILED, TaskStatus.INTERRUPTED, TaskStatus.CANCELLED}:
            task.status, task.error, task.progress = TaskStatus.PENDING, "", 0
            self._changed()

    def start(self):
        if self.engine and not self.engine.ready:
            self.storage_error.emit("引擎尚未就绪，请在设置中检查后再开始队列")
            return
        self.paused = False
        self._next()

    def pause(self):
        self.paused = True
        self.changed.emit()

    def _next(self):
        if self.current or self.paused:
            return
        if self.engine and not self.engine.ready:
            self.paused = True
            self.storage_error.emit("引擎尚未就绪，队列已暂停")
            self.changed.emit()
            return
        self.current = next((t for t in self.tasks if t.status == TaskStatus.PENDING), None)
        if not self.current:
            self.idle.emit()
            return
        self.stopping = False
        self.errors = ""
        self.current.status = TaskStatus.RUNNING
        self.current.detail = "检查媒体与参数…"
        self._changed()
        if self.current.operation == "raw":
            self._prepare()
            return
        self.waiting = {str(Path(p).resolve()) for p in [self.current.source, self.current.options.get("external_audio", "")] if p}
        for path in list(self.waiting):
            self.probe.request(path, refresh=True)

    def _probed(self, path, media):
        if self.current and path in self.waiting:
            self.waiting.remove(path)
            if not self.waiting:
                self._prepare()

    def _probe_failed(self, path, error):
        if self.current and path in self.waiting:
            self._complete(TaskStatus.FAILED, error)

    def _prepare(self):
        try:
            task = self.current
            if self.engine and not self.engine.ready:
                raise ValueError("FFmpeg/FFprobe 尚未就绪，请检查设置")
            media = self.probe.cache.get(str(Path(task.source).resolve()), MediaInfo(task.source))
            codec = task.options.get("video_codec", "")
            encoding = task.operation == "video" or task.operation == "subtitle" and task.options.get("subtitle_mode") == "burn" or task.operation == "trim" and task.options.get("trim_mode") == "encode" and any(s.kind == "video" for s in media.streams)
            if encoding and self.engine and any(k in codec for k in ("nvenc", "qsv", "amf")) and self.engine.hardware.get(codec) is not True:
                raise ValueError(f"硬件编码器 {codec} 尚未通过设备检测")
            self.plan = build_plan(task, media, self.probe.cache, self.engine.encoders if self.engine else None, attempt_id=uuid4().hex)
            overwrite = task.options.get("overwrite", False)
            protected_inputs = {
                str(Path(path).resolve()).casefold()
                for queued in self.tasks
                for path in (queued.source, queued.options.get("subtitle", ""), queued.options.get("external_audio", ""))
                if path
            }
            for _, final in self.plan.publications:
                if str(Path(final).resolve()).casefold() in protected_inputs:
                    raise ValueError("输出不能覆盖队列中任一任务的输入文件")
                if Path(final).exists() and not overwrite:
                    raise ValueError(f"输出已存在：{final}，请修改输出路径")
            if self.plan.temp_dir:
                # Never remove or reuse a pre-existing directory after a crash.
                Path(self.plan.temp_dir).mkdir(exist_ok=False)
                self.owns_temp = True
                for path, content in self.plan.text_files.items():
                    Path(path).write_text(content, encoding="utf-8")
                for destination, source in self.plan.copies.items():
                    shutil.copyfile(source, destination)
            self.step = 0
            self._run_step()
        except (ValueError, OSError, TypeError, KeyError) as error:
            self._complete(TaskStatus.FAILED, str(error))

    def _run_step(self):
        self.buffer, self.errors = "", ""
        self.process.setWorkingDirectory(self.plan.temp_dir or str(Path.cwd()))
        args = self.plan.commands[self.step]
        self.log.emit(self.current.id, "参数：" + repr(args) + "\n")
        self.process.start(self.config.get_ffmpeg_path(), ["-hide_banner", "-nostdin", "-progress", "pipe:1", "-nostats"] + args)

    def _stdout(self):
        self.buffer += bytes(self.process.readAllStandardOutput()).decode("utf-8", "replace")
        lines = self.buffer.split("\n")
        self.buffer = lines.pop()
        if not self.current:
            return
        for line in lines:
            key, _, value = line.strip().partition("=")
            if key == "out_time_us":
                try:
                    seconds = max(0, int(value) / 1_000_000)
                    duration = self.plan.durations[self.step]
                    fraction = min(1, seconds / duration) if duration > 0 else 0
                    total = sum(self.plan.durations)
                    done = sum(self.plan.durations[:self.step]) + duration * fraction
                    self.current.progress = min(99, int(100 * done / total)) if total else 0
                    self.seconds = seconds
                except ValueError:
                    pass
            elif key == "speed":
                try:
                    speed = float(value.rstrip("x"))
                    remaining = max(0, self.plan.durations[self.step] - getattr(self, "seconds", 0))
                    eta = f"{int(remaining / speed)} 秒" if speed > 0 else "未知"
                except ValueError:
                    eta = "未知"
                self.current.detail = f"步骤 {self.step + 1}/{len(self.plan.commands)} · {value} · 本步剩余 {eta}"
        self.changed.emit()

    def _stderr(self):
        message = bytes(self.process.readAllStandardError()).decode("utf-8", "replace")
        self.errors = (self.errors + message)[-6000:]
        if self.current:
            self.log.emit(self.current.id, message)

    def _finished(self, code, status):
        self.kill_timer.stop()
        self._stdout()
        self._stderr()
        if not self.current:
            return
        if self.stopping:
            self._complete(TaskStatus.CANCELLED, "用户停止了任务")
        elif code or status != QProcess.ExitStatus.NormalExit:
            self._complete(TaskStatus.FAILED, self.errors.strip() or f"FFmpeg 退出码 {code}")
        elif self.step + 1 < len(self.plan.commands):
            self.step += 1
            self._run_step()
        else:
            try:
                for temporary, _ in self.plan.publications:
                    if not Path(temporary).is_file() or not Path(temporary).stat().st_size:
                        raise ValueError("FFmpeg 未生成有效输出")
                self._publish()
                self._complete(TaskStatus.COMPLETED)
            except (OSError, ValueError) as error:
                self._complete(TaskStatus.FAILED, str(error))

    def _publish(self):
        published, backups = [], []
        try:
            for number, (temporary, final) in enumerate(self.plan.publications):
                if self.current.options.get("overwrite", False) and Path(final).exists():
                    backup = str(Path(self.plan.temp_dir) / f"backup{number}")
                    os.replace(final, backup)
                    backups.append((backup, final))
                # Windows rename is atomic and refuses to replace an existing file.
                # POSIX rename replaces by default, so use an exclusive hard link there.
                if os.name == "nt":
                    os.rename(temporary, final)
                else:
                    os.link(temporary, final)
                published.append(final)
            # Keep backups until the entire publication succeeds; normal cleanup
            # removes them. A failed backup deletion must never trigger rollback.
        except OSError as publication_error:
            try:
                for final in published:
                    Path(final).unlink(missing_ok=True)
                for backup, final in backups:
                    os.replace(backup, final)
            except OSError as rollback_error:
                self.owns_temp = False
                raise OSError(f"输出发布失败，原文件备份保留在 {self.plan.temp_dir}：{rollback_error}") from publication_error
            raise

    def _error(self, error):
        if error == QProcess.ProcessError.FailedToStart and self.current:
            self._complete(TaskStatus.FAILED, "无法启动 FFmpeg：" + self.process.errorString())

    def cancel(self):
        if not self.current:
            return
        self.stopping = True
        if self.process.state() == QProcess.ProcessState.NotRunning:
            self._complete(TaskStatus.CANCELLED, "用户停止了任务")
        else:
            self.process.terminate()
            self.kill_timer.start(2000)

    def _complete(self, status, error=""):
        if not self.current:
            return
        self.kill_timer.stop()
        self.waiting.clear()
        self.current.status, self.current.error = status, error
        self.current.detail = error.splitlines()[-1] if error else status.value
        if status == TaskStatus.COMPLETED:
            self.current.progress = 100
        if self.plan and self.plan.temp_dir and getattr(self, "owns_temp", False):
            # Only the freshly created task directory is owned by this execution.
            try:
                shutil.rmtree(self.plan.temp_dir)
            except OSError as cleanup_error:
                self.log.emit(self.current.id, f"临时目录未能清理：{cleanup_error}\n")
        self.owns_temp = False
        self.plan = None
        self.current = None
        self._changed()
        if self.paused:
            self.idle.emit()
        else:
            QTimer.singleShot(0, self._next)
