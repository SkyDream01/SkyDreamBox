# -*- coding: utf-8 -*-
# SkyDreamBox/constants.py
# 应用常量定义

# =============================================================================
# 应用信息
# =============================================================================
APP_NAME = "SkyDreamBox - 天梦工具箱"
APP_VERSION = "2.3.0"
AUTHOR = "Tensin"
GITHUB_URL = "https://github.com/SkyDream01/SkyDreamBox"

# =============================================================================
# FFmpeg 相关常量
# =============================================================================
DEFAULT_FFMPEG_PATH = "ffmpeg"
DEFAULT_FFPROBE_PATH = "ffprobe"
FFMPEG_TIMEOUT_MS = 5000  # FFmpeg 检查超时时间（毫秒）
FFPROBE_TIMEOUT_MS = 5000  # FFprobe 检查超时时间（毫秒）
PROCESS_TERMINATE_TIMEOUT_MS = 3000  # 进程终止等待超时（毫秒）
PROCESS_KILL_TIMEOUT_MS = 1000  # 进程强制结束等待超时（毫秒）

# =============================================================================
# 默认配置值
# =============================================================================
DEFAULT_OVERWRITE_FILES = True
DEFAULT_AUDIO_BITRATE = "192k"
DEFAULT_COMPRESSION_LEVEL = "5"
DEFAULT_SAMPLE_RATE = "(默认)"

# =============================================================================
# 验证相关常量
# =============================================================================
CRF_MIN = 0
CRF_MAX = 51
CQ_MIN = 0
CQ_MAX = 51
FPS_MIN = 0.1

# =============================================================================
# UI 相关常量
# =============================================================================
WINDOW_MIN_WIDTH = 750
WINDOW_MIN_HEIGHT = 850
SPLASH_WIDTH = 450
SPLASH_HEIGHT = 350
PROGRESS_BAR_MAX = 100
MAX_CONSOLE_LINES = 2000
SPLASH_FINISH_DELAY_SEC = 0.3
WINDOW_POSITION_X = 50
WINDOW_POSITION_Y = 50

# =============================================================================
# 文件过滤器
# =============================================================================
FILE_FILTER_ALL = "All Files (*)"
FILE_FILTER_EXECUTABLE = "Executable Files (*.exe)"
FILE_FILTER_IMAGE = "Image Files (*.png *.jpg *.jpeg *.bmp)"
FILE_FILTER_MEDIA = "Media Files (*.mp4 *.mkv)"

VIDEO_FORMAT_CODECS = {
    "mp4": ["libx264", "h264_nvenc", "h264_amf", "h264_qsv", "libx265", "hevc_nvenc", "hevc_amf", "hevc_qsv", "libaom-av1", "copy"],
    "mkv": ["libx264", "h264_nvenc", "h264_amf", "h264_qsv", "libx265", "hevc_nvenc", "hevc_amf", "hevc_qsv", "vp9", "libaom-av1", "copy"],
    "avi": ["libx264", "mpeg4"],
    "mov": ["libx264", "h264_nvenc", "h264_amf", "h264_qsv", "libx265", "hevc_nvenc", "hevc_amf", "hevc_qsv", "copy"],
    "webm": ["vp9", "libvpx-vp9", "libaom-av1", "copy"]
}
AUDIO_CODECS_FOR_VIDEO_FORMAT = {
    "mp4": ["aac", "mp3", "alac", "copy"],
    "mkv": ["aac", "mp3", "flac", "opus", "copy"],
    "avi": ["mp3", "aac"],
    "mov": ["aac", "mp3", "alac", "copy"],
    "webm": ["opus", "vorbis", "copy"]
}

AUDIO_FORMAT_CODECS = {
    "mp3": ["libmp3lame"],
    "flac": ["flac"],
    "aac": ["aac"],
    "wav": ["pcm"],
    "opus": ["libopus"],
    "alac": ["alac"],
    "m4a": ["aac", "alac", "copy"]
}

WAV_BIT_DEPTH_CODECS = {
    "16-bit (默认)": "pcm_s16le",
    "24-bit": "pcm_s24le",
    "32-bit": "pcm_s32le",
    "8-bit": "pcm_u8"
}

AUDIO_SAMPLE_FORMATS = {
    "(默认)": None,
    "16-bit": "s16",
    "24-bit": "s32",
    "32-bit (float)": "fltp"
}

VIDEO_FORMATS = list(VIDEO_FORMAT_CODECS.keys())
AUDIO_FORMATS = list(AUDIO_FORMAT_CODECS.keys())
AUDIO_BITRATES = ["128k", "192k", "256k", "320k"]
AUDIO_SAMPLE_RATES = ["(默认)", "24000", "44100", "48000", "96000", "192000"]
SUBTITLE_FORMATS = "字幕文件 (*.srt *.ass *.ssa);;所有文件 (*)"
DEFAULT_COMPRESSION_LEVEL = "5"

RESOLUTION_PRESETS = {
    "720p": 1280,
    "1080p": 1920,
    "2k": 2560,
    "4k": 3840
}
