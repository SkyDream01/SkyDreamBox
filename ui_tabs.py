# -*- coding: utf-8 -*-
# SkyDreamBox/ui_tabs.py

import os
import re
from PyQt5.QtWidgets import QWidget, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


# 引入 UI 定义
from ui.video_tab_ui import Ui_VideoTab
from ui.audio_tab_ui import Ui_AudioTab
from ui.muxing_tab_ui import Ui_MuxingTab
from ui.demuxing_tab_ui import Ui_DemuxingTab
from ui.common_ops_tab_ui import Ui_CommonOpsTab
from ui.pro_tab_ui import Ui_ProfessionalTab
from ui.about_tab_ui import Ui_AboutTab # 导入新的 AboutTab UI

from utils import (
    VIDEO_FORMATS, VIDEO_FORMAT_CODECS, AUDIO_CODECS_FOR_VIDEO_FORMAT,
    AUDIO_BITRATES, AUDIO_FORMATS, AUDIO_FORMAT_CODECS, AUDIO_SAMPLE_RATES,
    WAV_BIT_DEPTH_CODECS, AUDIO_SAMPLE_FORMATS,
    SUBTITLE_FORMATS, DEFAULT_COMPRESSION_LEVEL
)
# constants 和 resource_path 不再在此文件中直接使用，可以移除

# --- Helper Functions ---

def validate_time_format(time_str):
    if not time_str: return True
    return re.fullmatch(r'\d{1,2}:\d{2}:\d{2}(\.\d+)?', time_str) is not None

def validate_crf(crf_str):
    if not crf_str: return True
    return crf_str.isdigit() and 0 <= int(crf_str) <= 51

def validate_cq(cq_str):
    if not cq_str: return True
    return cq_str.isdigit() and 0 <= int(cq_str) <= 51

def validate_fps(fps_str):
    if not fps_str: return True
    try:
        return float(fps_str) > 0
    except ValueError:
        return False

def validate_resolution(res_str):
    if not res_str: return True
    return re.fullmatch(r'\d+[xX]\d+', res_str) is not None

def validate_bitrate(br_str):
    if not br_str: return True
    return re.fullmatch(r'\d+[kKmM]?', br_str) is not None

def display_error(console, message):
    console.append(f"<font color='#e74c3c'><b>输入错误:</b> {message}</font>")

# --- Base Tab Class ---

class BaseTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.process_handler = main_window.process_handler
        self.console = main_window.console

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
                    self.console.append(f"<font color='#e67e22'>{message}</font>")
                else:
                    self.console.clear()
                    self.console.append(f"<b>{message}</b>\n<hr>")
                    self.main_window.set_buttons_enabled(False)
        except Exception as e:
            display_error(self.console, f"构建命令时发生意外错误: {e}")

    def _validate_inputs(self):
        return True

    def _get_command(self):
        raise NotImplementedError

    def set_buttons_enabled(self, enabled):
        if hasattr(self, 'run_button'):
            self.run_button.setEnabled(enabled)

# --- Tab Implementations ---

