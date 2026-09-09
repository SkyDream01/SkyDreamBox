# -*- coding: utf-8 -*-
# SkyDreamBox/config.py
# 配置管理模块

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

from constants import DEFAULT_FFMPEG_PATH, DEFAULT_FFPROBE_PATH, DEFAULT_OVERWRITE_FILES
from logger import get_logger

logger = get_logger()


class Config:
    """配置管理类"""

    def __init__(self, config_dir=None):
        self._config = {}
        self.config_dir = Path(config_dir) if config_dir is not None else self._get_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self._load_defaults()
        self.load()

    def _get_config_dir(self):
        """获取配置目录"""
        if getattr(sys, "frozen", False):  # 打包后的应用
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent

        # 首先尝试应用目录。
        app_config_dir = base_dir / "config"
        try:
            app_config_dir.mkdir(exist_ok=True)
            # An existing directory can still be read-only (e.g. Program Files).
            with tempfile.TemporaryFile(dir=app_config_dir):
                pass
            return app_config_dir
        except OSError as error:
            # 安装目录（例如 Program Files）通常不可写，回退到当前用户目录。
            user_config_dir = (
                Path(os.environ.get("APPDATA", Path.home())) / "SkyDreamBox"
            )
            user_config_dir.mkdir(parents=True, exist_ok=True)
            logger.warning(
                "应用目录不可写，配置将保存到用户目录: %s (%s)",
                user_config_dir,
                error,
            )
            return user_config_dir

    def _load_defaults(self) -> None:
        """加载默认配置"""
        self._config: Dict[str, Any] = {
            "ffmpeg_path": DEFAULT_FFMPEG_PATH,
            "ffprobe_path": DEFAULT_FFPROBE_PATH,
            "overwrite_files": DEFAULT_OVERWRITE_FILES,
            "config_version": 2,
            "presets": {},
        }

    def load(self) -> bool:
        """从配置文件加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    if not isinstance(loaded_config, dict):
                        logger.error("配置文件根节点必须是对象，已使用默认配置")
                        return False
                    for key, value in loaded_config.items():
                        if key in self._config:
                            expected_type = type(self._config[key])
                            if isinstance(value, expected_type):
                                self._config[key] = value
                            else:
                                logger.warning(f"配置项 '{key}' 类型不匹配，使用默认值")
                logger.info(f"配置文件已加载: {self.config_file}")
                self._config["config_version"] = 2
                return True
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
        except IOError as e:
            logger.error(f"加载配置文件失败: {e}")
        return False

    def save(self) -> bool:
        """原子地保存配置到文件，避免中断写入损坏原配置。"""
        temporary_file = self.config_file.with_suffix(".json.tmp")
        try:
            with open(temporary_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            os.replace(temporary_file, self.config_file)
            logger.info(f"配置文件已保存: {self.config_file}")
            return True
        except OSError as e:
            logger.error(f"保存配置文件失败: {e}")
            try:
                temporary_file.unlink(missing_ok=True)
            except OSError:
                pass
        return False

    def get(self, key, default=None):
        """获取配置值"""
        return self._config.get(key, default)

    def set(self, key, value):
        """设置配置值"""
        if key not in self._config:
            raise KeyError(f"未知配置项: {key}")
        expected_type = type(self._config[key])
        if not isinstance(value, expected_type):
            raise TypeError(
                f"配置项 '{key}' 类型错误: 期望 {expected_type.__name__}, 实际 {type(value).__name__}"
            )
        self._config[key] = value

    def get_ffmpeg_path(self) -> str:
        """获取FFmpeg路径（支持自定义路径）"""
        path = self.get("ffmpeg_path", DEFAULT_FFMPEG_PATH)
        # 如果路径为空或为默认值，返回默认命令
        if not path or path == DEFAULT_FFMPEG_PATH:
            return DEFAULT_FFMPEG_PATH
        # 确保路径是字符串
        return str(path)

    def get_ffprobe_path(self) -> str:
        """获取FFprobe路径（支持自定义路径）"""
        path = self.get("ffprobe_path", DEFAULT_FFPROBE_PATH)
        if not path or path == DEFAULT_FFPROBE_PATH:
            return DEFAULT_FFPROBE_PATH
        return str(path)

    def validate_ffmpeg_path(self, path):
        """验证FFmpeg路径是否有效"""
        if not path or path == "ffmpeg":
            # 使用系统PATH
            return self._check_system_ffmpeg("ffmpeg")

        # 检查自定义路径
        if isinstance(path, str):
            path_obj = Path(path)
            if path_obj.exists() and path_obj.is_file():
                # 检查是否可执行（简化的检查）
                return self._check_executable(path)

        return False

    def validate_ffprobe_path(self, path):
        """验证FFprobe路径是否有效"""
        if not path or path == "ffprobe":
            return self._check_system_ffmpeg("ffprobe")

        if isinstance(path, str):
            path_obj = Path(path)
            if path_obj.exists() and path_obj.is_file():
                return self._check_executable(path)

        return False

    def _check_system_ffmpeg(self, command):
        """检查系统PATH中的FFmpeg/FFprobe"""
        import subprocess

        try:
            result = subprocess.run(
                [command, "-version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _check_executable(self, path):
        """检查可执行文件是否有效"""
        import subprocess

        try:
            result = subprocess.run(
                [str(path), "-version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    @property
    def ffmpeg_path(self):
        return self.get_ffmpeg_path()

    @ffmpeg_path.setter
    def ffmpeg_path(self, value):
        self.set("ffmpeg_path", value)

    @property
    def ffprobe_path(self):
        return self.get_ffprobe_path()

    @ffprobe_path.setter
    def ffprobe_path(self, value):
        self.set("ffprobe_path", value)


# 全局配置实例
_config_instance = None


def get_config():
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def init_config():
    """初始化配置（供主程序调用）"""
    return get_config()
