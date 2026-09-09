"""Pure command planning. No Qt objects, filesystem writes or process execution."""
import math
import re
from pathlib import Path

from core.models import CommandPlan, MediaInfo, TaskSpec
from validators import validate_bitrate, validate_fps, validate_resolution


VIDEO_ENCODERS = ["libx264", "libx265", "h264_nvenc", "hevc_nvenc", "h264_qsv", "hevc_qsv", "h264_amf", "hevc_amf", "libaom-av1"]
VIDEO_CODECS = {"libx264": "h264", "libx265": "hevc", "libaom-av1": "av1"}
# Conservative interoperability policy; MKV accepts most common streams.
COMPATIBLE = {
    "mp4": {"video": {"h264", "hevc", "av1", "mpeg4"}, "audio": {"aac", "mp3", "alac", "ac3", "eac3"}, "subtitle": {"mov_text"}},
    "flv": {"video": {"h264", "flv1", "vp6f"}, "audio": {"aac", "mp3"}, "subtitle": set()},
    "mkv": {"video": {"h264", "hevc", "av1", "mpeg4", "vp8", "vp9", "mpeg2video", "ffv1", "mjpeg", "theora"}, "audio": {"aac", "mp3", "flac", "alac", "opus", "vorbis", "ac3", "eac3", "dts", "truehd", "pcm_s16le", "pcm_s24le", "pcm_s32le", "pcm_f32le", "pcm_u8"}, "subtitle": {"subrip", "ass", "ssa", "hdmv_pgs_subtitle", "dvd_subtitle", "webvtt"}},
    "m4a": {"audio": {"aac", "alac"}},
    "aac": {"audio": {"aac"}},
    "flac": {"audio": {"flac"}},
    "mp3": {"audio": {"mp3"}},
    "wav": {"audio": {"pcm_s16le", "pcm_s24le", "pcm_s32le", "pcm_f32le", "pcm_u8"}},
    "mka": {}, "mks": {},
}


def check_compatible(container, stream):
    if container == "mka" and stream.kind != "audio" or container == "mks" and stream.kind != "subtitle":
        raise ValueError(f"{container.upper()} 扩展名与所选流类型不匹配")
    if container in {"mka", "mks"}:
        container = "mkv"
    if stream.codec not in COMPATIBLE.get(container, {}).get(stream.kind, set()):
        raise ValueError(f"{container.upper()} 不支持当前 {stream.kind} 编码 {stream.codec}；请选择兼容容器或主动转换编码")


def stream_at(media, index, kind=None):
    found = next((s for s in media.streams if s.index == int(index)), None)
    if found is None or (kind and found.kind != kind):
        raise ValueError(f"文件 {Path(media.path).name} 中不存在选定的 {kind or ''} 流 #{index}")
    return found


def first_index(media, kind):
    return next((s.index for s in media.streams if s.kind == kind), -1)


