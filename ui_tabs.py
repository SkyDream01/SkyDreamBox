# -*- coding: utf-8 -*-
# SkyDreamBox/ui_tabs.py

import os
import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLineEdit,
    QLabel, QGroupBox, QComboBox, QTextEdit, QStyle, QGridLayout
)
from PyQt5.QtCore import Qt
from utils import (
    VIDEO_FORMATS, VIDEO_FORMAT_CODECS, AUDIO_CODECS_FOR_VIDEO_FORMAT,
    AUDIO_BITRATES, AUDIO_FORMATS, AUDIO_FORMAT_CODECS, AUDIO_SAMPLE_RATES,
    SUBTITLE_FORMATS, DEFAULT_COMPRESSION_LEVEL
)

def validate_time_format(time_str):
    if not time_str: return True
    return re.fullmatch(r'\d{2}:\d{2}:\d{2}(\.\d+)?', time_str) is not None

def validate_crf(crf_str):
    if not crf_str: return True
    return crf_str.isdigit() and 0 <= int(crf_str) <= 51

def validate_fps(fps_str):
    if not fps_str: return True
    try:
        return float(fps_str) > 0
    except ValueError:
        return False

def validate_resolution(res_str):
    if not res_str: return True
    return re.fullmatch(r'\d+x\d+', res_str) is not None

def validate_bitrate(br_str):
    if not br_str: return True
    return re.fullmatch(r'\d+[kKmM]?', br_str) is not None

def display_error(console, message):
    console.append(f"<font color='red'><b>输入错误:</b> {message}</font>")

class BaseTab(QWidget):
    def __init__(self, process_handler, console, main_window, parent=None):
        super().__init__(parent)
        self.process_handler = process_handler
        self.console = console
        self.main_window = main_window
        self.run_button = None
        self._init_ui()

    def _init_ui(self):
        raise NotImplementedError

    def _get_command(self):
        raise NotImplementedError

    def _validate_inputs(self):
        return True

    def _run_command(self):
        self.main_window.reset_progress_display()
        self.main_window.switch_to_console_tab()
        if not self._validate_inputs():
            return
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
            display_error(self.console, str(e))

    def _create_file_input(self, label_text, button_text="选择文件", callback=None):
        layout = QHBoxLayout()
        line_edit = QLineEdit()
        button = QPushButton(button_text)
        button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        effective_callback = callback or (lambda le: self.main_window.select_file(le))
        button.clicked.connect(lambda: effective_callback(line_edit))
        layout.addWidget(QLabel(label_text))
        layout.addWidget(line_edit)
        layout.addWidget(button)
        return layout, line_edit

