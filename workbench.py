"""SkyDreamBox workbench: reusable task forms and one persistent queue."""
import copy
import json
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, QProcess
from PySide6.QtGui import QPalette, QDesktopServices, QIcon, QKeySequence, QPainter, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QSplitter, QStackedWidget, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFileDialog, QMessageBox, QLineEdit,
    QCheckBox, QPlainTextEdit, QTextEdit, QTabWidget, QInputDialog,
    QListWidgetItem, QGroupBox,
)

from config import get_config
from core.commands import build_plan, first_index
from core.models import TaskSpec, TaskStatus, output_path, task_outputs, allocate_output
from core.queue import TaskQueue
from core.services import ProbeService, EngineService
from ui.task_forms import TaskForm, Fields, button, note, VideoFields
from utils import resource_path
from styles import apply_theme, normalize_theme


OPERATIONS = [("video", "视频压制", "自定义编码与画质，保留每一处细节"), ("trim", "音视频粗剪", "预览、标记与导出你需要的片段"), ("subtitle", "字幕处理", "可开关字幕轨，或将字幕固定到画面"), ("audio", "音频转换", "AAC / WAV / FLAC / ALAC"), ("mux", "抽取与封装", "选择媒体流，无损抽取与重新封装")]


class EmptyTable(QTableWidget):
    """Paint a non-interactive hint without interfering with selection or drops."""

    def __init__(self, columns, heading, description):
        super().__init__(0, columns)
        self.empty_heading = heading
        self.empty_description = description
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setDefaultSectionSize(44)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.rowCount():
            return
        painter = QPainter(self.viewport())
        rect = self.viewport().rect().adjusted(12, 8, -12, -8)
        font = self.font()
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(self.palette().color(QPalette.ColorRole.PlaceholderText))
        if rect.height() < 64:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.empty_heading)
            painter.end()
            return
        painter.drawText(rect.adjusted(0, 0, 0, -24), Qt.AlignmentFlag.AlignCenter, self.empty_heading)
        font.setBold(False)
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(self.palette().color(QPalette.ColorRole.PlaceholderText))
        painter.drawText(rect.adjusted(0, 30, 0, 0), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.empty_description)
        painter.end()


