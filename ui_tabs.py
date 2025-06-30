# -*- coding: utf-8 -*-
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLineEdit,
    QLabel, QGroupBox, QComboBox, QTextEdit, QStyle
)
from PyQt5.QtCore import Qt
from utils import (
    VIDEO_FORMATS, VIDEO_CODECS, AUDIO_CODECS_VIDEO_TAB, AUDIO_FORMATS,
    AUDIO_CODECS_AUDIO_TAB, SUBTITLE_FORMATS, DEFAULT_COMPRESSION_LEVEL
)

# =============================================================================
# UI Base Class (UI基类)
# =============================================================================
class BaseTab(QWidget):
    def __init__(self, process_handler, console, main_window, parent=None):
        super().__init__(parent)
        self.process_handler = process_handler
        self.console = console
        self.main_window = main_window
        self.run_button = None
        self._init_ui_base()

    def _init_ui_base(self): raise NotImplementedError
    def _get_command(self): raise NotImplementedError

    def _run_command(self):
        try:
            command = self._get_command()
            if command:
                is_started, message = self.process_handler.run_ffmpeg(command)
                if not is_started:
                    self.console.append(f"<font color='orange'>{message}</font>")
                else:
                    self.console.clear()
                    self.console.append(f"<b>{message}</b>\n<hr>")
                    self.main_window.set_buttons_enabled(False)
        except (ValueError, FileNotFoundError) as e:
            self.console.append(f"<font color='red'>错误: {e}</font>")

    def _create_file_input(self, label_text, button_text, select_callback):
        layout = QHBoxLayout()
        line_edit = QLineEdit()
        button = QPushButton(button_text)
        button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        button.clicked.connect(lambda: select_callback(line_edit))
        layout.addWidget(QLabel(label_text))
        layout.addWidget(line_edit)
        layout.addWidget(button)
        return layout, line_edit