class VideoTab(BaseTab, Ui_VideoTab):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setupUi(self)
        self._connect_signals()
        self._initialize_ui_state()

    def _connect_signals(self):
        self.select_input_button.clicked.connect(lambda: self.main_window.select_file(self.input_edit))
        self.select_output_button.clicked.connect(self.select_output_path)
        self.select_subtitle_button.clicked.connect(self.select_subtitle_file)
        self.run_button.clicked.connect(self._run_command)
        self.format_combo.currentTextChanged.connect(self._on_video_format_changed)
        self.audio_codec_combo.currentIndexChanged.connect(self._update_audio_bitrate_visibility)
        self.video_codec_combo.currentTextChanged.connect(self._update_video_options_visibility)

    def _initialize_ui_state(self):
        self.format_combo.addItems(VIDEO_FORMATS)
        self.audio_bitrate_combo.addItems(AUDIO_BITRATES)
        self.audio_bitrate_combo.setCurrentText("192k")
        self._on_video_format_changed(self.format_combo.currentText())

    def _on_video_format_changed(self, v_format):
        self.video_codec_combo.clear()
        self.video_codec_combo.addItems(VIDEO_FORMAT_CODECS.get(v_format, []))
        self.audio_codec_combo.clear()
        self.audio_codec_combo.addItems(AUDIO_CODECS_FOR_VIDEO_FORMAT.get(v_format, []))
        self.auto_set_output_path(self.input_edit.text())
        self._update_audio_bitrate_visibility()

    def _update_audio_bitrate_visibility(self):
        codec = self.audio_codec_combo.currentText()
        is_visible = codec not in ['flac', 'copy', 'alac']
        self.audio_bitrate_label.setVisible(is_visible)
        self.audio_bitrate_combo.setVisible(is_visible)

    def _update_video_options_visibility(self):
        codec = self.video_codec_combo.currentText()
        is_crf_visible = "libx" in codec
        is_cq_visible = "nvenc" in codec

        self.crf_label.setVisible(is_crf_visible)
        self.crf_edit.setVisible(is_crf_visible)

        self.cq_label.setVisible(is_cq_visible)
        self.cq_edit.setVisible(is_cq_visible)

        is_bitrate_visible = codec != 'copy'
        self.video_bitrate_label.setVisible(is_bitrate_visible)
        self.video_bitrate_edit.setVisible(is_bitrate_visible)

    def _validate_inputs(self):
        if not self.input_edit.text() or not os.path.exists(self.input_edit.text()):
            display_error(self.console, "输入视频文件不存在或未指定。"); return False
        if not self.output_edit.text():
            display_error(self.console, "输出文件路径不能为空。"); return False
        if self.crf_edit.isVisible() and not validate_crf(self.crf_edit.text()):
            display_error(self.console, f"无效的CRF值: {self.crf_edit.text()} (应为0-51的整数)"); return False
        if self.cq_edit.isVisible() and not validate_cq(self.cq_edit.text()):
            display_error(self.console, f"无效的CQ值: {self.cq_edit.text()} (应为0-51的整数)"); return False
        if not validate_fps(self.fps_edit.text()):
            display_error(self.console, f"无效的FPS值: {self.fps_edit.text()}"); return False
        if not validate_resolution(self.resolution_edit.text()):
            display_error(self.console, f"无效的分辨率格式: {self.resolution_edit.text()} (应为 宽度x高度)"); return False
        if self.video_bitrate_edit.isVisible() and not validate_bitrate(self.video_bitrate_edit.text()):
            display_error(self.console, f"无效的视频比特率: {self.video_bitrate_edit.text()}"); return False
        if self.subtitle_edit.text() and not os.path.exists(self.subtitle_edit.text()):
            display_error(self.console, "指定的字幕文件不存在。"); return False
        return True

    def auto_set_output_path(self, input_path):
        if not input_path: return
        base_path, _ = os.path.splitext(input_path)
        selected_format = self.format_combo.currentText()
        self.output_edit.setText(f"{base_path}_output.{selected_format}")

    def select_output_path(self):
        filter_str = f"{self.format_combo.currentText().upper()} (*.{self.format_combo.currentText()});;All Files (*)"
        default_path = self.output_edit.text() or os.path.dirname(self.input_edit.text())
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出路径", default_path, filter_str)
        if file_name: self.output_edit.setText(file_name)

    def select_subtitle_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择字幕文件", "", SUBTITLE_FORMATS)
        if file_name: self.subtitle_edit.setText(file_name)

    def _get_command(self):
        input_file, output_file = self.input_edit.text(), self.output_edit.text()
        command = ["ffmpeg", "-i", input_file]
        
        subtitle_file = self.subtitle_edit.text()
        if subtitle_file:
            escaped_subtitle_path = subtitle_file.replace(':', '\\\\:')
            command.extend(["-vf", f"subtitles={escaped_subtitle_path}"])

        video_codec = self.video_codec_combo.currentText()
        command.extend(["-c:v", video_codec])
        if video_codec != 'copy':
            if self.crf_edit.isVisible() and self.crf_edit.text():
                command.extend(["-crf", self.crf_edit.text()])
            if self.cq_edit.isVisible() and self.cq_edit.text():
                command.extend(["-cq", self.cq_edit.text()])
            if self.video_bitrate_edit.isVisible() and self.video_bitrate_edit.text():
                command.extend(["-b:v", self.video_bitrate_edit.text()])
            if self.fps_edit.text():
                command.extend(["-r", self.fps_edit.text()])
            if self.resolution_edit.text():
                command.extend(["-s", self.resolution_edit.text()])

        audio_codec = self.audio_codec_combo.currentText()
        command.extend(["-c:a", audio_codec])
        if audio_codec != 'copy' and self.audio_bitrate_combo.isVisible() and self.audio_bitrate_combo.currentText():
            command.extend(["-b:a", self.audio_bitrate_combo.currentText()])
        
        command.extend(["-y", output_file])
        return command

