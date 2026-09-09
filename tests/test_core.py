import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QTextEdit

from config import get_config
from process_handler import ProcessHandler
from ui_tabs import (
    AudioTab,
    CommonOperationsTab,
    DemuxingTab,
    MuxingTab,
    ProfessionalTab,
    VideoTab,
    output_file_args,
)
from validators import validate_fps, validate_resolution, validate_time_format


class DummyMainWindow:
    def __init__(self, process_handler=None):
        self.process_handler = process_handler or ProcessHandler()
        self.console = QTextEdit()


class ValidatorTests(unittest.TestCase):
    def test_rejects_invalid_time_resolution_and_fps(self):
        self.assertFalse(validate_time_format("00:60:00"))
        self.assertTrue(validate_time_format("100:59:59.5"))
        self.assertFalse(validate_resolution("1920:-999"))
        self.assertTrue(validate_resolution("-1:720"))
        self.assertFalse(validate_fps("inf"))


class CommandConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.main_window = DummyMainWindow()

    def test_professional_command_preserves_windows_path(self):
        tab = ProfessionalTab(self.main_window)
        tab.command_input.setPlainText(
            'ffmpeg -i "C:\\Media Files\\input.mp4" output.mp4'
        )

        self.assertEqual(
            tab._get_command(),
            ["ffmpeg", "-i", r"C:\Media Files\input.mp4", "output.mp4"],
        )

    def test_stream_copy_rejects_filtering_options(self):
        tab = VideoTab(self.main_window)
        tab.input_edit.setText(str(Path("assets/logo.png").resolve()))
        tab.output_edit.setText(str(Path("assets/output.mp4").resolve()))
        tab.video_codec_combo.setCurrentText("copy")
        tab.resolution_edit.setText("1280:-1")

        self.assertFalse(tab._validate_inputs())

    def test_overwrite_setting_produces_noninteractive_flag(self):
        config = get_config()
        original_value = config.get("overwrite_files")
        try:
            config.set("overwrite_files", False)
            self.assertEqual(output_file_args("output.mp4"), ["-n", "output.mp4"])
        finally:
            config.set("overwrite_files", original_value)


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "FFmpeg and FFprobe are required for this test",
)
class ProcessHandlerTests(unittest.TestCase):
    def test_failed_start_is_reported_without_leaving_a_running_process(self):
        handler = ProcessHandler()
        handler._get_ffmpeg_path = lambda: "__skydreambox_missing_ffmpeg__"

        started, message = handler.run_ffmpeg(["ffmpeg", "-version"])

        self.assertFalse(started)
        self.assertIn("无法启动 FFmpeg", message)
        self.assertFalse(handler._is_process_active(handler.ffmpeg_process))

    def test_check_rejects_an_unrelated_executable(self):
        handler = ProcessHandler()
        handler._get_ffmpeg_path = lambda: "ffprobe"
        handler._get_ffprobe_path = lambda: "ffprobe"

        is_ready, message = handler.check_ffmpeg()

        self.assertFalse(is_ready)
        self.assertIn("不是有效的 FFmpeg", message)