# =============================================================================
# UI Tabs Module
# =============================================================================
class VideoTab(BaseTab):
    def _init_ui_base(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        io_group = QGroupBox("输入与输出")
        io_layout = QVBoxLayout(io_group)
        input_layout, self.input_edit = self._create_file_input("视频文件:", "选择文件", self.main_window.select_file)
        output_layout, self.output_edit = self._create_file_input("输出路径:", "选择路径", self.select_output_path)
        io_layout.addLayout(input_layout)
        io_layout.addLayout(output_layout)
        main_layout.addWidget(io_group)
        options_group = QGroupBox("操作设置")
        options_layout = QVBoxLayout(options_group)
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(VIDEO_FORMATS)
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo)
        options_layout.addLayout(format_layout)
        video_group = QGroupBox("视频")
        video_layout = QVBoxLayout(video_group)
        codec_v_layout = QHBoxLayout()
        codec_v_layout.addWidget(QLabel("视频编码器:"))
        self.video_codec_combo = QComboBox()
        self.video_codec_combo.addItems(VIDEO_CODECS)
        codec_v_layout.addWidget(self.video_codec_combo)
        crf_layout = QHBoxLayout()
        crf_layout.addWidget(QLabel("CRF:"))
        self.crf_edit = QLineEdit()
        self.crf_edit.setPlaceholderText("x264(18-28,默认23), x265(默认28)")
        crf_layout.addWidget(self.crf_edit)
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("FPS:"))
        self.fps_edit = QLineEdit()
        self.fps_edit.setPlaceholderText("可选, 如 24, 30, 60 (默认不变)")
        fps_layout.addWidget(self.fps_edit)
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("分辨率:"))
        self.resolution_edit = QLineEdit()
        self.resolution_edit.setPlaceholderText("可选, 如 1920x1080")
        resolution_layout.addWidget(self.resolution_edit)
        bitrate_v_layout = QHBoxLayout()
        bitrate_v_layout.addWidget(QLabel("视频比特率:"))
        self.video_bitrate_edit = QLineEdit()
        self.video_bitrate_edit.setPlaceholderText("可选, e.g., 2000k (CRF优先)")
        bitrate_v_layout.addWidget(self.video_bitrate_edit)
        video_layout.addLayout(codec_v_layout)
        video_layout.addLayout(crf_layout)
        video_layout.addLayout(fps_layout)
        video_layout.addLayout(resolution_layout)
        video_layout.addLayout(bitrate_v_layout)
        options_layout.addWidget(video_group)
        audio_group = QGroupBox("音频")
        audio_layout = QVBoxLayout(audio_group)
        codec_a_layout = QHBoxLayout()
        codec_a_layout.addWidget(QLabel("音频编码器:"))
        self.audio_codec_combo = QComboBox()
        self.audio_codec_combo.addItems(AUDIO_CODECS_VIDEO_TAB)
        codec_a_layout.addWidget(self.audio_codec_combo)
        bitrate_a_layout = QHBoxLayout()
        bitrate_a_layout.addWidget(QLabel("音频比特率:"))
        self.audio_bitrate_edit = QLineEdit("192k")
        self.audio_bitrate_edit.setPlaceholderText("e.g., 192k")
        bitrate_a_layout.addWidget(self.audio_bitrate_edit)
        audio_layout.addLayout(codec_a_layout)
        audio_layout.addLayout(bitrate_a_layout)
        options_layout.addWidget(audio_group)
        subtitle_layout, self.subtitle_edit = self._create_file_input("字幕文件:", "选择字幕", self.select_subtitle_file)
        options_layout.addLayout(subtitle_layout)
        main_layout.addWidget(options_group)
        self.run_button = QPushButton("开始处理视频")
        self.run_button.clicked.connect(self._run_command)
        main_layout.addWidget(self.run_button, 0, Qt.AlignCenter)
        main_layout.addStretch()

    def _on_format_changed(self, new_format):
        current_path = self.output_edit.text()
        if not current_path: return
        base_path, _ = os.path.splitext(current_path)
        self.output_edit.setText(f"{base_path}.{new_format}")

    def select_output_path(self, output_edit):
        filter_str = f"{self.format_combo.currentText().upper()} (*.{self.format_combo.currentText()});;All Files (*)"
        default_path = self.output_edit.text() or os.path.dirname(self.input_edit.text())
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出路径", default_path, filter_str)
        if file_name: output_edit.setText(file_name)

    def select_subtitle_file(self, target_edit):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择字幕文件", "", SUBTITLE_FORMATS)
        if file_name: target_edit.setText(file_name)

    def _get_command(self):
        input_file, output_file = self.input_edit.text(), self.output_edit.text()
        if not all([input_file, output_file]): raise ValueError("输入和输出文件路径不能为空。")
        command = ["ffmpeg", "-i", input_file]
        if self.subtitle_edit.text(): command.extend(["-i", self.subtitle_edit.text()])
        video_codec = self.video_codec_combo.currentText()
        command.extend(["-c:v", video_codec])
        if video_codec != 'copy':
            crf_value = self.crf_edit.text()
            if crf_value:
                command.extend(["-crf", crf_value])
            elif self.video_bitrate_edit.text():
                command.extend(["-b:v", self.video_bitrate_edit.text()])
            if self.resolution_edit.text():
                command.extend(["-s", self.resolution_edit.text()])
            if self.fps_edit.text():
                command.extend(["-r", self.fps_edit.text()])
        audio_codec = self.audio_codec_combo.currentText()
        command.extend(["-c:a", audio_codec])
        if audio_codec != 'copy' and self.audio_bitrate_edit.text():
            command.extend(["-b:a", self.audio_bitrate_edit.text()])
        if self.subtitle_edit.text():
            command.extend(["-map", "0", "-map", "1"])
            codec = "mov_text" if self.format_combo.currentText() == 'mp4' else "copy"
            command.extend(["-c:s", codec])
        command.extend(["-y", output_file])
        return command