class VideoTab(BaseTab):
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        io_group = QGroupBox("输入与输出")
        io_layout = QVBoxLayout(io_group)
        input_layout, self.input_edit = self._create_file_input("视频文件:")
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
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        options_layout.addLayout(format_layout)
        
        video_group = QGroupBox("视频")
        video_layout = QVBoxLayout(video_group)
        
        codec_v_layout = QHBoxLayout()
        codec_v_layout.addWidget(QLabel("视频编码器:"))
        self.video_codec_combo = QComboBox()
        codec_v_layout.addWidget(self.video_codec_combo)
        codec_v_layout.addStretch()
        
        video_grid_layout = QGridLayout()
        video_grid_layout.setSpacing(10)
        self.crf_edit = QLineEdit(); self.crf_edit.setPlaceholderText("x264(18-28), x265(默认28)")
        video_grid_layout.addWidget(QLabel("CRF:"), 0, 0); video_grid_layout.addWidget(self.crf_edit, 0, 1)
        self.fps_edit = QLineEdit(); self.fps_edit.setPlaceholderText("可选, 如 24, 30, 60")
        video_grid_layout.addWidget(QLabel("FPS:"), 0, 2); video_grid_layout.addWidget(self.fps_edit, 0, 3)
        self.resolution_edit = QLineEdit(); self.resolution_edit.setPlaceholderText("可选, 如 1920x1080")
        video_grid_layout.addWidget(QLabel("分辨率:"), 1, 0); video_grid_layout.addWidget(self.resolution_edit, 1, 1)
        self.video_bitrate_edit = QLineEdit(); self.video_bitrate_edit.setPlaceholderText("可选, e.g., 2000k")
        video_grid_layout.addWidget(QLabel("视频比特率:"), 1, 2); video_grid_layout.addWidget(self.video_bitrate_edit, 1, 3)

        video_layout.addLayout(codec_v_layout); video_layout.addLayout(video_grid_layout)
        options_layout.addWidget(video_group)

        audio_group = QGroupBox("音频")
        audio_layout = QVBoxLayout(audio_group)
        audio_options_layout = QHBoxLayout()
        audio_options_layout.addWidget(QLabel("音频编码器:"))
        self.audio_codec_combo = QComboBox()
        self.audio_codec_combo.currentIndexChanged.connect(self._update_audio_bitrate_visibility)
        audio_options_layout.addWidget(self.audio_codec_combo)
        self.audio_bitrate_label = QLabel("音频比特率:")
        self.audio_bitrate_combo = QComboBox(); self.audio_bitrate_combo.addItems(AUDIO_BITRATES)
        self.audio_bitrate_combo.setCurrentText("192k")
        audio_options_layout.addWidget(self.audio_bitrate_label)
        audio_options_layout.addWidget(self.audio_bitrate_combo)
        audio_options_layout.addStretch()
        audio_layout.addLayout(audio_options_layout)
        options_layout.addWidget(audio_group)

        subtitle_layout, self.subtitle_edit = self._create_file_input("字幕文件:", "选择字幕", self.select_subtitle_file)
        options_layout.addLayout(subtitle_layout)
        main_layout.addWidget(options_group)
        
        self.run_button = QPushButton("开始处理视频"); self.run_button.clicked.connect(self._run_command)
        main_layout.addWidget(self.run_button, 0, Qt.AlignCenter); main_layout.addStretch()
        
        # 【修改】连接信号并初始化
        self.format_combo.currentTextChanged.connect(self._on_video_format_changed)
        self._on_video_format_changed(self.format_combo.currentText())

    def _on_video_format_changed(self, v_format):
        # 更新视频编码器
        compatible_v_codecs = VIDEO_FORMAT_CODECS.get(v_format, [])
        self.video_codec_combo.clear()
        self.video_codec_combo.addItems(compatible_v_codecs)
        
        # 更新音频编码器
        compatible_a_codecs = AUDIO_CODECS_FOR_VIDEO_FORMAT.get(v_format, [])
        self.audio_codec_combo.clear()
        self.audio_codec_combo.addItems(compatible_a_codecs)
        
        # 更新输出文件扩展名
        current_path = self.output_edit.text()
        if current_path:
            base_path, _ = os.path.splitext(current_path)
            self.output_edit.setText(f"{base_path}.{v_format}")
        
        self._update_audio_bitrate_visibility()

    def _update_audio_bitrate_visibility(self):
        codec = self.audio_codec_combo.currentText()
        show_bitrate = codec not in ['flac', 'copy', 'alac']
        self.audio_bitrate_label.setVisible(show_bitrate)
        self.audio_bitrate_combo.setVisible(show_bitrate)

    def _validate_inputs(self):
        if not self.input_edit.text() or not os.path.exists(self.input_edit.text()):
            display_error(self.console, "输入视频文件不存在或未指定。"); return False
        if not self.output_edit.text():
            display_error(self.console, "输出文件路径不能为空。"); return False
        if self.subtitle_edit.text() and not os.path.exists(self.subtitle_edit.text()):
            display_error(self.console, "字幕文件不存在。"); return False
        if not validate_crf(self.crf_edit.text()):
            display_error(self.console, "CRF值必须是0-51之间的整数。"); return False
        if not validate_fps(self.fps_edit.text()):
            display_error(self.console, "FPS值必须是一个正数。"); return False
        if not validate_resolution(self.resolution_edit.text()):
            display_error(self.console, "分辨率格式应为 '宽x高' (例如 1920x1080)。"); return False
        if not validate_bitrate(self.video_bitrate_edit.text()):
            display_error(self.console, "视频比特率格式不正确 (例如 2000k 或 2M)。"); return False
        return True

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
        command = ["ffmpeg", "-i", input_file]
        if self.subtitle_edit.text(): command.extend(["-i", self.subtitle_edit.text()])
        command.extend(["-c:v", self.video_codec_combo.currentText()])
        if self.video_codec_combo.currentText() != 'copy':
            if self.crf_edit.text(): command.extend(["-crf", self.crf_edit.text()])
            elif self.video_bitrate_edit.text(): command.extend(["-b:v", self.video_bitrate_edit.text()])
            if self.resolution_edit.text(): command.extend(["-s", self.resolution_edit.text()])
            if self.fps_edit.text(): command.extend(["-r", self.fps_edit.text()])
        command.extend(["-c:a", self.audio_codec_combo.currentText()])
        if self.audio_bitrate_combo.isVisible(): command.extend(["-b:a", self.audio_bitrate_combo.currentText()])
        if self.subtitle_edit.text():
            command.extend(["-map", "0", "-map", "1"])
            codec = "mov_text" if self.format_combo.currentText() == 'mp4' else "copy"
            command.extend(["-c:s", codec])
        command.extend(["-y", output_file])
        return command