class AudioTab(BaseTab, Ui_AudioTab):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setupUi(self)
        self._connect_signals()
        self._initialize_ui_state()

    def _connect_signals(self):
        self.select_input_button.clicked.connect(lambda: self.main_window.select_file(self.input_edit))
        self.select_output_button.clicked.connect(self.select_output_path)
        self.run_button.clicked.connect(self._run_command)
        self.format_combo.currentTextChanged.connect(self._on_audio_format_changed)
        self.codec_combo.currentTextChanged.connect(self._update_dynamic_options)
        self.bitrate_combo.currentTextChanged.connect(self._update_dynamic_options)

    def _initialize_ui_state(self):
        self.format_combo.addItems(AUDIO_FORMATS)
        self.sample_rate_combo.addItems(AUDIO_SAMPLE_RATES)
        self.bitrate_combo.addItems(AUDIO_BITRATES)
        self.bitrate_combo.setCurrentText("192k")
        self.compression_combo.addItems(map(str, range(13)))
        self.compression_combo.setCurrentText(DEFAULT_COMPRESSION_LEVEL)
        self._on_audio_format_changed(self.format_combo.currentText())

    def _on_audio_format_changed(self, a_format):
        self.codec_combo.clear()
        codecs = AUDIO_FORMAT_CODECS.get(a_format, [])
        self.codec_combo.addItems(codecs)

        self.bit_depth_combo.clear()
        if a_format == 'wav':
            self.bit_depth_combo.addItems(WAV_BIT_DEPTH_CODECS.keys())
        else:
            self.bit_depth_combo.addItems(AUDIO_SAMPLE_FORMATS.keys())
        
        self.auto_set_output_path(self.input_edit.text())
        self._update_dynamic_options()

    def _update_dynamic_options(self):
        a_format = self.format_combo.currentText()
        codec = self.codec_combo.currentText()
        if not codec: return
        
        is_copy = codec == 'copy'
        is_lossy = codec in ['libmp3lame', 'aac', 'opus', 'vorbis']
        is_flac = codec == 'flac'
        is_wav = a_format == 'wav'

        self.sample_rate_combo.setEnabled(not is_copy)
        self.bitrate_combo.setEnabled(not is_copy)
        self.compression_combo.setEnabled(not is_copy)

        self.bitrate_label.setVisible(is_lossy)
        self.bitrate_combo.setVisible(is_lossy)

        self.compression_label.setVisible(is_flac)
        self.compression_combo.setVisible(is_flac)
        
        # MODIFIED: For lossy codecs, bit depth is not applicable. Also hide for 'copy'
        is_bit_depth_visible = not is_copy and not is_lossy
        self.bit_depth_label.setVisible(is_bit_depth_visible)
        self.bit_depth_combo.setVisible(is_bit_depth_visible)
        self.bit_depth_combo.setEnabled(is_bit_depth_visible)

        if is_bit_depth_visible:
            self.bit_depth_label.setText("位深:" if is_wav else "采样格式:")

    def auto_set_output_path(self, input_path):
        if not input_path: return
        base_path, _ = os.path.splitext(input_path)
        selected_format = self.format_combo.currentText()
        self.output_edit.setText(f"{base_path}_output.{selected_format}")

    def select_output_path(self):
        filter_str = f"{self.format_combo.currentText().upper()} (*.{self.format_combo.currentText()});;All Files (*)"
        default_path = self.output_edit.text() or os.path.dirname(self.input_edit.text())
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出路径", default_path, filter_str)
        if file_name: self.output_edit.setText(file_name)
        
    def _validate_inputs(self):
        if not self.input_edit.text() or not os.path.exists(self.input_edit.text()):
            display_error(self.console, "输入音频文件不存在或未指定。"); return False
        if not self.output_edit.text():
            display_error(self.console, "输出文件路径不能为空。"); return False
        return True

    def _get_command(self):
        input_file, output_file = self.input_edit.text(), self.output_edit.text()
        command = ["ffmpeg", "-i", input_file]
        
        a_format = self.format_combo.currentText()
        codec = self.codec_combo.currentText()
        if not codec: raise ValueError("未选择任何有效的编码器")
        
        if a_format == 'wav':
            bit_depth_text = self.bit_depth_combo.currentText()
            wav_codec = WAV_BIT_DEPTH_CODECS.get(bit_depth_text, "pcm_s16le")
            command.extend(["-c:a", wav_codec])
        else:
            command.extend(["-c:a", codec])

            if codec != 'copy':
                is_lossy = codec in ['libmp3lame', 'aac', 'opus', 'vorbis']

                if self.bitrate_label.isVisible() and is_lossy:
                    bitrate = self.bitrate_combo.currentText()
                    if bitrate:
                        command.extend(["-b:a", bitrate])
                
                if self.compression_label.isVisible() and codec == 'flac':
                    command.extend(["-compression_level", self.compression_combo.currentText()])

                # MODIFIED: Only add sample format for non-lossy codecs
                if not is_lossy:
                    sample_fmt_text = self.bit_depth_combo.currentText()
                    sample_fmt = AUDIO_SAMPLE_FORMATS.get(sample_fmt_text)
                    if sample_fmt:
                        command.extend(["-sample_fmt", sample_fmt])

        if codec != 'copy':
            sample_rate = self.sample_rate_combo.currentText()
            if sample_rate and sample_rate != "(默认)":
                command.extend(["-ar", sample_rate])

        command.extend(["-y", output_file])
        return command
    