class AudioTab(BaseTab):
    def _init_ui_base(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        io_group = QGroupBox("输入与输出")
        io_layout = QVBoxLayout(io_group)
        input_layout, self.input_edit = self._create_file_input("音频文件:", "选择文件", self.main_window.select_file)
        output_layout, self.output_edit = self._create_file_input("输出路径:", "选择路径", self.select_output_path)
        io_layout.addLayout(input_layout)
        io_layout.addLayout(output_layout)
        main_layout.addWidget(io_group)
        options_group = QGroupBox("音频操作")
        options_layout = QVBoxLayout(options_group)
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(AUDIO_FORMATS)
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo)
        codec_layout = QHBoxLayout()
        codec_layout.addWidget(QLabel("音频编码器:"))
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(AUDIO_CODECS_AUDIO_TAB)
        self.codec_combo.currentIndexChanged.connect(self._update_dynamic_options)
        codec_layout.addWidget(self.codec_combo)
        self.dynamic_layout = QHBoxLayout()
        self.bitrate_label = QLabel("音频比特率:")
        self.bitrate_edit = QLineEdit("192k")
        self.compression_label = QLabel("压缩等级:")
        self.compression_combo = QComboBox()
        self.compression_combo.addItems(map(str, range(9)))
        self.compression_combo.setCurrentText(DEFAULT_COMPRESSION_LEVEL)
        self.dynamic_layout.addWidget(self.bitrate_label)
        self.dynamic_layout.addWidget(self.bitrate_edit)
        self.dynamic_layout.addWidget(self.compression_label)
        self.dynamic_layout.addWidget(self.compression_combo)
        options_layout.addLayout(format_layout)
        options_layout.addLayout(codec_layout)
        options_layout.addLayout(self.dynamic_layout)
        main_layout.addWidget(options_group)
        self.run_button = QPushButton("开始处理音频")
        self.run_button.clicked.connect(self._run_command)
        main_layout.addWidget(self.run_button, 0, Qt.AlignCenter)
        main_layout.addStretch()
        self._update_dynamic_options()

    def _on_format_changed(self, new_format):
        current_path = self.output_edit.text()
        if not current_path: return
        base_path, _ = os.path.splitext(current_path)
        self.output_edit.setText(f"{base_path}.{new_format}")

    def _update_dynamic_options(self):
        codec = self.codec_combo.currentText()
        is_lossless = codec in ['flac', 'alac']
        is_fixed = codec in ['copy', 'pcm_s16le']
        self.bitrate_label.setVisible(not is_lossless and not is_fixed)
        self.bitrate_edit.setVisible(not is_lossless and not is_fixed)
        self.compression_label.setVisible(is_lossless)
        self.compression_combo.setVisible(is_lossless)

    def select_output_path(self, output_edit):
        filter_str = f"{self.format_combo.currentText().upper()} (*.{self.format_combo.currentText()});;All Files (*)"
        default_path = self.output_edit.text() or os.path.dirname(self.input_edit.text())
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出路径", default_path, filter_str)
        if file_name: output_edit.setText(file_name)

    def _get_command(self):
        input_file, output_file = self.input_edit.text(), self.output_edit.text()
        if not all([input_file, output_file]): raise ValueError("输入和输出文件路径不能为空。")
        command = ["ffmpeg", "-i", input_file, "-vn"]
        codec = self.codec_combo.currentText()
        command.extend(["-c:a", codec])
        if codec in ['flac', 'alac']: command.extend(["-compression_level", self.compression_combo.currentText()])
        elif codec not in ['copy', 'pcm_s16le'] and self.bitrate_edit.text(): command.extend(["-b:a", self.bitrate_edit.text()])
        command.extend(["-y", output_file])
        return command