class AudioTab(BaseTab):
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        io_group = QGroupBox("输入与输出")
        io_layout = QVBoxLayout(io_group)
        input_layout, self.input_edit = self._create_file_input("音频文件:")
        output_layout, self.output_edit = self._create_file_input("输出路径:", "选择路径", self.select_output_path)
        io_layout.addLayout(input_layout); io_layout.addLayout(output_layout)
        main_layout.addWidget(io_group)
        
        options_group = QGroupBox("音频操作")
        options_layout = QGridLayout(options_group)
        options_layout.setSpacing(10)

        options_layout.addWidget(QLabel("输出格式:"), 0, 0)
        self.format_combo = QComboBox(); self.format_combo.addItems(AUDIO_FORMATS)
        options_layout.addWidget(self.format_combo, 0, 1)

        options_layout.addWidget(QLabel("音频编码器 (位深):"), 0, 2)
        self.codec_combo = QComboBox()
        options_layout.addWidget(self.codec_combo, 0, 3)

        options_layout.addWidget(QLabel("采样率 (Hz):"), 1, 0)
        self.sample_rate_combo = QComboBox(); self.sample_rate_combo.addItems(AUDIO_SAMPLE_RATES)
        options_layout.addWidget(self.sample_rate_combo, 1, 1)
        
        self.bitrate_label = QLabel("音频比特率:"); self.bitrate_edit = QLineEdit("192k")
        self.compression_label = QLabel("压缩等级:")
        self.compression_combo = QComboBox(); self.compression_combo.addItems(map(str, range(13)))
        self.compression_combo.setCurrentText(DEFAULT_COMPRESSION_LEVEL)

        options_layout.addWidget(self.bitrate_label, 1, 2); options_layout.addWidget(self.bitrate_edit, 1, 3)
        options_layout.addWidget(self.compression_label, 1, 2); options_layout.addWidget(self.compression_combo, 1, 3)
        
        main_layout.addWidget(options_group)
        
        self.run_button = QPushButton("开始处理音频"); self.run_button.clicked.connect(self._run_command)
        main_layout.addWidget(self.run_button, 0, Qt.AlignCenter); main_layout.addStretch()
        
        # 【修改】连接信号并初始化
        self.format_combo.currentTextChanged.connect(self._on_audio_format_changed)
        self.codec_combo.currentIndexChanged.connect(self._update_dynamic_options)
        self._on_audio_format_changed(self.format_combo.currentText())

    def _on_audio_format_changed(self, a_format):
        # 更新音频编码器
        compatible_codecs = AUDIO_FORMAT_CODECS.get(a_format, [])
        self.codec_combo.clear()
        self.codec_combo.addItems(compatible_codecs)
        
        # 更新输出文件扩展名
        current_path = self.output_edit.text()
        if current_path:
            base_path, _ = os.path.splitext(current_path)
            self.output_edit.setText(f"{base_path}.{a_format}")
        
        self._update_dynamic_options()

    def _update_dynamic_options(self):
        codec_text = self.codec_combo.currentText()
        if not codec_text: return
        codec = codec_text.split(" ")[0]
        
        is_lossless = codec in ['flac', 'alac']
        is_pcm = 'pcm' in codec
        is_copy = codec == 'copy'

        self.bitrate_label.setVisible(not is_lossless and not is_pcm and not is_copy)
        self.bitrate_edit.setVisible(not is_lossless and not is_pcm and not is_copy)
        self.compression_label.setVisible(is_lossless)
        self.compression_combo.setVisible(is_lossless)

    def _validate_inputs(self):
        if not self.input_edit.text() or not os.path.exists(self.input_edit.text()):
            display_error(self.console, "输入音频文件不存在或未指定。"); return False
        if not self.output_edit.text():
            display_error(self.console, "输出文件路径不能为空。"); return False
        if self.bitrate_edit.isVisible() and not validate_bitrate(self.bitrate_edit.text()):
            display_error(self.console, "音频比特率格式不正确 (例如 192k)。"); return False
        return True

    def select_output_path(self, output_edit):
        filter_str = f"{self.format_combo.currentText().upper()} (*.{self.format_combo.currentText()});;All Files (*)"
        default_path = self.output_edit.text() or os.path.dirname(self.input_edit.text())
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出路径", default_path, filter_str)
        if file_name: output_edit.setText(file_name)

    def _get_command(self):
        input_file, output_file = self.input_edit.text(), self.output_edit.text()
        command = ["ffmpeg", "-i", input_file, "-vn"]
        if self.sample_rate_combo.currentText() != "(默认)":
            command.extend(["-ar", self.sample_rate_combo.currentText()])
        
        codec_text = self.codec_combo.currentText()
        codec = codec_text.split(" ")[0]
        command.extend(["-c:a", codec])
        
        if self.compression_combo.isVisible():
            command.extend(["-compression_level", self.compression_combo.currentText()])
        elif self.bitrate_edit.isVisible():
            command.extend(["-b:a", self.bitrate_edit.text()])
            
        command.extend(["-y", output_file])
        return command

