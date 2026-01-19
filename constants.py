# -*- coding: utf-8 -*-
# SkyDreamBox/constants.py

APP_NAME = "SkyDreamBox - 天梦工具箱"
APP_VERSION = "2.3.0"
AUTHOR = "Tensin"
GITHUB_URL = "https://github.com/SkyDream01/SkyDreamBox"

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