class FileTable(EmptyTable):
    def __init__(self, add_files):
        super().__init__(3, "将媒体文件拖到这里", "或点击「添加文件」 · 支持批量导入")
        self.add_files_callback = add_files
        self.setHorizontalHeaderLabels(["文件", "媒体信息", "配对 / 检查结果"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.verticalHeader().hide()
        self.setMinimumHeight(120)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.add_files_callback([url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()])
        event.acceptProposedAction()


class Workbench(QMainWindow):
    def __init__(self, config=None, queue_path=None, start_engine=True, splash=None):
        super().__init__()
        self.config = config or get_config()
        self.probe = ProbeService(self.config, self)
        self.engine = EngineService(self.config, self)
        self.queue = TaskQueue(self.config, self.probe, self.engine, queue_path, self)
        self.records = {}
        self.logs = {}
        self.editing_id = None
        self.loading_streams = False
        self.closing = False
        self.preview_closed = False
        self.process_handler = None  # Legacy forms only use the queue adapter below.
        self.is_ready = True
        self.setWindowTitle("SkyDreamBox · 天梦工具箱")
        self.setWindowIcon(QIcon(resource_path("assets/logo.ico")))
        self.resize(1320, 860)
        self.setMinimumSize(900, 620)
        self._build()
        self._apply_theme()
        self.probe.ready.connect(self._media_ready)
        self.probe.failed.connect(self._media_failed)
        self.engine.updated.connect(self._engine_updated)
        self.queue.changed.connect(self._refresh_queue)
        self.queue.log.connect(self._log)
        self.queue.storage_error.connect(self._notify)
        self.queue.idle.connect(self._idle)
        self._refresh_queue()
        if self.queue.load_error:
            self._notify(self.queue.load_error)
        if start_engine:
            QTimer.singleShot(0, self.engine.refresh)
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.choose_files)
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.enqueue)

    def _apply_theme(self):
        theme = normalize_theme(self.config.get("theme", "light"))
        apply_theme(QApplication.instance(), theme)
        target = "白天" if theme == "dark" else "黑夜"
        self.theme_button.setText(f"切换到{target}模式")
        self.theme_button.setToolTip(f"切换到{target}配色，自动记住选择")
        self.theme_button.setAccessibleName(f"切换到{target}模式")

    def toggle_theme(self):
        theme = normalize_theme(self.config.get("theme", "light"))
        self.config.set("theme", "light" if theme == "dark" else "dark")
        self._apply_theme()
        if not self.config.save():
            self._notify("配色已切换，但保存失败，重启后可能恢复原配色。")

    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(190)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 28, 16, 20)
        logo = QLabel()
        logo.setObjectName("brandLogo")
        logo_pixmap = QPixmap(resource_path("assets/logo.png")).scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        logo_pixmap.setDevicePixelRatio(2)
        logo.setPixmap(logo_pixmap)
        logo.setAccessibleName("SkyDreamBox 应用标志")
        side.addWidget(logo)
        side.addSpacing(8)
        brand = QLabel("SkyDreamBox")
        brand.setObjectName("brand")
        side.addWidget(brand)
        side.addWidget(note("天梦工具箱 · 媒体工作台"))
        side.addSpacing(24)
        section = QLabel("工作空间")
        section.setObjectName("sidebarSection")
        side.addWidget(section)
        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.navigation.setSpacing(3)
        self.navigation.setCursor(Qt.CursorShape.PointingHandCursor)
        self.navigation.addItems([name for _, name, _ in OPERATIONS] + ["高级工具", "设置"])
        self.navigation.item(5).setHidden(True)
        self.navigation.item(6).setHidden(True)
        side.addWidget(self.navigation)
        self.advanced_button = button("高级工具", lambda: self.navigation.setCurrentRow(5))
        self.settings_button = button("设置", lambda: self.navigation.setCurrentRow(6))
        for widget in (self.advanced_button, self.settings_button):
            widget.setCheckable(True)
            side.addWidget(widget)
        self.theme_button = button("", self.toggle_theme)
        self.theme_button.setObjectName("themeToggle")
        side.addWidget(self.theme_button)
        side.addSpacing(16)
        side.addWidget(note("本地处理 · 安心创作\n单个文件 / 批量任务"))
        layout.addWidget(sidebar)
        right = QWidget()
        right.setObjectName("workArea")
        body = QVBoxLayout(right)
        body.setContentsMargins(24, 24, 24, 18)
        body.setSpacing(10)
        header = QHBoxLayout()
        self.title = QLabel()
        self.title.setObjectName("title")
        header.addWidget(self.title)
        header.addStretch()
        self.engine_label = note("正在检测引擎…")
        self.engine_label.setObjectName("engineBadge")
        self.engine_label.setWordWrap(False)
        header.addWidget(self.engine_label)
        body.addLayout(header)
        self.description = note("")
        body.addWidget(self.description)
        self.notification = QLabel()
        self.notification.setWordWrap(True)
        self.notification.setObjectName("notification")
        self.notification.hide()
        body.addWidget(self.notification)
        self.vertical = QSplitter(Qt.Orientation.Vertical)
        self.pages = QStackedWidget()
        workspace = QWidget()
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 8, 0, 0)
        self.horizontal = QSplitter(Qt.Orientation.Horizontal)
        files_panel = QWidget()
        files_panel.setObjectName("card")
        files_layout = QVBoxLayout(files_panel)
        files_layout.setContentsMargins(16, 16, 16, 16)
        files_layout.setSpacing(10)
        files_title = QLabel("素材文件")
        files_title.setObjectName("sectionTitle")
        files_heading = QHBoxLayout()
        files_heading.addWidget(files_title)
        files_heading.addStretch()
        self.count = note("0 个文件")
        self.count.setWordWrap(False)
        files_heading.addWidget(self.count)
        files_layout.addLayout(files_heading)
        actions = QHBoxLayout()
        actions.addWidget(button("＋ 添加文件", self.choose_files))
        actions.addWidget(button("移除", self.remove_files))
        self.scope = VideoFields._choices([("处理全部文件", "all"), ("仅处理选中项", "selected")])
        actions.addWidget(self.scope)
        actions.addStretch()
        files_layout.addLayout(actions)
        files_layout.addWidget(note("导入素材，检查轨道，再统一设置处理参数。"))
        self.file_table = FileTable(self.add_files)
        self.file_table.itemSelectionChanged.connect(self._file_selected)
        files_layout.addWidget(self.file_table, 2)
        pairing = QHBoxLayout()
        self.pair_sub = button("配对字幕…", lambda: self.pair_file("subtitle"))
        self.pair_audio = button("配对音频…", lambda: self.pair_file("external_audio"))
        self.auto_audio = button("同名配对", self.auto_pair_audio)
        self.clear_pair = button("清除配对", self.clear_pairing)
        for widget in (self.pair_sub, self.pair_audio, self.auto_audio, self.clear_pair):
            pairing.addWidget(widget)
        files_layout.addLayout(pairing)
        self.media_label = note("选择文件后显示媒体轨道与时长。")
        files_layout.addWidget(self.media_label)
        self.streams = QListWidget()
        self.streams.setMaximumHeight(115)
        self.streams.itemChanged.connect(self._streams_changed)
        files_layout.addWidget(self.streams)
        self.stream_fields = Fields()
        self.video_stream = self.stream_fields.add("video", "视频轨", VideoFields._choices([]))
        self.audio_stream = self.stream_fields.add("audio", "音频轨", VideoFields._choices([]))
        self.external_stream = self.stream_fields.add("external", "外部音轨", VideoFields._choices([]))
        self.video_stream.currentIndexChanged.connect(self._track_changed)
        self.audio_stream.currentIndexChanged.connect(self._track_changed)
        self.external_stream.currentIndexChanged.connect(self._track_changed)
        files_layout.addWidget(self.stream_fields)
        files_panel.setMinimumHeight(410)
        files_scroll = QScrollArea()
        files_scroll.setWidgetResizable(True)
        files_scroll.setWidget(files_panel)
        self.horizontal.addWidget(files_scroll)
        editor_panel = QWidget()
        editor_panel.setObjectName("card")
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(16, 16, 16, 16)
        editor_layout.setSpacing(10)
        presets = QHBoxLayout()
        parameters_title = QLabel("任务参数")
        parameters_title.setObjectName("sectionTitle")
        presets.addWidget(parameters_title)
        presets.addStretch()
        presets.addWidget(button("保存方案", self.save_preset))
        presets.addWidget(button("加载方案", self.load_preset))
        editor_layout.addLayout(presets)
        self.forms = {}
        self.form_stack = QStackedWidget()
        for operation, _, _ in OPERATIONS:
            form = TaskForm(operation)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(form)
            self.forms[operation] = form
            self.form_stack.addWidget(scroll)
        editor_layout.addWidget(self.form_stack)
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("自动命名到源目录；编辑单项任务时可自定义完整路径")
        editor_layout.addWidget(self.output_edit)
        output_actions = QHBoxLayout()
        output_actions.addWidget(button("输出位置…", self.choose_output))
        self.enqueue_button = button("加入队列", self.enqueue, True)
        output_actions.addWidget(self.enqueue_button, 1)
        self.cancel_edit = button("结束编辑", self.end_edit)
        self.cancel_edit.hide()
        output_actions.addWidget(self.cancel_edit)
        editor_layout.addLayout(output_actions)
        self.horizontal.addWidget(editor_panel)
        self.horizontal.setSizes([400, 560])
        self.horizontal.setChildrenCollapsible(False)
        workspace_layout.addWidget(self.horizontal)
        self.pages.addWidget(workspace)
        self.pages.addWidget(self._advanced())
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setWidget(self._settings())
        self.pages.addWidget(settings_scroll)
        self.vertical.addWidget(self.pages)
        queue_panel = QWidget()
        queue_panel.setObjectName("card")
        queue_layout = QVBoxLayout(queue_panel)
        queue_layout.setContentsMargins(16, 12, 16, 12)
        queue_layout.setSpacing(8)
        row = QHBoxLayout()
        self.queue_label = QLabel("任务队列")
        self.queue_label.setObjectName("sectionTitle")
        row.addWidget(self.queue_label)
        row.addStretch()
        row.addWidget(button("开始队列", self.queue.start, True))
        row.addWidget(button("暂停后续", self.queue.pause))
        row.addWidget(button("停止当前", self.queue.cancel))
        self.show_log = QCheckBox("显示日志")
        row.addWidget(self.show_log)
        queue_layout.addLayout(row)
        self.queue_table = EmptyTable(5, "准备好，即可开始", "设置参数后点击「加入队列」，在这里查看处理进度。")
        self.queue_table.setMinimumHeight(100)
        self.queue_table.setHorizontalHeaderLabels(["任务 / 文件", "状态", "进度", "处理详情", "输出"])
        self.queue_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for column, width in [(1, 76), (2, 60)]:
            self.queue_table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            self.queue_table.setColumnWidth(column, width)
        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.queue_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.queue_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.queue_table.verticalHeader().hide()
        self.queue_table.itemSelectionChanged.connect(self._show_task_log)
        self.queue_table.cellDoubleClicked.connect(lambda *_: self.edit_task())
        queue_layout.addWidget(self.queue_table)
        actions = QHBoxLayout()
        for text, callback in [("编辑", self.edit_task), ("重试", lambda: self.queue.retry(self.selected_task_id())), ("移除", lambda: self.queue.remove(self.selected_task_id())), ("↑", lambda: self.queue.move(self.selected_task_id(), -1)), ("↓", lambda: self.queue.move(self.selected_task_id(), 1)), ("打开输出目录", self.open_output)]:
            actions.addWidget(button(text, callback))
        actions.addStretch()
        self.clear_queue_button = button("清空记录", self.clear_queue)
        self.clear_queue_button.setToolTip("清空所有非运行中的任务（包括待办）及其日志，保留当前任务，不删除输出文件")
        actions.addWidget(self.clear_queue_button)
        queue_layout.addLayout(actions)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.document().setMaximumBlockCount(2000)
        self.log_view.setMaximumHeight(110)
        self.log_view.hide()
        self.show_log.toggled.connect(self.log_view.setVisible)
        queue_layout.addWidget(self.log_view)
        self.vertical.addWidget(queue_panel)
        self.vertical.setSizes([530, 210])
        body.addWidget(self.vertical)
        layout.addWidget(right, 1)
        self.navigation.currentRowChanged.connect(self._page_changed)
        self.navigation.setCurrentRow(0)

    def _advanced(self):
        from ui_tabs import ProfessionalTab, CommonOperationsTab, VideoTab, AudioTab
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(note("保留旧版扩展工具。专业命令直接执行你提供的参数，输出策略由命令决定；所有任务统一进入队列。"))
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(85)
        self.legacy_tabs = QTabWidget()
        for name, constructor in [("专业命令", ProfessionalTab), ("图声合成 / 旧版截取", CommonOperationsTab), ("额外视频格式", VideoTab), ("额外音频格式", AudioTab)]:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(constructor(self))
            self.legacy_tabs.addTab(scroll, name)
        layout.addWidget(self.legacy_tabs)
        layout.addWidget(self.console)
        return panel

    def _settings(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        group = QGroupBox("处理引擎与输出")
        group_layout = QVBoxLayout(group)
        self.settings = Fields()
        self.settings.add("ffmpeg_path", "FFmpeg", QLineEdit(self.config.get_ffmpeg_path()))
        self.settings.add("ffprobe_path", "FFprobe", QLineEdit(self.config.get_ffprobe_path()))
        for key in ("ffmpeg_path", "ffprobe_path"):
            group_layout.addWidget(button(f"选择 {key.split('_')[0]}…", lambda checked=False, k=key: self.browse_engine(k)))
        overwrite = QCheckBox("允许覆盖已有输出（始终禁止覆盖输入）")
        overwrite.setChecked(self.config.get("overwrite_files", False))
        self.settings.add("overwrite_files", "覆盖策略", overwrite)
        group_layout.addWidget(self.settings)
        group_layout.addWidget(button("保存并重新检测", self.save_settings, True))
        layout.addWidget(group)
        self.engine_details = note("")
        layout.addWidget(self.engine_details)
        layout.addWidget(note("配置与队列保存在：" + str(self.config.config_dir) + "\n队列在重新打开后保持暂停，已中断任务可重试。"))
        layout.addWidget(note("SkyDreamBox · 天梦工具箱\n作者 Tensin · GNU GPL v3\nFFmpeg / FFprobe 为外部依赖，预览使用 Qt Multimedia。"))
        layout.addStretch()
        return panel

    @property
    def operation(self):
        return OPERATIONS[min(max(self.navigation.currentRow(), 0), 4)][0]

    def _page_changed(self, row):
        if row < 0:
            return
        self.advanced_button.setChecked(row == 5)
        self.settings_button.setChecked(row == 6)
        for form in self.forms.values():
            if form.preview:
                form.preview.player.pause()
        if row < 5:
            self.pages.setCurrentIndex(0)
            self.form_stack.setCurrentIndex(row)
            self.title.setText(OPERATIONS[row][1])
            self.description.setText(OPERATIONS[row][2])
        else:
            self.pages.setCurrentIndex(row - 4)
            self.title.setText("高级工具" if row == 5 else "设置")
            self.description.setText("更多媒体处理能力" if row == 5 else "配置本地处理引擎与输出行为")
        self.pair_sub.setVisible(row == 2)
        self.pair_audio.setVisible(row == 4)
        self.auto_audio.setVisible(row == 4)
        self.clear_pair.setVisible(row in {2, 4})
        self.streams.setVisible(row == 4)
        self._refresh_files()
        self._file_selected()

    def _notify(self, message):
        self.notification.setText(str(message))
        self.notification.show()

    def choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "添加音视频文件", "", "媒体文件 (*.mp4 *.mkv *.flv *.mov *.avi *.webm *.m4a *.aac *.wav *.flac *.mp3 *.opus *.mka);;所有文件 (*)")
        self.add_files(paths)

    def add_files(self, paths):
        subtitle_indexes = {}
        for path in paths:
            path = str(Path(path).resolve())
            if not Path(path).is_file() or path in self.records:
                continue
            self.records[path] = {"error": "", "subtitle": "", "external_audio": ""}
            parent = Path(path).parent
            if parent not in subtitle_indexes:
                index = {}
                try:
                    for candidate in parent.iterdir():
                        if candidate.suffix.lower() in {".srt", ".ass", ".ssa"} and candidate.is_file():
                            index.setdefault(candidate.stem.casefold(), []).append(candidate)
                except OSError:
                    pass
                subtitle_indexes[parent] = index
            candidates = subtitle_indexes[parent].get(Path(path).stem.casefold(), [])
            if len(candidates) == 1:
                self.records[path]["subtitle"] = str(candidates[0])
            elif len(candidates) > 1:
                self.records[path]["subtitle_error"] = "多个同名字幕，请手动配对"
            self.probe.request(path)
        self._refresh_files()
        if self.file_table.rowCount() and self.file_table.currentRow() < 0:
            self.file_table.selectRow(0)

    def selected_paths(self):
        return [self.file_table.item(i.row(), 0).data(Qt.ItemDataRole.UserRole) for i in self.file_table.selectionModel().selectedRows()]

    def target_paths(self):
        return self.selected_paths() if self.editing_id or self.scope.currentData() == "selected" else list(self.records)

    def current_path(self):
        row = self.file_table.currentRow()
        return self.file_table.item(row, 0).data(Qt.ItemDataRole.UserRole) if row >= 0 else ""

    def remove_files(self):
        for path in self.selected_paths():
            self.records.pop(path, None)
        self._refresh_files()

    def _refresh_files(self):
        selected = set(self.selected_paths())
        self.file_table.blockSignals(True)
        self.file_table.setRowCount(len(self.records))
        for row, (path, record) in enumerate(self.records.items()):
            media = self.probe.cache.get(path)
            summary = f"{media.duration:.1f} 秒 · {len(media.streams)} 条轨道" if media else "正在读取…"
            if self.operation == "subtitle":
                pairing = Path(record["subtitle"]).name if record["subtitle"] else record.get("subtitle_error", "未配对字幕")
            elif self.operation == "mux":
                pairing = Path(record["external_audio"]).name if record["external_audio"] else record.get("audio_error", "仅源文件流")
            else:
                pairing = "HDR · 检查色彩参数" if media and media.hdr else "就绪" if media else "等待探测"
            for column, text in enumerate([Path(path).name, summary, record.get("error") or pairing]):
                item = QTableWidgetItem(text)
                item.setToolTip(path if column == 0 else text)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, path)
                self.file_table.setItem(row, column, item)
            if path in selected:
                for column in range(3):
                    self.file_table.item(row, column).setSelected(True)
        self.file_table.blockSignals(False)
        self.count.setText(f"{len(self.records)} 个文件")

    def _media_ready(self, path, media):
        if path in self.records:
            record = self.records[path]
            record["error"] = ""
            record.setdefault("streams", [s.index for s in media.streams if s.kind in {"video", "audio", "subtitle"}])
            record.setdefault("video_stream", first_index(media, "video"))
            record.setdefault("audio_stream", first_index(media, "audio"))
        self._refresh_files()
        self._file_selected()

    def _media_failed(self, path, error):
        if path in self.records:
            self.records[path]["error"] = error
            self._refresh_files()
        else:
            self._notify(error)

    def _file_selected(self):
        path = self.current_path()
        media = self.probe.cache.get(path)
        self.loading_streams = True
        self.streams.clear()
        for widget in (self.video_stream, self.audio_stream, self.external_stream):
            widget.clear()
        if media and path in self.records:
            record = self.records[path]
            self.media_label.setText(f"{media.duration:.3f} 秒" + (" · HDR：请检查压制色彩参数" if media.hdr else " · 选择需要的媒体轨道"))
            self.audio_stream.addItem("无音频", -1)
            for stream in media.streams:
                text = f"#{stream.index}  {stream.kind} · {stream.codec} · {stream.language}"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, stream.index)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if stream.index in record.get("streams", []) else Qt.CheckState.Unchecked)
                self.streams.addItem(item)
                if stream.kind == "video":
                    self.video_stream.addItem(text, stream.index)
                elif stream.kind == "audio":
                    self.audio_stream.addItem(text, stream.index)
            self.video_stream.setCurrentIndex(self.video_stream.findData(record.get("video_stream")))
            self.audio_stream.setCurrentIndex(self.audio_stream.findData(record.get("audio_stream")))
            external = self.probe.cache.get(record.get("external_audio"))
            if external:
                for stream in external.streams:
                    if stream.kind == "audio":
                        self.external_stream.addItem(f"#{stream.index} {stream.codec} · {stream.language}", stream.index)
                self.external_stream.setCurrentIndex(max(0, self.external_stream.findData(record.get("external_audio_stream"))))
            if self.operation == "trim":
                preview = self.forms["trim"].preview
                if preview.loaded_path != path:
                    preview.load(path)
                    self.forms["trim"].end.setValue(media.duration)
        self.stream_fields.form.setRowVisible(self.external_stream, self.operation == "mux" and self.external_stream.count() > 0)
        self.stream_fields.form.setRowVisible(self.video_stream, self.operation in {"video", "subtitle", "trim"})
        self.stream_fields.form.setRowVisible(self.audio_stream, self.operation != "mux")
        self.loading_streams = False

    def _streams_changed(self):
        if not self.loading_streams and self.current_path() in self.records:
            self.records[self.current_path()]["streams"] = [self.streams.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.streams.count()) if self.streams.item(i).checkState() == Qt.CheckState.Checked]

    def _track_changed(self):
        if not self.loading_streams and self.current_path() in self.records:
            record = self.records[self.current_path()]
            for key, widget in [("video_stream", self.video_stream), ("audio_stream", self.audio_stream), ("external_audio_stream", self.external_stream)]:
                if widget.currentData() is not None:
                    record[key] = widget.currentData()

    def pair_file(self, key):
        path = self.current_path()
        if not path:
            return
        chosen, _ = QFileDialog.getOpenFileName(self, "配对字幕" if key == "subtitle" else "配对外部音频", str(Path(path).parent), "字幕 (*.srt *.ass *.ssa);;所有文件 (*)" if key == "subtitle" else "所有文件 (*)")
        if chosen:
            self.records[path][key] = str(Path(chosen).resolve())
            self.records[path]["error"] = ""
            if key == "external_audio":
                self.records[path].pop("external_audio_stream", None)
                self.probe.request(chosen)
            self._refresh_files()

    def auto_pair_audio(self):
        for path in self.selected_paths() or self.records:
            candidates = [p for p in Path(path).parent.iterdir() if p.stem.casefold() == Path(path).stem.casefold() and p.suffix.lower() in {".aac", ".m4a", ".wav", ".flac", ".mp3", ".mka"} and str(p.resolve()) != path]
            if len(candidates) == 1:
                self.records[path]["external_audio"] = str(candidates[0].resolve())
                self.probe.request(str(candidates[0]))
            else:
                self.records[path]["audio_error"] = "未找到唯一同名音频，请手动配对"
        self._refresh_files()

    def clear_pairing(self):
        for path in self.selected_paths():
            self.records[path]["subtitle" if self.operation == "subtitle" else "external_audio"] = ""
        self._refresh_files()
        self._file_selected()

    def choose_output(self):
        paths = self.target_paths()
        if len(paths) == 1:
            extension = self.forms[self.operation].values()["container"]
            name, _ = QFileDialog.getSaveFileName(self, "输出文件", output_path(paths[0], self.operation, extension), f"输出 (*.{extension})")
        else:
            name = QFileDialog.getExistingDirectory(self, "批量输出目录")
        if name:
            self.output_edit.setText(name)

    def enqueue(self):
        if self.navigation.currentRow() >= 5:
            return
        paths = self.target_paths()
        if not paths:
            self._notify("请先添加文件。")
            return
        if not self.engine.ready:
            self._notify("引擎尚未就绪，请在设置中检查 FFmpeg / FFprobe。")
            return
        if self.editing_id and len(paths) != 1:
            self._notify("编辑任务时请只选中对应的一个源文件。")
            return
        reserved = [path for task in self.queue.tasks if task.id != self.editing_id for path in ([task.output] if task.output else []) + task_outputs(task)]
        protected = {str(Path(path).resolve()).casefold() for task in self.queue.tasks for path in (task.source, task.options.get("subtitle", ""), task.options.get("external_audio", "")) if path}
        protected.update(str(Path(path).resolve()).casefold() for path in self.records)
        protected.update(str(Path(record[key]).resolve()).casefold() for record in self.records.values() for key in ("subtitle", "external_audio") if record.get(key))
        success = 0
        for path in paths:
            try:
                media = self.probe.cache.get(path)
                if not media:
                    raise ValueError("媒体尚未完成探测")
                options = self.forms[self.operation].values()
                record = self.records[path]
                options.update({k: copy.deepcopy(record[k]) for k in ("video_stream", "audio_stream", "streams", "external_audio_stream") if k in record})
                if self.operation == "subtitle":
                    options["subtitle"] = record["subtitle"]
                if self.operation == "mux":
                    options["external_audio"] = record["external_audio"]
                options["overwrite"] = self.config.get("overwrite_files", False)
                codec = options.get("video_codec", "")
                encoding = self.operation == "video" or self.operation == "subtitle" and options.get("subtitle_mode") == "burn" or self.operation == "trim" and options.get("trim_mode") == "encode"
                if encoding and any(k in codec for k in ("nvenc", "qsv", "amf")) and self.engine.hardware.get(codec) is not True:
                    raise ValueError(f"{codec} 尚未通过设备检测，请选择可用编码器")
                output = self.output_edit.text().strip()
                if output and Path(output).is_dir():
                    fake_source = str(Path(output) / Path(path).name)
                    output = allocate_output(fake_source, self.operation, options["container"], options, reserved)
                elif not output:
                    output = allocate_output(path, self.operation, options["container"], options, reserved)
                elif len(paths) > 1:
                    raise ValueError("批量处理请指定输出目录，不要指定单个文件")
                task = TaskSpec(self.operation, path, output, options)
                if self.editing_id:
                    task.id = self.editing_id
                plan = build_plan(task, media, self.probe.cache, self.engine.encoders)
                for _, final in plan.publications:
                    if str(Path(final).resolve()).casefold() in protected:
                        raise ValueError("输出不能覆盖文件列表或队列中的输入文件")
                    if str(Path(final).resolve()).casefold() in {str(Path(p).resolve()).casefold() for p in reserved}:
                        raise ValueError("输出与已有队列任务冲突，请修改名称")
                    if Path(final).exists() and not options["overwrite"]:
                        raise ValueError("输出文件已存在，请修改名称")
                if self.editing_id:
                    self.queue.update(self.editing_id, task)
                else:
                    self.queue.add(task)
                reserved.extend(final for _, final in plan.publications)
                reserved.append(task.output)
                record["error"] = ""
                success += 1
            except (ValueError, OSError, TypeError, KeyError) as error:
                self.records[path]["error"] = str(error)
        self._refresh_files()
        self._notify(f"已{'保存' if self.editing_id else '加入'} {success} 个任务。" + ("其余文件请查看列表中的检查结果。" if success < len(paths) else "可继续添加任务，或开始队列。"))
        if self.editing_id and success:
            self.end_edit()

    def save_preset(self):
        name, ok = QInputDialog.getText(self, "保存个人方案", "方案名称")
        if ok and name.strip():
            presets = copy.deepcopy(self.config.get("presets", {}))
            presets[f"{self.operation}/{name.strip()}"] = self.forms[self.operation].values()
            self.config.set("presets", presets)
            self._notify("方案已保存" if self.config.save() else "方案保存失败")

    def load_preset(self):
        presets = self.config.get("presets", {})
        names = [key for key in presets if key.startswith(self.operation + "/")]
        if not names:
            self._notify("当前功能尚无个人方案。")
            return
        name, ok = QInputDialog.getItem(self, "加载个人方案", "方案", names, 0, False)
        if ok:
            try:
                self.forms[self.operation].restore(presets[name])
            except (TypeError, ValueError, AttributeError) as error:
                self._notify("方案格式无效：" + str(error))

    def selected_task_id(self):
        row = self.queue_table.currentRow()
        return self.queue_table.item(row, 0).data(Qt.ItemDataRole.UserRole) if row >= 0 else ""

    def edit_task(self):
        task = next((t for t in self.queue.tasks if t.id == self.selected_task_id()), None)
        if not task or task is self.queue.current or task.status == TaskStatus.COMPLETED:
            return
        if task.operation in {"raw", "legacy"}:
            original = ["ffmpeg"] + task.options["args"] + ([task.output] if task.operation == "legacy" else [])
            command, ok = QInputDialog.getMultiLineText(self, "编辑高级任务", "FFmpeg 命令（保留 Windows 路径双引号）", subprocess.list2cmdline(original))
            if ok:
                args = QProcess.splitCommand(command)
                if not args or Path(args[0]).name.lower() not in {"ffmpeg", "ffmpeg.exe"}:
                    self._notify("命令必须以 ffmpeg 或 ffmpeg.exe 开头")
                    return
                try:
                    replacement = self._legacy_spec(args, expert=task.operation == "raw")
                    self.queue.update(task.id, replacement)
                except (ValueError, IndexError) as error:
                    self._notify(str(error))
            return
        self.queue.pause()
        self.navigation.setCurrentRow(next(i for i, (op, _, _) in enumerate(OPERATIONS) if op == task.operation))
        self.add_files([task.source])
        self.records[task.source].update(copy.deepcopy(task.options))
        self.forms[task.operation].restore(task.options)
        self.output_edit.setText(task.output)
        self.file_table.clearSelection()
        self.file_table.selectRow(list(self.records).index(task.source))
        self.editing_id = task.id
        self.scope.setEnabled(False)
        self.enqueue_button.setText("保存任务修改")
        self.cancel_edit.show()

    def end_edit(self):
        self.editing_id = None
        self.scope.setEnabled(True)
        self.enqueue_button.setText("加入队列")
        self.cancel_edit.hide()
        self.output_edit.clear()

    def clear_queue(self):
        self.queue.clear()
        retained = {task.id for task in self.queue.tasks}
        self.logs = {task_id: log for task_id, log in self.logs.items() if task_id in retained}
        if self.editing_id and self.editing_id not in retained:
            self.end_edit()
        self._show_task_log()

    def _refresh_queue(self):
        selected = self.selected_task_id()
        self.queue_table.blockSignals(True)
        self.queue_table.setRowCount(len(self.queue.tasks))
        names = {op: name for op, name, _ in OPERATIONS}
        for row, task in enumerate(self.queue.tasks):
            texts = [f"{names.get(task.operation, '高级工具')} · {Path(task.source).name or '自定义命令'}", task.status.value, f"{task.progress}%", task.detail, Path(task.output).name if task.output else "命令指定"]
            for column, text in enumerate(texts):
                item = QTableWidgetItem(text)
                item.setToolTip(task.error if column == 3 and task.error else task.output if column == 4 else text)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, task.id)
                self.queue_table.setItem(row, column, item)
            if task.id == selected:
                self.queue_table.selectRow(row)
        self.queue_table.blockSignals(False)
        completed = sum(t.status == TaskStatus.COMPLETED for t in self.queue.tasks)
        self.clear_queue_button.setEnabled(any(t is not self.queue.current for t in self.queue.tasks))
        self.queue_label.setText(f"任务队列  {completed}/{len(self.queue.tasks)} 完成 · {'后续已暂停' if self.queue.paused else '顺序执行'}")

    def _log(self, task_id, message):
        self.logs[task_id] = (self.logs.get(task_id, "") + message)[-100000:]
        if self.selected_task_id() == task_id:
            self._show_task_log()

    def _show_task_log(self):
        self.log_view.setPlainText(self.logs.get(self.selected_task_id(), ""))

    def open_output(self):
        task = next((t for t in self.queue.tasks if t.id == self.selected_task_id()), None)
        if task and task.output:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(task.output).parent)))

    def browse_engine(self, key):
        path, _ = QFileDialog.getOpenFileName(self, "选择可执行文件", "", "可执行文件 (*.exe);;所有文件 (*)")
        if path:
            self.settings.fields[key].setText(path)

    def save_settings(self):
        if self.queue.current:
            self._notify("请等待当前任务结束或停止任务后修改引擎。")
            return
        for key, value in self.settings.values().items():
            self.config.set(key, value or key.split("_")[0] if key.endswith("_path") else value)
        self._notify("设置已保存" if self.config.save() else "设置保存失败")
        self.engine.refresh()

    def _engine_updated(self):
        self.engine_label.setText(self.engine.message)
        details = [f"{codec}: {'可用' if available else '当前设备不可用'}" for codec, available in self.engine.hardware.items()]
        self.engine_details.setText(self.engine.message + "\n" + "\n".join(details))
        for form in self.forms.values():
            if form.video_fields:
                widget = form.video_fields.codec
                for i in range(widget.count()):
                    codec = widget.itemText(i)
                    state = "设备可用" if self.engine.hardware.get(codec) else "设备未通过检测" if codec in self.engine.hardware else "FFmpeg 已提供" if codec in self.engine.encoders else "未检测到"
                    widget.setItemData(i, state, Qt.ItemDataRole.ToolTipRole)

    # Compatibility adapter: old advanced forms submit to the same queue.
    def enqueue_legacy(self, command):
        from ui_tabs import ProfessionalTab
        expert = isinstance(self.legacy_tabs.currentWidget().widget(), ProfessionalTab)
        task = self.queue.add(self._legacy_spec(command, expert))
        self.console.append("已加入统一队列：" + task.id[:8])

    def _legacy_spec(self, command, expert):
        args = command[1:] if command and Path(command[0]).name.lower() in {"ffmpeg", "ffmpeg.exe"} else command
        if expert:
            return TaskSpec("raw", "", "", {"args": args})
        inputs = [args[i + 1] for i, value in enumerate(args[:-1]) if value == "-i"]
        if not inputs or len(args) < 3:
            raise ValueError("高级工具缺少输入或输出路径")
        output = str(Path(args[-1]).resolve())
        if output.casefold() in {str(Path(p).resolve()).casefold() for p in inputs}:
            raise ValueError("输出不能覆盖输入文件")
        return TaskSpec("legacy", inputs[0], output, {"args": args[:-1], "inputs": inputs, "overwrite": self.config.get("overwrite_files", False)})

    def select_file(self, target):
        path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if path:
            target.setText(path)
            tab = self.legacy_tabs.currentWidget().widget()
            if hasattr(tab, "auto_set_output_path"):
                tab.auto_set_output_path(path)

    def reset_progress_display(self):
        pass

    def switch_to_console_tab(self):
        self.show_log.setChecked(True)

    def set_buttons_enabled(self, enabled):
        pass

    def _idle(self):
        if self.closing:
            QTimer.singleShot(0, self.close)

    def closeEvent(self, event):
        if self.queue.current:
            self.closing = True
            self.queue.pause()
            self.queue.cancel()
            event.ignore()
            return
        self.queue.save()
        if not self.preview_closed:
            self.preview_closed = True
            for form in self.forms.values():
                if form.preview:
                    form.preview.shutdown()
        self.probe.shutdown()
        self.engine.shutdown()
        active = [self.probe.process] + self.engine.processes
        preview_active = any(form.preview and not form.preview.player.source().isEmpty() for form in self.forms.values())
        if preview_active or any(p.state() != QProcess.ProcessState.NotRunning for p in active):
            event.ignore()
            QTimer.singleShot(50, self.close)
            return
        event.accept()