class MuxingTab(BaseTab):
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        mux_group = QGroupBox("封装 (合并音视频)")
        mux_layout = QVBoxLayout(mux_group)
        video_input_layout, self.video_input_edit = self._create_file_input("视频文件:", "选择视频")
        audio_input_layout, self.audio_input_edit = self._create_file_input("音频文件:", "选择音频")
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
        
    def _validate_inputs(self):
        video_file, audio_file, subtitle_file = self.video_input_edit.text(), self.audio_input_edit.text(), self.subtitle_input_edit.text()
        if not video_file and not audio_file:
            display_error(self.console, "至少需要一个视频或音频输入。"); return False
        if not self.output_edit.text():
            display_error(self.console, "输出文件路径不能为空。"); return False
        if video_file and not os.path.exists(video_file):
            display_error(self.console, "输入视频文件不存在。"); return False
        if audio_file and not os.path.exists(audio_file):
            display_error(self.console, "输入音频文件不存在。"); return False
        if subtitle_file and not os.path.exists(subtitle_file):
            display_error(self.console, "字幕文件不存在。"); return False
        return True

    def select_subtitle_file(self, target_edit):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择字幕文件", "", SUBTITLE_FORMATS)
        if file_name: target_edit.setText(file_name)

    def select_output_path(self, target_edit):
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出文件", os.path.dirname(self.video_input_edit.text()), "Media Files (*.mp4 *.mkv)")
        if file_name: target_edit.setText(file_name)

    def _get_command(self):
        command = ["ffmpeg"]
        map_commands = []
        input_index = 0
        if self.video_input_edit.text():
            command.extend(["-i", self.video_input_edit.text()]); map_commands.extend(["-map", f"{input_index}:v?"]); input_index += 1
        if self.audio_input_edit.text():
            command.extend(["-i", self.audio_input_edit.text()]); map_commands.extend(["-map", f"{input_index}:a?"]); input_index += 1
        if self.subtitle_input_edit.text():
            command.extend(["-i", self.subtitle_input_edit.text()]); map_commands.extend(["-map", f"{input_index}:s?"]); input_index += 1
        command.extend(map_commands)
        command.extend(["-c", "copy", "-y", self.output_edit.text()])
        return command