def video_args(options, media, available=None):
    codec = options.get("video_codec", "libx264")
    if codec not in VIDEO_ENCODERS:
        raise ValueError("请选择有效的视频编码器")
    if available is not None and codec not in available:
        raise ValueError(f"当前 FFmpeg 不提供编码器 {codec}")
    mode = options.get("quality_mode", "CRF")
    quality = float(options.get("quality", 18))
    if not math.isfinite(quality) or not 0 <= quality <= 51:
        raise ValueError("质量值必须在 0–51 之间")
    args = ["-c:v", codec]
    preset = options.get("preset", "medium")
    if mode == "码率":
        bitrate = options.get("video_bitrate", "6000k")
        if not validate_bitrate(bitrate):
            raise ValueError("视频码率格式无效")
        args += ["-b:v", bitrate]
    elif codec in {"libx264", "libx265", "libaom-av1"}:
        if mode != "CRF":
            raise ValueError("软件编码请选择 CRF 或码率")
        args += ["-crf", str(quality)]
        if codec == "libaom-av1":
            args += ["-b:v", "0"]
    elif "nvenc" in codec:
        if mode != "CQ":
            raise ValueError("NVENC 请选择 CQ 或码率")
        args += ["-rc", "vbr", "-cq", str(quality), "-b:v", "0"]
    elif "qsv" in codec:
        if mode != "CQ":
            raise ValueError("QSV 请选择 CQ 或码率")
        args += ["-global_quality", str(quality)]
    elif "amf" in codec:
        if mode != "CQ":
            raise ValueError("AMF 请选择 CQ 或码率")
        args += ["-rc", "cqp", "-qp_i", str(int(quality)), "-qp_p", str(int(quality))]
    if codec == "libaom-av1":
        if preset not in [str(n) for n in range(9)]:
            raise ValueError("AV1 cpu-used 应为 0–8")
        args += ["-cpu-used", preset]
    elif "amf" in codec:
        if preset not in {"speed", "balanced", "quality"}:
            raise ValueError("AMF 速度参数无效")
        args += ["-quality", preset]
    else:
        presets = {f"p{n}" for n in range(1, 8)} if "nvenc" in codec else {"veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"}
        if codec in {"libx264", "libx265"}:
            presets |= {"ultrafast", "superfast"}
        if preset not in presets:
            raise ValueError("编码速度参数与编码器不兼容")
        args += ["-preset", preset]
    if options.get("fps"):
        if not validate_fps(options["fps"]):
            raise ValueError("帧率必须是有限正数")
        args += ["-r", options["fps"]]
    for key, flag in [("pix_fmt", "-pix_fmt"), ("color_transfer", "-color_trc"), ("color_primaries", "-color_primaries"), ("color_space", "-colorspace")]:
        value = options.get(key, "")
        if value:
            if not re.fullmatch(r"[a-zA-Z0-9_]+", value):
                raise ValueError(f"{key} 参数无效")
            args += [flag, value]
    if media.hdr and not options.get("hdr_confirmed"):
        raise ValueError("检测到 HDR，请检查像素格式和色彩参数并勾选确认")
    return args