class MuxingTab(BaseTab, Ui_MuxingTab):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setupUi(self)
        self._connect_signals()

    def _connect_signals(self):
        self.select_video_button.clicked.connect(lambda: self.main_window.select_file(self.video_input_edit))
        self.select_audio_button.clicked.connect(lambda: self.main_window.select_file(self.audio_input_edit))
        self.select_subtitle_button.clicked.connect(self.select_subtitle_file)
        self.select_output_button.clicked.connect(self.select_output_path)
        self.run_button.clicked.connect(self._run_command)
    
    def select_subtitle_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择字幕文件", "", SUBTITLE_FORMATS)
        if file_name: self.subtitle_input_edit.setText(file_name)

    def select_output_path(self):
        default_dir = os.path.dirname(self.video_input_edit.text())
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出文件", default_dir, "Media Files (*.mp4 *.mkv)")
        if file_name: self.output_edit.setText(file_name)
        
    def _validate_inputs(self):
        if not self.video_input_edit.text() or not os.path.exists(self.video_input_edit.text()):
            display_error(self.console, "输入的视频文件不存在或未指定。"); return False
        if not self.audio_input_edit.text() or not os.path.exists(self.audio_input_edit.text()):
            display_error(self.console, "输入的音频文件不存在或未指定。"); return False
        if self.subtitle_input_edit.text() and not os.path.exists(self.subtitle_input_edit.text()):
            display_error(self.console, "指定的字幕文件不存在。"); return False
        if not self.output_edit.text():
            display_error(self.console, "输出文件路径不能为空。"); return False
        return True

    def _get_command(self):
        video_file = self.video_input_edit.text()
        audio_file = self.audio_input_edit.text()
        subtitle_file = self.subtitle_input_edit.text()
        output_file = self.output_edit.text()
        
        command = ["ffmpeg", "-i", video_file, "-i", audio_file]
        if subtitle_file:
            command.extend(["-i", subtitle_file])
        
        command.extend(["-map", "0:v:0", "-map", "1:a:0"])
        if subtitle_file:
            command.extend(["-map", "2:s:0"])
        
        command.extend(["-c:v", "copy", "-c:a", "copy"])
        if subtitle_file:
            if output_file.endswith('.mp4'):
                command.extend(["-c:s", "mov_text"])
            else:
                command.extend(["-c:s", "copy"])
                
        command.extend(["-y", output_file])
        return command

class DemuxingTab(BaseTab, Ui_DemuxingTab):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setupUi(self)
        self._connect_signals()
        self.current_stream_type = None

    def _connect_signals(self):
        self.select_input_button.clicked.connect(lambda: self.main_window.select_file(self.input_edit))
        self.extract_video_button.clicked.connect(lambda: self._run_demux_command('video'))
        self.extract_audio_button.clicked.connect(lambda: self._run_demux_command('audio'))

    def _run_demux_command(self, stream_type):
        self.current_stream_type = stream_type
        self._run_command()

    def set_buttons_enabled(self, enabled):
        self.extract_video_button.setEnabled(enabled)
        self.extract_audio_button.setEnabled(enabled)
    
    def _validate_inputs(self):
        if not self.input_edit.text() or not os.path.exists(self.input_edit.text()):
            display_error(self.console, "输入文件不存在或未指定。"); return False
        return True

    def _get_command(self):
        input_file = self.input_edit.text()
        base, ext = os.path.splitext(input_file)
        
        if self.current_stream_type == 'video':
            output_file = f"{base}_video_only{ext}"
            return ["ffmpeg", "-i", input_file, "-c:v", "copy", "-an", "-y", output_file]
        elif self.current_stream_type == 'audio':
            output_file = f"{base}_audio_only.mka"
            return ["ffmpeg", "-i", input_file, "-c:a", "copy", "-vn", "-y", output_file]
        return None