class MuxingTab(BaseTab):
    def _init_ui_base(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        mux_group = QGroupBox("封装 (合并音视频)")
        mux_layout = QVBoxLayout(mux_group)
        video_input_layout, self.video_input_edit = self._create_file_input("视频文件:", "选择视频", self.main_window.select_file)
        audio_input_layout, self.audio_input_edit = self._create_file_input("音频文件:", "选择音频", self.main_window.select_file)
        subtitle_input_layout, self.subtitle_input_edit = self._create_file_input("字幕文件:", "选择字幕", self.select_subtitle_file)
        output_layout, self.output_edit = self._create_file_input("输出文件:", "选择路径", self.select_output_path)
        mux_layout.addLayout(video_input_layout)
        mux_layout.addLayout(audio_input_layout)
        mux_layout.addLayout(subtitle_input_layout)
        mux_layout.addLayout(output_layout)
        main_layout.addWidget(mux_group)
        self.run_button = QPushButton("开始封装")
        self.run_button.clicked.connect(self._run_command)
        main_layout.addWidget(self.run_button, 0, Qt.AlignCenter)
        main_layout.addStretch()

    def select_subtitle_file(self, target_edit):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择字幕文件", "", SUBTITLE_FORMATS)
        if file_name: target_edit.setText(file_name)

    def select_output_path(self, target_edit):
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出文件", os.path.dirname(self.video_input_edit.text()), "Media Files (*.mp4 *.mkv)")
        if file_name: target_edit.setText(file_name)

    def _get_command(self):
        video_file = self.video_input_edit.text()
        audio_file = self.audio_input_edit.text()
        subtitle_file = self.subtitle_input_edit.text()
        output_file = self.output_edit.text()
        if not video_file and not audio_file: raise ValueError("至少需要一个视频或音频输入。")
        if not output_file: raise ValueError("输出文件路径不能为空。")
        command = ["ffmpeg"]
        inputs = []
        if video_file:
            command.extend(["-i", video_file])
            inputs.append('video')
        if audio_file:
            command.extend(["-i", audio_file])
            inputs.append('audio')
        if subtitle_file:
            command.extend(["-i", subtitle_file])
            inputs.append('subtitle')

        command.extend(["-c", "copy"])

        for i, input_type in enumerate(inputs):
            if input_type == 'video':
                command.extend(["-map", f"{i}:v?"])
            elif input_type == 'audio':
                command.extend(["-map", f"{i}:a?"])
            elif input_type == 'subtitle':
                command.extend(["-map", f"{i}:s?"])

        command.extend(["-y", output_file])
        return command

class DemuxingTab(BaseTab):
    def _init_ui_base(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        demux_group = QGroupBox("抽取音/视频")
        demux_layout = QVBoxLayout(demux_group)
        input_layout, self.input_edit = self._create_file_input("输入文件:", "选择文件", self.main_window.select_file)
        demux_layout.addLayout(input_layout)
        buttons_layout = QHBoxLayout()
        self.extract_video_button = QPushButton("抽取视频流")
        self.extract_audio_button = QPushButton("抽取音频流")
        buttons_layout.addWidget(self.extract_video_button)
        buttons_layout.addWidget(self.extract_audio_button)
        demux_layout.addLayout(buttons_layout)
        main_layout.addWidget(demux_group)
        main_layout.addStretch()
        self.extract_video_button.clicked.connect(lambda: self._run_demux_command('video'))
        self.extract_audio_button.clicked.connect(lambda: self._run_demux_command('audio'))
        self.run_button = self.extract_video_button

    def _run_demux_command(self, stream_type):
        self.current_stream_type = stream_type
        self._run_command()

    def _get_command(self):
        input_file = self.input_edit.text()
        if not input_file: raise ValueError("请选择输入文件。")
        base_path, ext = os.path.splitext(input_file)
        command = ["ffmpeg", "-i", input_file]
        if self.current_stream_type == 'video':
            output_file = f"{base_path}_video{ext}"
            command.extend(["-map", "0:v", "-c:v", "copy", "-an"])
        elif self.current_stream_type == 'audio':
            output_file = f"{base_path}_audio.aac"
            command.extend(["-map", "0:a", "-c:a", "copy", "-vn"])
        else:
            raise ValueError("未知的流类型。")
        command.extend(["-y", output_file])
        self.console.append(f"<font color='cyan'>输出文件将保存为: {output_file}</font>")
        return command

class CommonOperationsTab(BaseTab):
    def _init_ui_base(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        trim_group = QGroupBox("视频截取")
        trim_layout = QVBoxLayout(trim_group)
        input_layout, self.trim_input_edit = self._create_file_input("输入文件:", "选择文件", self.main_window.select_file)
        output_layout, self.trim_output_edit = self._create_file_input("输出文件:", "选择路径", self.select_trim_output_path)
        time_layout = QHBoxLayout()
        self.start_time_edit = QLineEdit("00:00:00")
        self.end_time_edit = QLineEdit()
        self.end_time_edit.setPlaceholderText("HH:MM:SS 或 结尾")
        time_layout.addWidget(QLabel("开始时间:"))
        time_layout.addWidget(self.start_time_edit)
        time_layout.addWidget(QLabel("结束时间:"))
        time_layout.addWidget(self.end_time_edit)
        self.trim_button = QPushButton("开始截取")
        trim_layout.addLayout(input_layout)
        trim_layout.addLayout(output_layout)
        trim_layout.addLayout(time_layout)
        trim_layout.addWidget(self.trim_button, 0, Qt.AlignCenter)
        main_layout.addWidget(trim_group)
        img_audio_group = QGroupBox("图声合成")
        img_audio_layout = QVBoxLayout(img_audio_group)
        img_layout, self.img_input_edit = self._create_file_input("图片文件:", "选择图片", self.select_image_file)
        audio_layout, self.audio_input_edit = self._create_file_input("音频文件:", "选择音频", self.main_window.select_file)
        output_layout, self.img_audio_output_edit = self._create_file_input("输出视频:", "选择路径", self.select_img_audio_output_path)
        self.img_audio_button = QPushButton("开始合成")
        img_audio_layout.addLayout(img_layout)
        img_audio_layout.addLayout(audio_layout)
        img_audio_layout.addLayout(output_layout)
        img_audio_layout.addWidget(self.img_audio_button, 0, Qt.AlignCenter)
        main_layout.addWidget(img_audio_group)
        main_layout.addStretch()
        self.trim_button.clicked.connect(lambda: self._run_specific_command('trim'))
        self.img_audio_button.clicked.connect(lambda: self._run_specific_command('img_audio'))
        self.run_button = self.trim_button

    def _run_specific_command(self, command_type):
        self.current_command = command_type
        self._run_command()

    def select_trim_output_path(self, target_edit):
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出文件", os.path.dirname(self.trim_input_edit.text()))
        if file_name: target_edit.setText(file_name)

    def select_image_file(self, target_edit):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择图片文件", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_name: target_edit.setText(file_name)

    def select_img_audio_output_path(self, target_edit):
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出视频", os.path.dirname(self.img_input_edit.text()), "Video Files (*.mp4)")
        if file_name: target_edit.setText(file_name)

    def _get_command(self):
        command_type = self.current_command
        if command_type == 'trim':
            input_file = self.trim_input_edit.text()
            output_file = self.trim_output_edit.text()
            if not all([input_file, output_file]): raise ValueError("截取功能的输入和输出均不能为空。")
            command = ["ffmpeg", "-i", input_file]
            if self.start_time_edit.text() != "00:00:00": command.extend(["-ss", self.start_time_edit.text()])
            if self.end_time_edit.text(): command.extend(["-to", self.end_time_edit.text()])
            command.extend(["-c", "copy", "-y", output_file])
            return command
        elif command_type == 'img_audio':
            img_file = self.img_input_edit.text()
            audio_file = self.audio_input_edit.text()
            output_file = self.img_audio_output_edit.text()
            if not all([img_file, audio_file, output_file]): raise ValueError("图声合成的图片、音频和输出均不能为空。")
            command = ["ffmpeg", "-loop", "1", "-i", img_file, "-i", audio_file,
                       "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
                       "-shortest", "-y", output_file]
            return command
        raise ValueError("未知的常用操作。")

class ProfessionalTab(BaseTab):
    def _init_ui_base(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addWidget(QLabel("在此处输入完整的FFmpeg命令:"))
        self.command_input = QTextEdit()
        self.command_input.setPlaceholderText("e.g., ffmpeg -i input.mp4 -c:v libx264 -crf 22 output.mp4")
        layout.addWidget(self.command_input)
        self.run_button = QPushButton("执行命令")
        self.run_button.clicked.connect(self._run_command)
        layout.addWidget(self.run_button, 0, Qt.AlignCenter)
        layout.addStretch()