class DemuxingTab(BaseTab):
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        demux_group = QGroupBox("抽取音/视频")
        demux_layout = QVBoxLayout(demux_group)
        input_layout, self.input_edit = self._create_file_input("输入文件:")
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
        
    def _validate_inputs(self):
        if not self.input_edit.text() or not os.path.exists(self.input_edit.text()):
            display_error(self.console, "输入文件不存在或未指定。"); return False
        return True

    def _run_demux_command(self, stream_type):
        self.current_stream_type = stream_type
        self._run_command()

    def _get_command(self):
        input_file = self.input_edit.text()
        base_path, ext = os.path.splitext(input_file)
        command = ["ffmpeg", "-i", input_file]
        if self.current_stream_type == 'video':
            output_file = f"{base_path}_video{ext}"
            command.extend(["-map", "0:v", "-c:v", "copy", "-an"])
        elif self.current_stream_type == 'audio':
            acodec = 'aac' # Default fallback
            audio_ext_map = {'aac': '.m4a', 'mp3': '.mp3', 'flac': '.flac', 'opus': '.opus', 'vorbis': '.ogg'}
            audio_ext = audio_ext_map.get(acodec, f".{acodec}")
            output_file = f"{base_path}_audio{audio_ext}"
            command.extend(["-map", "0:a", "-c:a", "copy", "-vn"])
        else:
            raise ValueError("未知的流类型。")
        command.extend(["-y", output_file])
        self.console.append(f"<font color='cyan'>输出文件将保存为: {output_file}</font>")
        return command

