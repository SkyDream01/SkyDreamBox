# -*- coding: utf-8 -*-
# SkyDreamBox/logger.py
# 日志管理模块

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "SkyDreamBox", level: int = logging.INFO) -> logging.Logger:
    """
    设置并返回配置好的日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    return logger


def get_logger() -> logging.Logger:
    """获取默认日志记录器"""
    return logging.getLogger("SkyDreamBox")
