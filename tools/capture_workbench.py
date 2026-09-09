"""Generate actual Qt screenshots and exercise preview, without personal settings."""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Exercise the actual platform backend for playback. Windows' offscreen plugin
# has no native audio/window services and cannot validate multimedia teardown.
os.environ.setdefault("QT_QPA_PLATFORM", "windows" if os.name == "nt" else "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from config import Config
from styles import STYLESHEET
from workbench import Workbench
from core.models import TaskStatus


def wait(predicate, timeout=20000):
    deadline = time.monotonic() + timeout / 1000
    while not predicate() and time.monotonic() < deadline:
        QTest.qWait(20)
    if not predicate():
        raise RuntimeError("UI verification timed out")


def main():
    destination = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/screenshots").resolve()
    destination.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    # The Windows offscreen Qt plugin has no system font database.
    for font in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/segoeui.ttf"):
        if Path(font).exists():
            QFontDatabase.addApplicationFont(font)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    with tempfile.TemporaryDirectory(prefix="SDB-preview-") as directory:
        folder = Path(directory)
        source = folder / "海边旅行 · 示例.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=25", "-f", "lavfi", "-i", "sine=frequency=440", "-t", "3", "-c:v", "libx264", "-c:a", "aac", str(source)], check=True)
        with patch.object(Config, "_get_config_dir", return_value=folder):
            config = Config()
        window = Workbench(config=config)
        window.show()
        wait(lambda: window.engine.ready)
        window.add_files([str(source)])
        wait(lambda: str(source) in window.probe.cache)
        window.enqueue()
        if not window.queue.tasks:
            raise RuntimeError(window.notification.text() + repr(window.records))
        window.queue.start()
        wait(lambda: window.queue.tasks[0].status in {TaskStatus.COMPLETED, TaskStatus.FAILED})
        if window.queue.tasks[0].status != TaskStatus.COMPLETED:
            raise RuntimeError(window.queue.tasks[0].error)
        window.notification.hide()
        window.queue_table.selectRow(0)
        QTest.qWait(100)
        window.grab().save(str(destination / "workbench.png"))
        window.navigation.setCurrentRow(1)
        preview = window.forms["trim"].preview
        wait(lambda: preview.player.duration() > 0)
        preview.player.setPosition(1000)
        wait(lambda: abs(preview.player.position() - 1000) < 100)
        preview.player.play()
        wait(lambda: preview.player.position() > 1100)
        preview.player.pause()
        form = window.forms["trim"]
        form.segments = [[0, 1], [1.5, 2.8]]
        form.refresh_segments()
        QTest.qWait(100)
        window.grab().save(str(destination / "trim.png"))
        window.resize(900, 620)
        QTest.qWait(100)
        window.grab().save(str(destination / "small-window.png"))
        print("Verified engine, queue, playback and seek; screenshots:", destination, flush=True)
        window.close()
        if window.isVisible():
            # Use the native event loop for decoder teardown, not QTest's event pump.
            QTimer.singleShot(20000, app.quit)
            app.exec()
        if window.isVisible():
            raise RuntimeError("Window did not close after multimedia teardown")


if __name__ == "__main__":
    main()
