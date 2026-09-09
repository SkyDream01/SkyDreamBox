from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from uuid import uuid4
import math


class TaskStatus(str, Enum):
    PENDING = "待执行"
    RUNNING = "处理中"
    COMPLETED = "已完成"
    FAILED = "失败"
    CANCELLED = "已取消"
    INTERRUPTED = "已中断"


@dataclass
class StreamInfo:
    index: int
    kind: str
    codec: str
    language: str = "und"
    sample_rate: int = 0
    channels: int = 0
    width: int = 0
    height: int = 0
    pix_fmt: str = ""
    color_transfer: str = ""
    color_primaries: str = ""
    color_space: str = ""
    bits: int = 0


@dataclass
class MediaInfo:
    path: str
    duration: float = 0
    streams: list[StreamInfo] = field(default_factory=list)

    @classmethod
    def from_probe(cls, path, data):
        if not isinstance(data, dict) or not isinstance(data.get("streams", []), list):
            raise ValueError("媒体信息格式无效")
        streams = []
        for s in data.get("streams", []):
            def number(key):
                try:
                    return int(s.get(key, 0) or 0)
                except (ValueError, TypeError):
                    return 0
            streams.append(StreamInfo(
                index=int(s["index"]), kind=s.get("codec_type", "unknown"),
                codec=s.get("codec_name", "unknown"),
                language=s.get("tags", {}).get("language", "und"),
                sample_rate=number("sample_rate"), channels=number("channels"),
                width=number("width"), height=number("height"),
                pix_fmt=s.get("pix_fmt", ""), color_transfer=s.get("color_transfer", ""),
                color_primaries=s.get("color_primaries", ""), color_space=s.get("color_space", ""),
                bits=number("bits_per_raw_sample") or number("bits_per_sample"),
            ))
        try:
            duration = float(data.get("format", {}).get("duration", 0))
        except (ValueError, TypeError):
            duration = 0
        return cls(str(Path(path).resolve()), max(0, duration) if math.isfinite(duration) else 0, streams)

    @property
    def hdr(self):
        return any(s.color_transfer in {"smpte2084", "arib-std-b67"} for s in self.streams)


@dataclass
class TaskSpec:
    operation: str
    source: str
    output: str
    options: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)
    status: TaskStatus = TaskStatus.PENDING
    error: str = ""
    progress: int = 0
    detail: str = ""

    def to_dict(self):
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        if data.get("operation") not in {"video", "trim", "subtitle", "audio", "mux", "raw", "legacy"}:
            raise ValueError("队列包含未知任务类型")
        if not isinstance(data.get("options", {}), dict) or not all(isinstance(data.get(k, ""), str) for k in ("source", "output", "id", "error", "detail")):
            raise ValueError("队列任务字段格式无效")
        data["status"] = TaskStatus(data.get("status", TaskStatus.PENDING.value))
        if data["status"] == TaskStatus.RUNNING:
            data["status"] = TaskStatus.INTERRUPTED
            data["detail"] = "上次运行中断，请重试"
        return cls(**data)


@dataclass
class CommandPlan:
    commands: list[list[str]]
    durations: list[float]
    # Final files are published only after every command succeeds.
    publications: list[tuple[str, str]] = field(default_factory=list)
    text_files: dict[str, str] = field(default_factory=dict)
    copies: dict[str, str] = field(default_factory=dict)
    temp_dir: str = ""


def output_path(source, operation, extension, reserved=()):
    source = Path(source)
    candidate = source.with_name(f"{source.stem}_{operation}.{extension}")
    occupied = {str(Path(p).resolve()).casefold() for p in reserved}
    counter = 2
    while candidate.exists() or str(candidate.resolve()).casefold() in occupied:
        candidate = source.with_name(f"{source.stem}_{operation}_{counter}.{extension}")
        counter += 1
    return str(candidate.resolve())


def task_outputs(task):
    """All final filenames, including separately exported trim segments."""
    if not task.output:
        return []
    output = Path(task.output).resolve()
    segments = task.options.get("segments", [])
    if task.operation == "trim" and not task.options.get("merge") and len(segments) > 1:
        return [str(output.with_name(f"{output.stem}_{i:03d}{output.suffix}")) for i in range(1, len(segments) + 1)]
    return [str(output)]


def allocate_output(source, operation, extension, options, reserved=()):
    occupied = list(reserved)
    keys = {str(Path(p).resolve()).casefold() for p in occupied}
    while True:
        candidate = output_path(source, operation, extension, occupied)
        task = TaskSpec(operation, str(source), candidate, options)
        if not any(Path(p).exists() or str(Path(p).resolve()).casefold() in keys for p in task_outputs(task)):
            return candidate
        occupied.append(candidate)