class CommonOperationsTab(BaseTab):
    def _init_ui(self):
        main_layout = QVBoxLayout(self); main_layout.setSpacing(15)
        trim_group = QGroupBox("视频截取")
        trim_layout = QVBoxLayout(trim_group)
        input_layout, self.trim_input_edit = self._create_file_input("输入文件:")
        output_layout, self.trim_output_edit = self._create_file_input("输出文件:", "选择路径", self.select_trim_output_path)
        time_layout = QHBoxLayout()
        self.start_time_edit = QLineEdit("00:00:00")
        self.end_time_edit = QLineEdit(); self.end_time_edit.setPlaceholderText("HH:MM:SS 或 结尾")
        time_layout.addWidget(QLabel("开始时间:")); time_layout.addWidget(self.start_time_edit)
        time_layout.addWidget(QLabel("结束时间:")); time_layout.addWidget(self.end_time_edit)
        self.trim_button = QPushButton("开始截取")
        trim_layout.addLayout(input_layout); trim_layout.addLayout(output_layout)
        trim_layout.addLayout(time_layout); trim_layout.addWidget(self.trim_button, 0, Qt.AlignCenter)
        main_layout.addWidget(trim_group)
        img_audio_group = QGroupBox("图声合成")
        img_audio_layout = QVBoxLayout(img_audio_group)
        img_layout, self.img_input_edit = self._create_file_input("图片文件:", "选择图片", self.select_image_file)
        audio_layout, self.audio_input_edit = self._create_file_input("音频文件:", "选择音频")
        output_layout, self.img_audio_output_edit = self._create_file_input("输出视频:", "选择路径", self.select_img_audio_output_path)
        self.img_audio_button = QPushButton("开始合成")
        img_audio_layout.addLayout(img_layout); img_audio_layout.addLayout(audio_layout)
        img_audio_layout.addLayout(output_layout); img_audio_layout.addWidget(self.img_audio_button, 0, Qt.AlignCenter)
        main_layout.addWidget(img_audio_group); main_layout.addStretch()
        self.trim_button.clicked.connect(lambda: self._run_specific_command('trim'))
        self.img_audio_button.clicked.connect(lambda: self._run_specific_command('img_audio'))
        self.run_button = self.trim_button 

    def _validate_inputs(self):
        command_type = self.current_command
        if command_type == 'trim':
            if not self.trim_input_edit.text() or not os.path.exists(self.trim_input_edit.text()):
                display_error(self.console, "截取功能的输入文件不存在或未指定。"); return False
            if not self.trim_output_edit.text():
                display_error(self.console, "截取功能的输出文件路径不能为空。"); return False
            if not validate_time_format(self.start_time_edit.text()):
                display_error(self.console, "开始时间格式不正确 (应为 HH:MM:SS)。"); return False
            if not validate_time_format(self.end_time_edit.text()):
                display_error(self.console, "结束时间格式不正确 (应为 HH:MM:SS)。"); return False
        elif command_type == 'img_audio':
            if not self.img_input_edit.text() or not os.path.exists(self.img_input_edit.text()):
                display_error(self.console, "图声合成的图片文件不存在或未指定。"); return False
            if not self.audio_input_edit.text() or not os.path.exists(self.audio_input_edit.text()):
                display_error(self.console, "图声合成的音频文件不存在或未指定。"); return False
            if not self.img_audio_output_edit.text():
                display_error(self.console, "图声合成的输出文件路径不能为空。"); return False
        return True

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
            command = ["ffmpeg", "-i", self.trim_input_edit.text()]
            if self.start_time_edit.text() and self.start_time_edit.text() != "00:00:00": 
                command.extend(["-ss", self.start_time_edit.text()])
            if self.end_time_edit.text(): 
                command.extend(["-to", self.end_time_edit.text()])
            command.extend(["-c", "copy", "-y", self.trim_output_edit.text()])
            return command
        elif command_type == 'img_audio':
            return ["ffmpeg", "-loop", "1", "-i", self.img_input_edit.text(), "-i", self.audio_input_edit.text(),
                    "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-y", self.img_audio_output_edit.text()]
        raise ValueError("未知的常用操作。")

class ProfessionalTab(BaseTab):
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addWidget(QLabel("在此处输入完整的FFmpeg命令:"))
        self.command_input = QTextEdit()
        self.command_input.setPlaceholderText("e.g., ffmpeg -i input.mp4 -c:v libx264 -crf 22 output.mp4")
        self.command_input.setObjectName("console")
        layout.addWidget(self.command_input)
        self.run_button = QPushButton("执行命令")
        self.run_button.clicked.connect(self._run_command)
        layout.addWidget(self.run_button, 0, Qt.AlignCenter)
        layout.addStretch()

    def _validate_inputs(self):
        command_text = self.command_input.toPlainText().strip()
        if not command_text:
            display_error(self.console, "命令不能为空。"); return False
        if not command_text.lower().startswith('ffmpeg'):
            display_error(self.console, "命令必须以 'ffmpeg' 开始。"); return False
        return True

    def _get_command(self):
        return self.command_input.toPlainText().strip().split()