@unittest.skipUnless(shutil.which("ffprobe"), "FFprobe is required for this test")
class ProbeProcessTests(unittest.TestCase):
    def test_probe_output_remains_available_after_process_finished(self):
        handler = ProcessHandler()
        handler._get_ffprobe_path = lambda: "ffprobe"

        started, message = handler.run_ffprobe(str(Path("assets/logo.png").resolve()))

        self.assertTrue(started, message)
        self.assertTrue(handler.ffprobe_process.waitForFinished(5000))
        output = bytes(handler.ffprobe_process.readAllStandardOutput()).decode("utf-8")
        self.assertIn('"format"', output)


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "FFmpeg and FFprobe are required for this test",
)
class EndToEndCommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def execute(self, handler, command):
        started, message = handler.run_ffmpeg(command)
        self.assertTrue(started, message)
        self.assertTrue(handler.ffmpeg_process.waitForFinished(10_000))
        error_output = bytes(handler.ffmpeg_process.readAllStandardError()).decode(
            "utf-8", "ignore"
        )
        self.assertEqual(handler.ffmpeg_process.exitCode(), 0, error_output)

    def test_generated_media_commands_complete(self):
        config = get_config()
        original_overwrite = config.get("overwrite_files")
        config.set("overwrite_files", True)

        try:
            with tempfile.TemporaryDirectory(prefix="Sky Dream Box ") as temporary_directory:
                temp_dir = Path(temporary_directory)
                source_file = temp_dir / "source.mp4"
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        "testsrc=size=160x90:rate=25",
                        "-f",
                        "lavfi",
                        "-i",
                        "sine=frequency=1000:sample_rate=44100",
                        "-t",
                        "1",
                        "-c:v",
                        "mpeg4",
                        "-c:a",
                        "aac",
                        "-shortest",
                        str(source_file),
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                handler = ProcessHandler()
                handler._get_ffmpeg_path = lambda: "ffmpeg"
                main_window = DummyMainWindow(handler)

                subtitle_file = temp_dir / "caption file.srt"
                subtitle_file.write_text(
                    "1\n00:00:00,000 --> 00:00:00,500\nSkyDreamBox\n",
                    encoding="utf-8",
                )
                subtitle_output = temp_dir / "subtitled.mp4"
                subtitle_tab = VideoTab(main_window)
                subtitle_tab.input_edit.setText(str(source_file))
                subtitle_tab.output_edit.setText(str(subtitle_output))
                subtitle_tab.subtitle_edit.setText(str(subtitle_file))
                subtitle_tab.video_codec_combo.setCurrentText("mpeg4")
                subtitle_tab.audio_codec_combo.setCurrentText("aac")
                self.assertTrue(subtitle_tab._validate_inputs())
                self.execute(handler, subtitle_tab._get_command())
                self.assertTrue(subtitle_output.exists())

                video_output = temp_dir / "converted.avi"
                video_tab = VideoTab(main_window)
                video_tab.input_edit.setText(str(source_file))
                video_tab.output_edit.setText(str(video_output))
                video_tab.format_combo.setCurrentText("avi")
                video_tab.video_codec_combo.setCurrentText("mpeg4")
                video_tab.audio_codec_combo.setCurrentText("aac")
                video_tab.resolution_edit.setText("128:-2")
                self.assertTrue(video_tab._validate_inputs())
                self.execute(handler, video_tab._get_command())
                self.assertTrue(video_output.exists())

                audio_output = temp_dir / "audio.aac"
                audio_tab = AudioTab(main_window)
                audio_tab.input_edit.setText(str(source_file))
                audio_tab.output_edit.setText(str(audio_output))
                audio_tab.format_combo.setCurrentText("aac")
                self.assertTrue(audio_tab._validate_inputs())
                self.execute(handler, audio_tab._get_command())
                self.assertTrue(audio_output.exists())

                mux_output = temp_dir / "muxed.mkv"
                muxing_tab = MuxingTab(main_window)
                muxing_tab.video_input_edit.setText(str(video_output))
                muxing_tab.audio_input_edit.setText(str(audio_output))
                muxing_tab.output_edit.setText(str(mux_output))
                self.assertTrue(muxing_tab._validate_inputs())
                self.execute(handler, muxing_tab._get_command())
                self.assertTrue(mux_output.exists())

                demuxing_tab = DemuxingTab(main_window)
                demuxing_tab.input_edit.setText(str(mux_output))
                demuxing_tab.current_stream_type = "video"
                self.assertTrue(demuxing_tab._validate_inputs())
                self.execute(handler, demuxing_tab._get_command())
                self.assertTrue((temp_dir / "muxed_video_only.mkv").exists())

                trimmed_output = temp_dir / "trimmed.mp4"
                common_tab = CommonOperationsTab(main_window)
                common_tab.current_command_type = "trim"
                common_tab.trim_input_edit.setText(str(source_file))
                common_tab.trim_output_edit.setText(str(trimmed_output))
                common_tab.start_time_edit.setText("00:00:00")
                common_tab.end_time_edit.setText("00:00:00.5")
                self.assertTrue(common_tab._validate_inputs())
                self.execute(handler, common_tab._get_command())
                self.assertTrue(trimmed_output.exists())

                image_audio_output = temp_dir / "image-audio.mp4"
                common_tab.current_command_type = "img_audio"
                common_tab.img_input_edit.setText(str(Path("assets/logo.png").resolve()))
                common_tab.audio_input_edit.setText(str(audio_output))
                common_tab.img_audio_output_edit.setText(str(image_audio_output))
                self.assertTrue(common_tab._validate_inputs())
                self.execute(handler, common_tab._get_command())
                self.assertTrue(image_audio_output.exists())
        finally:
            config.set("overwrite_files", original_overwrite)


if __name__ == "__main__":
    unittest.main()