def build_plan(task: TaskSpec, media: MediaInfo, media_by_path=None, available=None, attempt_id=None):
    options = task.options
    source = str(Path(task.source).resolve()) if task.source else ""
    output = Path(task.output).resolve() if task.output else None
    inputs = [source] + [str(Path(options[k]).resolve()) for k in ("subtitle", "external_audio") if options.get(k)]
    if task.operation == "legacy":
        inputs += [str(Path(p).resolve()) for p in options.get("inputs", [])]
    if task.operation == "raw":
        args = list(options.get("args", []))
        if not args or any(not isinstance(a, str) or "\0" in a for a in args):
            raise ValueError("专业命令参数无效")
        # Expert commands may have arbitrary outputs; retain native semantics.
        return CommandPlan([args], [0])
    if not output or not output.parent.is_dir():
        raise ValueError("输出目录不存在")
    if str(output).casefold() in {p.casefold() for p in inputs}:
        raise ValueError("输出文件不能与输入文件相同")
    if not Path(source).is_file():
        raise ValueError("输入文件不存在")
    if not re.fullmatch(r"[a-f0-9]{32}", task.id):
        raise ValueError("任务标识无效")
    attempt_id = attempt_id or task.id
    if not re.fullmatch(r"[a-f0-9]{32}", attempt_id):
        raise ValueError("执行标识无效")
    temp_dir = output.parent / f".skydreambox-{attempt_id}"
    temporary = str(temp_dir / ("result" + output.suffix))
    plan = CommandPlan([], [], [(temporary, str(output))], temp_dir=str(temp_dir))
    if task.operation == "legacy":
        args = list(options.get("args", []))
        if not args or any(not isinstance(arg, str) or "\0" in arg for arg in args):
            raise ValueError("高级工具命令参数无效")
        plan.commands = [[arg for arg in args if arg not in {"-y", "-n"}] + ["-n", temporary]]
        plan.durations = [media.duration]
        return plan
    ext = output.suffix[1:].lower()
    args = ["-i", source]
    v = options.get("video_stream", first_index(media, "video"))
    a = options.get("audio_stream", first_index(media, "audio"))

    def audio_mapping(container):
        if int(a) < 0 or options.get("audio_codec") == "none":
            return ["-an"]
        stream = stream_at(media, a, "audio")
        codec = options.get("audio_codec", "copy")
        if codec == "copy":
            check_compatible(container, stream)
            return ["-map", f"0:{a}", "-c:a", "copy"]
        if codec != "aac":
            raise ValueError("视频音频策略仅支持复制、AAC 或移除")
        bitrate = options.get("audio_bitrate", "192k")
        if not validate_bitrate(bitrate):
            raise ValueError("音频码率格式无效")
        return ["-map", f"0:{a}", "-c:a", "aac", "-b:a", bitrate]

    def encode_video():
        stream_at(media, v, "video")
        codec = options.get("video_codec", "libx264")
        from dataclasses import replace
        check_compatible(ext, replace(stream_at(media, v), codec=VIDEO_CODECS.get(codec, "hevc" if "hevc" in codec else "h264")))
        result = ["-map", f"0:{v}"] + video_args(options, media, available)
        filters = []
        if options.get("resolution"):
            if not validate_resolution(options["resolution"]):
                raise ValueError("分辨率格式应为 1920:1080 或 1920:-2")
            filters.append("scale=" + options["resolution"])
        if task.operation == "subtitle":
            subtitle = Path(options.get("subtitle", ""))
            if not subtitle.is_file() or subtitle.suffix.lower() not in {".srt", ".ass", ".ssa"}:
                raise ValueError("请选择有效 SRT/ASS/SSA 字幕")
            # A safe relative filename avoids the two layers of filter escaping on Windows.
            safe_name = "caption" + subtitle.suffix.lower()
            plan.copies[str(temp_dir / safe_name)] = str(subtitle.resolve())
            expression = "subtitles=filename=" + safe_name
            if subtitle.suffix.lower() == ".srt":
                font = options.get("font", "Microsoft YaHei")
                if any(c in font for c in "\\':,;=[]\n\r"):
                    raise ValueError("字幕字体名称含有不支持的字符")
                size = int(options.get("font_size", 24))
                position = int(options.get("alignment", 2))
                if not 8 <= size <= 120 or position not in {2, 5, 8}:
                    raise ValueError("字幕字号或位置无效")
                expression += f":force_style='FontName={font},FontSize={size},Alignment={position}'"
            filters.append(expression)
        if filters:
            result += ["-vf", ",".join(filters)]
        return result

    if task.operation == "video" or (task.operation == "subtitle" and options.get("subtitle_mode") == "burn"):
        args += encode_video() + audio_mapping(ext)
    elif task.operation == "subtitle":
        subtitle = Path(options.get("subtitle", ""))
        if not subtitle.is_file() or subtitle.suffix.lower() not in {".srt", ".ass", ".ssa"}:
            raise ValueError("字幕缺失，请手动配对")
        if ext not in {"mp4", "mkv"}:
            raise ValueError("软字幕输出请选择 MP4 或 MKV")
        check_compatible(ext, stream_at(media, v, "video"))
        args += ["-i", str(subtitle.resolve()), "-map", f"0:{v}", "-c:v", "copy"] + audio_mapping(ext)
        args += ["-map", "1:s:0", "-c:s", "mov_text" if ext == "mp4" else "copy"]
    elif task.operation == "audio":
        stream = stream_at(media, a, "audio")
        fmt = options.get("audio_format", "AAC")
        bits = int(options.get("bits", 0)) or (24 if stream.bits > 16 else 16)
        if bits not in {16, 24, 32}:
            raise ValueError("位深应为 16、24 或 32")
        codec = {"AAC": "aac", "WAV": f"pcm_s{bits}le", "FLAC": "flac", "ALAC": "alac"}.get(fmt)
        extensions = {"AAC": {"aac", "m4a"}, "WAV": {"wav"}, "FLAC": {"flac"}, "ALAC": {"m4a"}}
        if not codec or ext not in extensions[fmt]:
            raise ValueError("输出扩展名与音频格式不匹配")
        args += ["-map", f"0:{a}", "-vn", "-c:a", codec]
        if fmt == "AAC":
            bitrate = options.get("audio_bitrate", "192k")
            if not validate_bitrate(bitrate):
                raise ValueError("音频码率格式无效")
            args += ["-b:a", bitrate]
        elif fmt in {"FLAC", "ALAC"}:
            if bits == 32:
                raise ValueError("FLAC/ALAC 本工具支持 16 或 24 位，请主动选择")
            args += ["-sample_fmt", "s16" if bits == 16 else "s32", "-bits_per_raw_sample", str(bits)]
        if fmt == "FLAC":
            level = int(options.get("compression", 5))
            if not 0 <= level <= 12:
                raise ValueError("FLAC 压缩等级应为 0–12")
            args += ["-compression_level", str(level)]
        for key, flag in [("sample_rate", "-ar"), ("channels", "-ac")]:
            if options.get(key):
                value = int(options[key])
                if value <= 0:
                    raise ValueError("采样率和声道数必须大于零")
                args += [flag, str(value)]
    elif task.operation == "mux":
        selected = options.get("streams", [])
        external = options.get("external_audio", "")
        if not selected and not external:
            raise ValueError("请至少选择一个流")
        if ext not in COMPATIBLE:
            raise ValueError("不支持的输出容器")
        if ext == "flv":
            selected_streams = [stream_at(media, index) for index in selected]
            if sum(s.kind == "video" for s in selected_streams) > 1 or sum(s.kind == "audio" for s in selected_streams) + bool(external) > 1:
                raise ValueError("FLV 仅支持一条视频轨和一条音频轨，请调整选择")
        if external:
            external = str(Path(external).resolve())
            external_info = (media_by_path or {}).get(external)
            if external_info is None:
                raise ValueError("外部音频尚未完成探测")
            external_index = options.get("external_audio_stream", first_index(external_info, "audio"))
            check_compatible(ext, stream_at(external_info, external_index, "audio"))
            args += ["-i", external]
        for index in selected:
            check_compatible(ext, stream_at(media, index))
            args += ["-map", f"0:{index}"]
        if external:
            args += ["-map", f"1:{external_index}"]
        args += ["-c", "copy"]
    elif task.operation == "trim":
        segments = options.get("segments", [])
        if not segments:
            raise ValueError("请添加至少一个片段")
        plan.commands = []
        plan.durations = []
        plan.publications = []
        parts = []
        for number, segment in enumerate(segments, 1):
            start, end = map(float, segment)
            if not all(math.isfinite(t) for t in (start, end)) or start < 0 or end <= start or (media.duration > 0 and end > media.duration + 0.001):
                raise ValueError(f"片段 {number} 超出时长或起止时间无效")
            part = str(temp_dir / f"part{number:03d}{output.suffix}")
            cut = ["-ss", str(start), "-i", source, "-t", str(end - start)]
            if options.get("trim_mode", "copy") == "copy":
                for s in media.streams:
                    if s.kind in {"video", "audio"}:
                        check_compatible(ext, s)
                        cut += ["-map", f"0:{s.index}"]
                cut += ["-c", "copy", "-avoid_negative_ts", "make_zero"]
            elif int(v) >= 0:
                # Output seeking decodes from the beginning to make the cut exact.
                cut = ["-i", source, "-ss", str(start), "-t", str(end - start)]
                cut += encode_video()
                if options.get("audio_codec") == "copy":
                    raise ValueError("精确剪切音频需重新编码，请选择 AAC 或移除音频")
                if int(a) >= 0 and options.get("audio_codec") != "none":
                    bitrate = options.get("audio_bitrate", "192k")
                    if not validate_bitrate(bitrate):
                        raise ValueError("音频码率格式无效")
                    cut += ["-map", f"0:{a}", "-c:a", "aac", "-b:a", bitrate]
                else:
                    cut += ["-an"]
            else:
                stream_at(media, a, "audio")
                codec = {"wav": "pcm_s16le", "flac": "flac", "m4a": "aac", "aac": "aac", "mka": "flac"}.get(ext)
                if not codec:
                    raise ValueError("纯音频精确剪切请选择 WAV、FLAC、AAC、M4A 或 MKA")
                cut = ["-i", source, "-ss", str(start), "-t", str(end - start), "-map", f"0:{a}", "-c:a", codec]
            plan.commands.append(cut + ["-n", part])
            plan.durations.append(end - start)
            parts.append(part)
            final = output if len(segments) == 1 else output.with_name(f"{output.stem}_{number:03d}{output.suffix}")
            if str(final).casefold() in {p.casefold() for p in inputs}:
                raise ValueError("片段输出不能覆盖输入文件")
            plan.publications.append((part, str(final)))
        if options.get("merge") and len(parts) > 1:
            manifest = str(temp_dir / "segments.txt")
            plan.text_files[manifest] = "".join(f"file '{Path(p).name}'\n" for p in parts)
            plan.commands.append(["-f", "concat", "-safe", "1", "-i", manifest, "-c", "copy", "-n", temporary])
            plan.durations.append(sum(plan.durations))
            plan.publications = [(temporary, str(output))]
        return plan
    else:
        raise ValueError("未知任务类型")
    plan.commands = [args + ["-n", temporary]]
    plan.durations = [media.duration]
    return plan
