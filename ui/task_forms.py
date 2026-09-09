"""Small, reusable task editors. Values are serialized before entering the queue."""
from PySide6.QtCore import Qt, QUrl, Slot, QMetaObject, Q_ARG
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoSink, QVideoFrame
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QComboBox,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QGroupBox,
    QListWidget, QSlider,
)

from core.commands import VIDEO_ENCODERS


def combo(items):
    widget = QComboBox()
    widget.addItems(items)
    return widget


def button(text, callback, primary=False):
    widget = QPushButton(text)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    widget.clicked.connect(callback)
    if primary:
        widget.setObjectName("primary")
    return widget


def note(text):
    label = QLabel(text)
    label.setWordWrap(True)
    label.setObjectName("muted")
    return label


class Fields(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.form = QFormLayout(self)
        self.form.setContentsMargins(0, 4, 0, 4)
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.fields = {}

    def add(self, key, label, widget):
        self.fields[key] = widget
        self.form.addRow(label, widget)
        return widget

    def values(self):
        values = {}
        for key, widget in self.fields.items():
            if isinstance(widget, QComboBox):
                values[key] = widget.currentData() if widget.currentData() is not None else widget.currentText()
            elif isinstance(widget, QCheckBox):
                values[key] = widget.isChecked()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                values[key] = widget.value()
            else:
                values[key] = widget.text().strip()
        return values

    def restore(self, values):
        for key, widget in self.fields.items():
            if key not in values:
                continue
            value = values[key]
            if isinstance(widget, QComboBox):
                index = widget.findData(value)
                if index < 0:
                    index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(value)
            else:
                widget.setText(str(value))


class VideoFields(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.basic = Fields()
        self.codec = self.basic.add("video_codec", "视频编码", combo(VIDEO_ENCODERS))
        self.mode = self.basic.add("quality_mode", "质量控制", combo(["CRF", "码率"]))
        quality = QDoubleSpinBox()
        quality.setRange(0, 51)
        quality.setValue(18)
        self.basic.add("quality", "质量值 · 越低越清晰", quality)
        self.preset = self.basic.add("preset", "编码速度", combo([]))
        self.basic.add("video_bitrate", "视频码率", QLineEdit("6000k"))
        self.basic.add("audio_codec", "音频处理", self._choices([("无损复制", "copy"), ("转为 AAC", "aac"), ("移除音频", "none")]))
        self.basic.add("audio_bitrate", "AAC 码率", QLineEdit("192k"))
        self.basic.fields["audio_codec"].currentIndexChanged.connect(self._audio_changed)
        layout.addWidget(self.basic)
        self.more = QGroupBox("高级参数")
        self.more.setCheckable(True)
        self.more.setChecked(False)
        more_layout = QVBoxLayout(self.more)
        self.advanced = Fields()
        for key, label, placeholder in [("resolution", "分辨率", "保持原始，如 1920:-2"), ("fps", "帧率", "保持原始"), ("pix_fmt", "像素格式", "自动，如 yuv420p10le"), ("color_transfer", "传递函数", "保持源信息，如 smpte2084"), ("color_primaries", "色彩原色", "保持源信息，如 bt2020"), ("color_space", "色彩矩阵", "保持源信息，如 bt2020nc")]:
            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            self.advanced.add(key, label, edit)
        self.advanced.add("hdr_confirmed", "HDR", QCheckBox("已检查 HDR 像素格式与色彩参数"))
        more_layout.addWidget(self.advanced)
        self.advanced.hide()
        self.more.toggled.connect(self.advanced.setVisible)
        layout.addWidget(self.more)
        self.codec.currentTextChanged.connect(self._codec_changed)
        self.mode.currentTextChanged.connect(self._mode_changed)
        self._codec_changed()
        self._audio_changed()

    @staticmethod
    def _choices(items):
        widget = QComboBox()
        for text, data in items:
            widget.addItem(text, data)
        return widget

    def _codec_changed(self):
        codec = self.codec.currentText()
        self.mode.clear()
        self.mode.addItems(["CQ" if any(k in codec for k in ("nvenc", "qsv", "amf")) else "CRF", "码率"])
        self.preset.clear()
        if "nvenc" in codec:
            self.preset.addItems([f"p{i}" for i in range(1, 8)])
            self.preset.setCurrentText("p5")
        elif "amf" in codec:
            self.preset.addItems(["speed", "balanced", "quality"])
            self.preset.setCurrentText("quality")
        elif codec == "libaom-av1":
            self.preset.addItems([str(i) for i in range(9)])
            self.preset.setCurrentText("4")
        else:
            presets = ["veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
            if codec in {"libx264", "libx265"}:
                presets = ["ultrafast", "superfast"] + presets
            self.preset.addItems(presets)
            self.preset.setCurrentText("medium")
        self._mode_changed()

    def _mode_changed(self):
        bitrate = self.mode.currentText() == "码率"
        self.basic.form.setRowVisible(self.basic.fields["video_bitrate"], bitrate)
        self.basic.form.setRowVisible(self.basic.fields["quality"], not bitrate)

    def _audio_changed(self):
        self.basic.form.setRowVisible(self.basic.fields["audio_bitrate"], self.basic.fields["audio_codec"].currentData() == "aac")

    def values(self):
        return {**self.basic.values(), **self.advanced.values()}

    def restore(self, values):
        self.basic.restore(values)
        self.advanced.restore(values)


class FrameView(QLabel):
    def __init__(self):
        super().__init__("媒体预览")
        self.image = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: #17253b; color: #a8bdd9; border-radius: 6px;")

    def display(self, image):
        self.image = image
        if image and not image.isNull():
            self.setPixmap(QPixmap.fromImage(image).scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.display(self.image)


class Preview(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.video = FrameView()
        self.video.setMinimumHeight(140)
        self.video.setMaximumHeight(240)
        self.player = QMediaPlayer(self)
        self.loaded_path = ""
        self.closed = False
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.sink = QVideoSink(self)
        self.player.setVideoSink(self.sink)
        # Frames can originate on a decoder thread. Never run Python UI callbacks
        # synchronously there: stop() joins that thread while Python owns the GIL.
        self.sink.videoFrameChanged.connect(self._frame, Qt.ConnectionType.QueuedConnection)
        layout.addWidget(self.video)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.sliderMoved.connect(self.player.setPosition)
        self.player.durationChanged.connect(self._duration, Qt.ConnectionType.QueuedConnection)
        self.player.positionChanged.connect(self._position, Qt.ConnectionType.QueuedConnection)
        layout.addWidget(self.slider)
        row = QHBoxLayout()
        self.play = button("播放 / 暂停", self.toggle)
        row.addWidget(self.play)
        self.position = QLabel("00:00.000")
        row.addWidget(self.position)
        row.addStretch()
        layout.addLayout(row)
        self.message = note("选择文件以预览；音频素材同样支持定位截取。")
        layout.addWidget(self.message)
        self.player.errorOccurred.connect(self._preview_error, Qt.ConnectionType.QueuedConnection)

    @Slot(QVideoFrame)
    def _frame(self, frame):
        if frame.isValid() and not self.closed:
            self.video.display(frame.toImage().copy())

    @Slot(int)
    def _duration(self, milliseconds):
        self.slider.setRange(0, milliseconds)

    def _preview_error(self, *args):
        self.message.setText("无法预览此媒体，仍可输入时间处理：" + self.player.errorString())

    def _position(self, ms):
        if not self.slider.isSliderDown():
            self.slider.setValue(ms)
        self.position.setText(f"{ms // 60000:02d}:{ms % 60000 / 1000:06.3f}")

    def load(self, path):
        self.loaded_path = path
        self.closed = False
        QMetaObject.invokeMethod(self.player, "stop", Qt.ConnectionType.QueuedConnection)
        self.video.image = None
        self.video.clear()
        self.video.setText("正在读取预览…")
        QMetaObject.invokeMethod(self.player, "setSource", Qt.ConnectionType.QueuedConnection, Q_ARG(QUrl, QUrl.fromLocalFile(path)))
        self.message.setText("定位后设置入点、出点；时间单位为秒。")

    def toggle(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def shutdown(self):
        self.closed = True
        self.video.image = None
        self.video.clear()
        # Execute native teardown after returning to Qt's event loop, rather than
        # joining decoder threads from a Python callback that can hold the GIL.
        QMetaObject.invokeMethod(self.player, "stop", Qt.ConnectionType.QueuedConnection)
        QMetaObject.invokeMethod(self.player, "setSource", Qt.ConnectionType.QueuedConnection, Q_ARG(QUrl, QUrl()))


class TaskForm(QWidget):
    def __init__(self, operation):
        super().__init__()
        self.operation = operation
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.fields = Fields()
        self.video_fields = None
        self.preview = None
        self.soft_audio = None
        self.segments = []
        if operation in {"video", "subtitle", "trim"}:
            formats = ["mp4", "mkv"] if operation != "trim" else ["mp4", "mkv", "flv", "wav", "flac", "m4a", "aac", "mka"]
            self.fields.add("container", "输出容器", combo(formats))
        if operation == "subtitle":
            self.fields.add("subtitle_mode", "处理方式", VideoFields._choices([("内嵌 · 可开关字幕轨", "soft"), ("烧录 · 固定到画面", "burn")]))
            self.layout.addWidget(note("在文件列表中逐项配对字幕。MP4 软字幕会转换为文本轨，ASS 样式无法完整保留。"))
            self.fields.add("font", "SRT 字体", QLineEdit("Microsoft YaHei"))
            size = QSpinBox()
            size.setRange(8, 120)
            size.setValue(24)
            self.fields.add("font_size", "SRT 字号", size)
            self.fields.add("alignment", "SRT 位置", VideoFields._choices([("底部", 2), ("居中", 5), ("顶部", 8)]))
        if operation == "audio":
            self.fields.add("audio_format", "音频格式", combo(["AAC", "WAV", "FLAC", "ALAC"]))
            self.fields.add("container", "输出扩展名", combo(["m4a", "aac"]))
            self.fields.add("audio_bitrate", "AAC 码率", QLineEdit("192k"))
            self.fields.add("sample_rate", "采样率", VideoFields._choices([("保持原始", 0)] + [(str(n), n) for n in [24000, 44100, 48000, 96000, 192000]]))
            self.fields.add("channels", "声道", VideoFields._choices([("保持原始", 0), ("单声道", 1), ("立体声", 2)]))
            self.fields.add("bits", "位深", VideoFields._choices([("自动匹配源位深", 0), ("16 位", 16), ("24 位", 24), ("32 位（WAV）", 32)]))
            level = QSpinBox()
            level.setRange(0, 12)
            level.setValue(5)
            self.fields.add("compression", "FLAC 压缩等级", level)
            self.fields.fields["audio_format"].currentTextChanged.connect(self._audio_format)
            self._audio_format()
        if operation == "mux":
            self.fields.add("container", "输出容器", combo(["mkv", "mp4", "flv", "mka", "m4a", "aac", "flac", "wav", "mp3", "mks"]))
            self.layout.addWidget(note("勾选源文件中的流即可无损抽取或换封装；配对外部音频后可组合封装。每行文件代表一个独立任务组。"))
        if operation == "trim":
            self.preview = Preview()
            self.layout.addWidget(self.preview)
            self.start = QDoubleSpinBox()
            self.end = QDoubleSpinBox()
            for widget in (self.start, self.end):
                widget.setDecimals(3)
                widget.setRange(0, 9999999)
                widget.setSuffix(" 秒")
            for widget, label in ((self.start, "设入点"), (self.end, "设出点")):
                times = QHBoxLayout()
                times.addWidget(widget, 1)
                times.addWidget(button(label, lambda checked=False, target=widget: target.setValue(self.preview.player.position() / 1000)))
                self.layout.addLayout(times)
            self.segment_list = QListWidget()
            self.segment_list.setMaximumHeight(105)
            self.layout.addWidget(self.segment_list)
            row = QHBoxLayout()
            row.addWidget(button("添加片段", self.add_segment))
            row.addWidget(button("删除", self.remove_segment))
            row.addWidget(button("↑", lambda: self.move_segment(-1)))
            row.addWidget(button("↓", lambda: self.move_segment(1)))
            self.layout.addLayout(row)
            self.fields.add("trim_mode", "剪切方式", VideoFields._choices([("无损关键帧剪切", "copy"), ("精确剪切 · 重新编码", "encode")]))
            self.fields.add("merge", "输出方式", QCheckBox("按列表顺序合并片段"))
            self.layout.addWidget(note("无损剪切可能偏离设定切点；精确剪切会重新编码。合并限同一源文件，批量逐文件检查区间。"))
        self.layout.addWidget(self.fields)
        if operation == "subtitle":
            self.soft_audio = Fields()
            self.soft_audio.add("audio_codec", "音频处理", VideoFields._choices([("无损复制", "copy"), ("转为 AAC", "aac"), ("移除音频", "none")]))
            self.soft_audio.add("audio_bitrate", "AAC 码率", QLineEdit("192k"))
            self.layout.addWidget(self.soft_audio)
            self.soft_audio.fields["audio_codec"].currentIndexChanged.connect(self._visibility)
        if operation in {"video", "subtitle", "trim"}:
            self.video_fields = VideoFields()
            if operation == "trim":
                audio_codec = self.video_fields.basic.fields["audio_codec"]
                audio_codec.removeItem(audio_codec.findData("copy"))
            self.layout.addWidget(self.video_fields)
        if operation in {"subtitle", "trim"}:
            key = "subtitle_mode" if operation == "subtitle" else "trim_mode"
            self.fields.fields[key].currentIndexChanged.connect(self._visibility)
        self._visibility()
        self.layout.addStretch()

    def _visibility(self):
        if self.video_fields and self.operation == "subtitle":
            burn = self.fields.values()["subtitle_mode"] == "burn"
            self.video_fields.setVisible(burn)
            self.soft_audio.setVisible(not burn)
            self.soft_audio.form.setRowVisible(self.soft_audio.fields["audio_bitrate"], self.soft_audio.values()["audio_codec"] == "aac")
            for key in ("font", "font_size", "alignment"):
                self.fields.form.setRowVisible(self.fields.fields[key], burn)
        if self.video_fields and self.operation == "trim":
            self.video_fields.setVisible(self.fields.values()["trim_mode"] == "encode")

    def _audio_format(self):
        fmt = self.fields.fields["audio_format"].currentText()
        extension = self.fields.fields["container"]
        extension.clear()
        extension.addItems({"AAC": ["m4a", "aac"], "WAV": ["wav"], "FLAC": ["flac"], "ALAC": ["m4a"]}[fmt])
        for key, visible in [("audio_bitrate", fmt == "AAC"), ("compression", fmt == "FLAC"), ("bits", fmt != "AAC")]:
            self.fields.form.setRowVisible(self.fields.fields[key], visible)

    def add_segment(self):
        if self.end.value() <= self.start.value():
            self.preview.message.setText("出点必须晚于入点。")
            return
        self.segments.append([self.start.value(), self.end.value()])
        self.refresh_segments()

    def refresh_segments(self):
        self.segment_list.clear()
        self.segment_list.addItems([f"{i + 1:02d}   {a:.3f} → {b:.3f} 秒   ·   {b - a:.3f} 秒" for i, (a, b) in enumerate(self.segments)])

    def remove_segment(self):
        row = self.segment_list.currentRow()
        if row >= 0:
            self.segments.pop(row)
            self.refresh_segments()

    def move_segment(self, offset):
        row = self.segment_list.currentRow()
        if 0 <= row + offset < len(self.segments) and row >= 0:
            self.segments.insert(row + offset, self.segments.pop(row))
            self.refresh_segments()
            self.segment_list.setCurrentRow(row + offset)

    def values(self):
        result = self.fields.values()
        if self.video_fields:
            result.update(self.video_fields.values())
        if self.soft_audio and result.get("subtitle_mode") == "soft":
            result.update(self.soft_audio.values())
        if self.operation == "trim":
            result["segments"] = [list(s) for s in self.segments]
        return result

    def restore(self, values):
        self.fields.restore(values)
        if self.video_fields:
            self.video_fields.restore(values)
        if self.soft_audio:
            self.soft_audio.restore(values)
        if self.operation == "trim":
            self.segments = [list(s) for s in values.get("segments", [])]
            self.refresh_segments()