class CommonOperationsTab(BaseTab, Ui_CommonOpsTab):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setupUi(self)
        self._connect_signals()
        self.current_command_type = None

    def _connect_signals(self):
        self.select_trim_input_button.clicked.connect(lambda: self.main_window.select_file(self.trim_input_edit))
        self.select_trim_output_button.clicked.connect(self.select_trim_output_path)
        self.trim_button.clicked.connect(lambda: self._run_specific_command('trim'))
        
        self.select_img_button.clicked.connect(self.select_image_file)
        self.select_audio_button.clicked.connect(lambda: self.main_window.select_file(self.audio_input_edit))
        self.select_img_audio_output_button.clicked.connect(self.select_img_audio_output_path)
        self.img_audio_button.clicked.connect(lambda: self._run_specific_command('img_audio'))

    def _run_specific_command(self, command_type):
        self.current_command_type = command_type
        self._run_command()

    def set_buttons_enabled(self, enabled):
        self.trim_button.setEnabled(enabled)
        self.img_audio_button.setEnabled(enabled)

    def select_trim_output_path(self):
        default_dir = os.path.dirname(self.trim_input_edit.text())
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出文件", default_dir)
        if file_name: self.trim_output_edit.setText(file_name)

    def select_image_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择图片文件", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_name: self.img_input_edit.setText(file_name)

    def select_img_audio_output_path(self):
        default_dir = os.path.dirname(self.img_input_edit.text())
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出视频", default_dir, "Video Files (*.mp4)")
        if file_name: self.img_audio_output_edit.setText(file_name)

    def _validate_inputs(self):
        if self.current_command_type == 'trim':
            if not self.trim_input_edit.text() or not os.path.exists(self.trim_input_edit.text()):
                display_error(self.console, "截取输入的视频文件不存在或未指定。"); return False
            if not self.trim_output_edit.text():
                display_error(self.console, "截取输出的文件路径不能为空。"); return False
            if not validate_time_format(self.start_time_edit.text()):
                display_error(self.console, f"无效的开始时间格式: {self.start_time_edit.text()}"); return False
            if not validate_time_format(self.end_time_edit.text()):
                display_error(self.console, f"无效的结束时间格式: {self.end_time_edit.text()}"); return False
        elif self.current_command_type == 'img_audio':
            if not self.img_input_edit.text() or not os.path.exists(self.img_input_edit.text()):
                display_error(self.console, "输入的图片文件不存在或未指定。"); return False
            if not self.audio_input_edit.text() or not os.path.exists(self.audio_input_edit.text()):
                display_error(self.console, "输入的音频文件不存在或未指定。"); return False
            if not self.img_audio_output_edit.text():
                display_error(self.console, "图声合成的输出路径不能为空。"); return False
        return True

    def _get_command(self):
        if self.current_command_type == 'trim':
            input_file = self.trim_input_edit.text()
            output_file = self.trim_output_edit.text()
            start_time = self.start_time_edit.text()
            end_time = self.end_time_edit.text()

            command = ["ffmpeg", "-i", input_file, "-c", "copy"]
            if start_time and start_time != '00:00:00':
                command.extend(["-ss", start_time])
            if end_time:
                command.extend(["-to", end_time])
            command.extend(["-y", output_file])
            return command

        elif self.current_command_type == 'img_audio':
            img_file = self.img_input_edit.text()
            audio_file = self.audio_input_edit.text()
            output_file = self.img_audio_output_edit.text()
            
            command = [
                "ffmpeg", "-loop", "1", "-i", img_file,
                "-i", audio_file,
                "-c:v", "libx264", "-tune", "stillimage",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-y", output_file
            ]
            return command
        return None

class ProfessionalTab(BaseTab, Ui_ProfessionalTab):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setupUi(self)
        self._connect_signals()

    def _connect_signals(self):
        self.run_button.clicked.connect(self._run_command)
    
    def _validate_inputs(self):
        if not self.command_input.toPlainText().strip():
            display_error(self.console, "命令不能为空。")
            return False
        return True

    def _get_command(self):
        command_text = self.command_input.toPlainText().strip()
        try:
            import shlex
            return shlex.split(command_text)
        except ImportError:
            return command_text.split()

# --- 修改后的 AboutTab ---
class AboutTab(BaseTab, Ui_AboutTab):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setupUi(self)

    def set_buttons_enabled(self, enabled):
        # 此选项卡没有需要禁用的按钮
        pass