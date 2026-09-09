import copy
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt, QMimeData, QUrl, QPoint, QPointF
from PySide6.QtGui import QDropEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from core.commands import build_plan, video_args
from core.models import CommandPlan, MediaInfo, StreamInfo, TaskSpec, TaskStatus, output_path, task_outputs, allocate_output
from core.queue import TaskQueue
from core.services import ProbeService, EngineService
from config import Config


APP = QApplication.instance() or QApplication([])


def wait_until(predicate, timeout=15000):
    deadline = time.monotonic() + timeout / 1000
    while not predicate() and time.monotonic() < deadline:
        QTest.qWait(10)
    if not predicate():
        raise AssertionError("异步操作超时")


class TestConfig:
    def __init__(self, directory):
        self.config_dir = Path(directory)
        self.data = {"ffmpeg_path": "ffmpeg", "ffprobe_path": "ffprobe", "overwrite_files": False, "presets": {}}

    def get_ffmpeg_path(self):
        return self.data["ffmpeg_path"]

    def get_ffprobe_path(self):
        return self.data["ffprobe_path"]

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value

    def save(self):
        return True


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="SDB 规划 ")
        self.directory = Path(self.temp.name)
        self.source = self.directory / "source.mp4"
        self.source.touch()
        self.media = MediaInfo(str(self.source), 10, [StreamInfo(0, "video", "h264"), StreamInfo(1, "audio", "aac", bits=24)])

    def tearDown(self):
        self.temp.cleanup()

    def task(self, operation="video", suffix="mp4", **options):
        return TaskSpec(operation, str(self.source), str(self.directory / f"output.{suffix}"), options)

    def test_software_quality_and_hardware_controls_are_distinct(self):
        cases = [("libx264", "CRF", "medium", "-crf"), ("h264_nvenc", "CQ", "p5", "-cq"), ("hevc_qsv", "CQ", "medium", "-global_quality"), ("h264_amf", "CQ", "quality", "-qp_i"), ("libaom-av1", "CRF", "4", "-cpu-used")]
        for codec, mode, preset, flag in cases:
            with self.subTest(codec=codec):
                args = video_args(dict(video_codec=codec, quality_mode=mode, preset=preset), self.media, {codec})
                self.assertIn(flag, args)
                if "nvenc" in codec:
                    self.assertNotIn("-crf", args)
        with self.assertRaisesRegex(ValueError, "不提供"):
            video_args({}, self.media, set())
        with self.assertRaises(ValueError):
            video_args(dict(video_codec="h264_nvenc", quality_mode="CRF", preset="p5"), self.media)
        with self.assertRaisesRegex(ValueError, "速度"):
            video_args(dict(video_codec="h264_qsv", quality_mode="CQ", preset="ultrafast"), self.media)

    def test_rejects_hdr_without_confirmation_and_nonfinite_quality(self):
        self.media.streams[0].color_transfer = "smpte2084"
        with self.assertRaisesRegex(ValueError, "HDR"):
            build_plan(self.task(), self.media)
        args = build_plan(self.task(hdr_confirmed=True, pix_fmt="yuv420p10le", color_transfer="smpte2084"), self.media).commands[0]
        self.assertIn("yuv420p10le", args)
        with self.assertRaises(ValueError):
            build_plan(self.task(quality=float("nan")), self.media)

    def test_container_compatibility_and_explicit_mapping(self):
        self.media.streams[1].codec = "flac"
        with self.assertRaisesRegex(ValueError, "不支持"):
            build_plan(self.task("mux", streams=[0, 1]), self.media)
        args = build_plan(self.task("mux", "mkv", streams=[1]), self.media).commands[0]
        self.assertEqual(args[args.index("-map") + 1], "0:1")
        self.assertIn("copy", args)

    def test_external_audio_index_not_overwritten_by_source_mapping(self):
        external = self.directory / "external.mka"
        external.touch()
        info = MediaInfo(str(external), 10, [StreamInfo(3, "audio", "aac")])
        task = self.task("mux", streams=[0], external_audio=str(external), external_audio_stream=3)
        args = build_plan(task, self.media, {str(external): info}).commands[0]
        self.assertIn("1:3", args)
        self.assertIn("0:0", args)

    def test_subtitle_paths_are_staged_without_filter_path_interpolation(self):
        subtitle = self.directory / "字幕 ' [a],;=.srt"
        subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\n测试\n", encoding="utf-8")
        task = self.task("subtitle", subtitle=str(subtitle), subtitle_mode="burn")
        plan = build_plan(task, self.media)
        self.assertIn(str(subtitle), plan.copies.values())
        filter_arg = plan.commands[0][plan.commands[0].index("-vf") + 1]
        self.assertIn("caption.srt", filter_arg)
        self.assertNotIn(str(subtitle), filter_arg)
        soft = build_plan(self.task("subtitle", subtitle=str(subtitle), subtitle_mode="soft"), self.media)
        self.assertIn("mov_text", soft.commands[0])

    def test_trim_validation_and_multistep_outputs(self):
        with self.assertRaisesRegex(ValueError, "片段"):
            build_plan(self.task("trim", segments=[[0, 11]]), self.media)
        plan = build_plan(self.task("trim", segments=[[0, 2], [4, 6]], merge=True), self.media)
        self.assertEqual(len(plan.commands), 3)
        self.assertEqual(len(plan.publications), 1)
        self.assertIn("file 'part001.mp4'", next(iter(plan.text_files.values())))
        separate = build_plan(self.task("trim", segments=[[0, 2], [4, 6]]), self.media)
        self.assertTrue(separate.publications[0][1].endswith("_001.mp4"))

    def test_output_and_source_collision(self):
        task = self.task()
        task.output = task.source
        with self.assertRaisesRegex(ValueError, "输入"):
            build_plan(task, self.media)
        first = output_path(self.source, "video", "mp4")
        second = output_path(self.source, "video", "mp4", [first])
        self.assertNotEqual(first, second)

    def test_audio_containers_and_flv_track_limits(self):
        with self.assertRaisesRegex(ValueError, "流类型"):
            build_plan(self.task("mux", "mka", streams=[0]), self.media)
        self.media.streams.append(StreamInfo(2, "audio", "aac"))
        with self.assertRaisesRegex(ValueError, "一条"):
            build_plan(self.task("mux", "flv", streams=[0, 1, 2]), self.media)

    def test_trim_output_reservations_include_every_segment(self):
        task = self.task("trim", segments=[[0, 1], [2, 3]])
        self.assertEqual(len(task_outputs(task)), 2)
        self.assertTrue(task_outputs(task)[1].endswith("output_002.mp4"))
        existing = self.directory / "source_trim_001.mp4"
        existing.touch()
        allocated = allocate_output(self.source, "trim", "mp4", task.options)
        self.assertTrue(allocated.endswith("source_trim_2.mp4"))

    def test_legacy_forms_stage_outputs_and_reject_input_overwrite(self):
        task = self.task("legacy", args=["-i", str(self.source), "-c", "copy", "-y"], inputs=[str(self.source)])
        plan = build_plan(task, self.media)
        self.assertNotIn("-y", plan.commands[0])
        self.assertNotEqual(plan.commands[0][-1], task.output)
        self.assertEqual(plan.publications[0][1], task.output)

    def test_alac_must_use_m4a_and_audio_selection_is_explicit(self):
        with self.assertRaisesRegex(ValueError, "扩展名"):
            build_plan(self.task("audio", "alac", audio_format="ALAC"), self.media)
        args = build_plan(self.task("audio", "m4a", audio_format="ALAC", audio_stream=1), self.media).commands[0]
        self.assertIn("alac", args)
        self.assertIn("0:1", args)
        self.assertIn("24", args)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = TestConfig(self.temp.name)
        self.probe = ProbeService(self.config)
        self.queue = TaskQueue(self.config, self.probe)

    def tearDown(self):
        self.temp.cleanup()

    def test_queue_snapshots_edit_order_and_recovery(self):
        options = {"segments": [[0, 1]]}
        first = self.queue.add(TaskSpec("trim", "a", "b", options))
        options["segments"][0][1] = 99
        self.assertEqual(first.options["segments"], [[0, 1]])
        second = self.queue.add(TaskSpec("video", "c", "d"))
        self.queue.move(second.id, -1)
        self.assertEqual(self.queue.tasks[0].id, second.id)
        first.status = TaskStatus.RUNNING
        self.queue.save()
        restored = TaskQueue(self.config, self.probe)
        self.assertTrue(restored.paused)
        self.assertEqual(restored.tasks[1].status, TaskStatus.INTERRUPTED)
        restored.retry(first.id)
        self.assertEqual(restored.tasks[1].status, TaskStatus.PENDING)

    def test_corrupt_queue_is_not_overwritten(self):
        self.queue.storage.write_text("broken", encoding="utf-8")
        restored = TaskQueue(self.config, self.probe)
        self.assertTrue(restored.load_error)
        self.assertFalse(restored.save())
        self.assertEqual(self.queue.storage.read_text(), "broken")

    def test_config_migrates_and_keeps_existing_overwrite(self):
        config_path = Path(self.temp.name) / "config.json"
        config_path.write_text(json.dumps({"ffmpeg_path": "custom.exe", "overwrite_files": True}), encoding="utf-8")
        with patch.object(Config, "_get_config_dir", return_value=Path(self.temp.name)):
            config = Config()
        self.assertTrue(config.get("overwrite_files"))
        self.assertEqual(config.get("config_version"), 2)
        self.assertEqual(config.get("presets"), {})

    def test_publication_failure_rolls_back_only_owned_outputs(self):
        directory = Path(self.temp.name)
        staging = directory / "owned"
        staging.mkdir()
        first = staging / "first.txt"
        second = staging / "second.txt"
        first.write_text("new first")
        second.write_text("new second")
        final1, final2 = directory / "final1.txt", directory / "final2.txt"
        final2.write_text("unrelated existing data")
        self.queue.current = TaskSpec("audio", "", "", {"overwrite": False})
        self.queue.plan = CommandPlan([], [], [(str(first), str(final1)), (str(second), str(final2))], temp_dir=str(staging))
        with self.assertRaises(OSError):
            self.queue._publish()
        self.assertFalse(final1.exists())
        self.assertEqual(final2.read_text(), "unrelated existing data")

    def test_overwrite_publication_preserves_old_file_on_failure(self):
        directory = Path(self.temp.name)
        staging = directory / "owned"
        staging.mkdir()
        first = staging / "first.txt"
        first.write_text("new content")
        original = directory / "original.txt"
        original.write_text("old content")
        self.queue.current = TaskSpec("audio", "", "", {"overwrite": True})
        self.queue.plan = CommandPlan([], [], [(str(first), str(original)), (str(staging / "missing"), str(directory / "second.txt"))], temp_dir=str(staging))
        with self.assertRaises(OSError):
            self.queue._publish()
        self.assertEqual(original.read_text(), "old content")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "需要 FFmpeg/FFprobe")
class MediaIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="SDB 媒体 ' ")
        cls.directory = Path(cls.temp.name)
        cls.source = cls.directory / "source.mp4"
        cls.run_ffmpeg(["-f", "lavfi", "-i", "testsrc2=size=160x96:rate=25", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "3", "-c:v", "libx264", "-g", "25", "-bf", "0", "-c:a", "aac", str(cls.source)])
        cls.media = cls.inspect(cls.source)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @staticmethod
    def run_ffmpeg(args, cwd=None):
        result = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-nostdin"] + args, capture_output=True, cwd=cwd, timeout=30)
        if result.returncode:
            raise AssertionError(result.stderr.decode("utf-8", "replace"))

    @staticmethod
    def inspect(path):
        result = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], capture_output=True, check=True, timeout=10)
        return MediaInfo.from_probe(str(path), json.loads(result.stdout))

    def execute(self, operation, suffix, **options):
        output = output_path(self.source, operation, suffix)
        task = TaskSpec(operation, str(self.source), output, options)
        plan = build_plan(task, self.media)
        Path(plan.temp_dir).mkdir()
        try:
            for path, text in plan.text_files.items():
                Path(path).write_text(text, encoding="utf-8")
            for destination, source in plan.copies.items():
                shutil.copyfile(source, destination)
            for command in plan.commands:
                self.run_ffmpeg(command, plan.temp_dir)
            outputs = []
            for temporary, final in plan.publications:
                shutil.move(temporary, final)
                outputs.append(Path(final))
            return outputs
        finally:
            shutil.rmtree(plan.temp_dir)

    def test_video_compression_properties(self):
        path = self.execute("video", "mp4", quality=18, resolution="128:-2", fps="20")[0]
        info = self.inspect(path)
        self.assertEqual(info.streams[0].codec, "h264")
        self.assertEqual(info.streams[0].width, 128)
        self.assertAlmostEqual(info.duration, 3, delta=0.15)

    def test_all_four_audio_formats(self):
        for fmt, suffix, codec in [("AAC", "aac", "aac"), ("AAC", "m4a", "aac"), ("WAV", "wav", "pcm_s24le"), ("FLAC", "flac", "flac"), ("ALAC", "m4a", "alac")]:
            with self.subTest(fmt=fmt, suffix=suffix):
                path = self.execute("audio", suffix, audio_format=fmt, bits=24)[0]
                info = self.inspect(path)
                self.assertEqual(len(info.streams), 1)
                self.assertEqual(info.streams[0].codec, codec)
                self.assertEqual(info.streams[0].sample_rate, 48000)
                if suffix == "aac":
                    # ADTS has no duration index; ffprobe estimates from bitrate.
                    decoded = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-"], capture_output=True, check=True)
                    duration = len(decoded.stdout) / (2 * info.streams[0].sample_rate * info.streams[0].channels)
                else:
                    duration = info.duration
                self.assertAlmostEqual(duration, 3, delta=0.25)

    def test_soft_subtitle_and_burn_with_special_path(self):
        subtitle = self.directory / "字幕 ' [a],;=.srt"
        subtitle.write_text("1\n00:00:00,000 --> 00:00:02,000\nSkyDreamBox\n", encoding="utf-8")
        for suffix in ("mp4", "mkv"):
            path = self.execute("subtitle", suffix, subtitle=str(subtitle), subtitle_mode="soft")[0]
            self.assertTrue(any(s.kind == "subtitle" for s in self.inspect(path).streams))
        burned = self.execute("subtitle", "mp4", subtitle=str(subtitle), subtitle_mode="burn")[0]
        self.assertFalse(any(s.kind == "subtitle" for s in self.inspect(burned).streams))
        def frame(path):
            return subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        # Compare against identically encoded video, so this tests visible subtitle rendering.
        plain = self.execute("video", "mp4")[0]
        self.assertNotEqual(frame(burned), frame(plain))

    def test_copy_and_precise_trim_separate_and_merge(self):
        separate = self.execute("trim", "mp4", segments=[[0, 0.8], [1, 1.8]], trim_mode="encode")
        self.assertEqual(len(separate), 2)
        for path in separate:
            self.assertAlmostEqual(self.inspect(path).duration, 0.8, delta=0.12)
        merged = self.execute("trim", "mp4", segments=[[0, 1], [2, 3]], merge=True, trim_mode="copy")[0]
        self.assertAlmostEqual(self.inspect(merged).duration, 2, delta=0.3)
        accurate = self.execute("trim", "mp4", segments=[[0.32, 0.88]], trim_mode="encode")[0]
        self.assertAlmostEqual(self.inspect(accurate).duration, 0.56, delta=0.1)

    def test_remux_and_extract_preserve_packet_payloads(self):
        def hashes(path, select):
            result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", select, "-show_packets", "-show_data_hash", "sha256", "-show_entries", "packet=data_hash", "-of", "json", str(path)], capture_output=True, check=True)
            return [p["data_hash"] for p in json.loads(result.stdout)["packets"]]
        original_video = hashes(self.source, "v:0")
        original_audio = hashes(self.source, "a:0")
        for suffix in ("mp4", "mkv", "flv"):
            with self.subTest(suffix=suffix):
                path = self.execute("mux", suffix, streams=[0, 1])[0]
                self.assertEqual(hashes(path, "v:0"), original_video)
                self.assertEqual(hashes(path, "a:0"), original_audio)
        path = self.execute("mux", "m4a", streams=[1])[0]
        self.assertEqual(hashes(path, "a:0"), original_audio)

    def test_async_queue_failure_continues_and_publishes(self):
        config = TestConfig(self.directory)
        probe = ProbeService(config)
        queue = TaskQueue(config, probe, storage=self.directory / "integration-queue.json")
        bad = queue.add(TaskSpec("raw", "", "", {"args": ["-invalid_sdb_option"]}))
        output = output_path(self.source, "queued", "flac")
        good = queue.add(TaskSpec("audio", str(self.source), output, {"audio_format": "FLAC"}))
        queue.start()
        wait_until(lambda: good.status in {TaskStatus.COMPLETED, TaskStatus.FAILED})
        self.assertEqual(bad.status, TaskStatus.FAILED)
        self.assertEqual(good.status, TaskStatus.COMPLETED, good.error)
        self.assertTrue(Path(output).exists())
        self.assertFalse(list(self.directory.glob(".skydreambox-*")))
        queue.pause()

    def test_async_cancel_and_failed_start(self):
        config = TestConfig(self.directory)
        probe = ProbeService(config)
        queue = TaskQueue(config, probe, storage=self.directory / "cancel-queue.json")
        task = queue.add(TaskSpec("raw", "", "", {"args": ["-re", "-f", "lavfi", "-i", "color=size=64x64:rate=1", "-t", "30", "-f", "null", "-"]}))
        queue.start()
        wait_until(lambda: queue.process.state() == queue.process.ProcessState.Running)
        queue.pause()
        queue.cancel()
        wait_until(lambda: task.status == TaskStatus.CANCELLED)
        config.data["ffmpeg_path"] = "__missing_sdb_ffmpeg__"
        queue.retry(task.id)
        queue.start()
        wait_until(lambda: task.status == TaskStatus.FAILED)
        self.assertIn("无法启动", task.error)
        queue.pause()

    def test_typed_failure_cleans_staging_and_keeps_existing_files(self):
        config = TestConfig(self.directory)
        probe = ProbeService(config)
        queue = TaskQueue(config, probe, storage=self.directory / "cleanup-queue.json")
        output = output_path(self.source, "bad", "mp4")
        # x264 refuses dimensions not divisible by two with yuv420p.
        task = queue.add(TaskSpec("video", str(self.source), output, {"resolution": "161:95", "pix_fmt": "yuv420p"}))
        original = self.source.read_bytes()
        queue.start()
        wait_until(lambda: task.status == TaskStatus.FAILED)
        self.assertFalse(Path(output).exists())
        self.assertFalse(list(self.directory.glob(".skydreambox-*")))
        self.assertEqual(self.source.read_bytes(), original)
        queue.pause()

    def test_retry_does_not_reuse_crashed_attempt_directory(self):
        config = TestConfig(self.directory)
        probe = ProbeService(config)
        queue = TaskQueue(config, probe, storage=self.directory / "retry-queue.json")
        output = output_path(self.source, "retry", "flac")
        task = queue.add(TaskSpec("audio", str(self.source), output, {"audio_format": "FLAC"}))
        stale = self.directory / f".skydreambox-{task.id}"
        stale.mkdir()
        marker = stale / "crash.txt"
        marker.write_text("previous attempt")
        try:
            queue.start()
            wait_until(lambda: task.status in {TaskStatus.FAILED, TaskStatus.COMPLETED})
            self.assertEqual(task.status, TaskStatus.COMPLETED, task.error)
            self.assertEqual(marker.read_text(), "previous attempt")
        finally:
            queue.pause()
            shutil.rmtree(stale)


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        from workbench import Workbench
        self.temp = tempfile.TemporaryDirectory()
        self.config = TestConfig(self.temp.name)
        self.window = Workbench(config=self.config, start_engine=False)
        self.window.show()
        APP.processEvents()

    def tearDown(self):
        self.window.close()
        APP.processEvents()
        self.temp.cleanup()

    def test_pages_and_window_work_without_engine(self):
        for row in range(7):
            self.window.navigation.setCurrentRow(row)
            APP.processEvents()
            self.assertTrue(self.window.is_ready)
        self.assertEqual(self.window.pages.currentIndex(), 2)
        self.window.resize(900, 620)
        APP.processEvents()
        self.assertLessEqual(self.window.width(), 900)

    def test_missing_engine_reports_error_without_closing_settings(self):
        self.config.data["ffmpeg_path"] = "__missing_sdb_engine__"
        self.window.engine.refresh()
        wait_until(lambda: "不可用" in self.window.engine.message)
        self.window.navigation.setCurrentRow(6)
        self.assertTrue(self.window.isVisible())
        self.assertFalse(self.window.engine.ready)

    def test_form_roundtrip_and_codec_controls(self):
        form = self.window.forms["video"]
        form.restore({"video_codec": "h264_nvenc", "quality_mode": "CQ", "preset": "p6", "quality": 22, "resolution": "1280:-2"})
        values = form.values()
        self.assertEqual(values["preset"], "p6")
        self.assertEqual(values["quality_mode"], "CQ")
        self.assertEqual(values["resolution"], "1280:-2")
        self.window.forms["audio"].restore({"audio_format": "ALAC", "container": "m4a", "bits": 24})
        self.assertEqual(self.window.forms["audio"].values()["container"], "m4a")

    def test_drop_adds_file_and_missing_subtitle_is_visible(self):
        path = Path(self.temp.name) / "example.mp4"
        path.touch()
        self.window.probe.request = lambda *args, **kwargs: None
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(path))])
        event = QDropEvent(QPointF(20, 20), Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        self.window.file_table.dropEvent(event)
        self.assertEqual(self.window.file_table.rowCount(), 1)
        self.window.navigation.setCurrentRow(2)
        self.assertIn("未配对", self.window.file_table.item(0, 2).text())

    def test_batch_enqueues_all_files_and_edit_preserves_snapshot(self):
        self.window.probe.request = lambda *args, **kwargs: None
        self.window.engine.ready = True
        self.window.engine.encoders = {"libx264", "aac"}
        paths = []
        for name in ("one.mp4", "two.mp4"):
            path = str(Path(self.temp.name) / name)
            Path(path).touch()
            self.window.probe.cache[path] = MediaInfo(path, 3, [StreamInfo(0, "video", "h264"), StreamInfo(1, "audio", "aac")])
            paths.append(path)
        self.window.add_files(paths)
        for path in paths:
            self.window._media_ready(path, self.window.probe.cache[path])
        self.window.enqueue()
        self.assertEqual(len(self.window.queue.tasks), 2)
        self.window.forms["video"].restore({"quality": 30})
        self.assertEqual(self.window.queue.tasks[0].options["quality"], 18)
        self.window.queue_table.selectRow(0)
        self.window.edit_task()
        self.window.forms["video"].restore({"quality": 21})
        self.window.enqueue()
        self.assertEqual(len(self.window.queue.tasks), 2)
        self.assertEqual(self.window.queue.tasks[0].options["quality"], 21)
        self.assertEqual(self.window.queue.tasks[1].options["quality"], 18)

    def test_soft_subtitles_expose_audio_conversion(self):
        form = self.window.forms["subtitle"]
        form.restore({"subtitle_mode": "soft", "audio_codec": "aac", "audio_bitrate": "256k"})
        self.assertEqual(form.values()["audio_codec"], "aac")
        self.assertEqual(form.values()["audio_bitrate"], "256k")


if __name__ == "__main__":
    unittest.main()
