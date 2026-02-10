# -*- coding: utf-8 -*-
# SkyDreamBox/validators.py
# 输入验证模块

import re
from typing import Optional, Tuple

from constants import CRF_MIN, CRF_MAX, CQ_MIN, CQ_MAX, FPS_MIN
from logger import get_logger

logger = get_logger()


class ValidationError(Exception):
    """验证错误异常"""
    pass


class ValidationResult:
    """验证结果类"""
    def __init__(self, is_valid: bool, message: str = ""):
        self.is_valid = is_valid
        self.message = message
    
    def __bool__(self):
        return self.is_valid
    
    @classmethod
    def success(cls, message: str = "") -> "ValidationResult":
        return cls(True, message)
    
    @classmethod
    def failure(cls, message: str) -> "ValidationResult":
        return cls(False, message)


# 预编译正则表达式以提高性能
_TIME_PATTERN = re.compile(r'^\d{1,2}:\d{2}:\d{2}(\.\d+)?$')
_RESOLUTION_PATTERN = re.compile(r'^\d+:-?\d+$')
_BITRATE_PATTERN = re.compile(r'^\d+[kKmM]?$')


def validate_time_format(time_str: Optional[str]) -> ValidationResult:
    """
    验证时间格式 (HH:MM:SS 或 HH:MM:SS.ms)
    
    Args:
        time_str: 时间字符串
        
    Returns:
        ValidationResult: 验证结果
    """
    if not time_str:
        return ValidationResult.success()
    
    if _TIME_PATTERN.match(time_str):
        return ValidationResult.success()
    
    return ValidationResult.failure(
        f"无效的时间格式 '{time_str}'，应为 HH:MM:SS 或 HH:MM:SS.ms"
    )


def validate_crf(crf_str: Optional[str]) -> ValidationResult:
    """
    验证 CRF (Constant Rate Factor) 值
    
    Args:
        crf_str: CRF 值字符串
        
    Returns:
        ValidationResult: 验证结果
    """
    if not crf_str:
        return ValidationResult.success()
    
    try:
        crf = int(crf_str)
        if CRF_MIN <= crf <= CRF_MAX:
            return ValidationResult.success()
        return ValidationResult.failure(
            f"CRF 值 {crf} 超出范围 [{CRF_MIN}, {CRF_MAX}]"
        )
    except ValueError:
        return ValidationResult.failure(f"CRF 值 '{crf_str}' 不是有效的整数")


def validate_cq(cq_str: Optional[str]) -> ValidationResult:
    """
    验证 CQ (Constant Quality) 值
    
    Args:
        cq_str: CQ 值字符串
        
    Returns:
        ValidationResult: 验证结果
    """
    if not cq_str:
        return ValidationResult.success()
    
    try:
        cq = int(cq_str)
        if CQ_MIN <= cq <= CQ_MAX:
            return ValidationResult.success()
        return ValidationResult.failure(
            f"CQ 值 {cq} 超出范围 [{CQ_MIN}, {CQ_MAX}]"
        )
    except ValueError:
        return ValidationResult.failure(f"CQ 值 '{cq_str}' 不是有效的整数")


def validate_fps(fps_str: Optional[str]) -> ValidationResult:
    """
    验证帧率值
    
    Args:
        fps_str: 帧率字符串
        
    Returns:
        ValidationResult: 验证结果
    """
    if not fps_str:
        return ValidationResult.success()
    
    try:
        fps = float(fps_str)
        if fps > FPS_MIN:
            return ValidationResult.success()
        return ValidationResult.failure(f"帧率必须大于 {FPS_MIN}")
    except ValueError:
        return ValidationResult.failure(f"帧率 '{fps_str}' 不是有效的数字")


def validate_resolution(res_str: Optional[str]) -> ValidationResult:
    """
    验证分辨率格式 (宽度:高度)
    
    Args:
        res_str: 分辨率字符串
        
    Returns:
        ValidationResult: 验证结果
    """
    if not res_str:
        return ValidationResult.success()
    
    if _RESOLUTION_PATTERN.match(res_str):
        return ValidationResult.success()
    
    return ValidationResult.failure(
        f"无效的分辨率格式 '{res_str}'，应为 宽度:高度 (如 1920:1080)"
    )


def validate_bitrate(br_str: Optional[str]) -> ValidationResult:
    """
    验证比特率格式
    
    Args:
        br_str: 比特率字符串
        
    Returns:
        ValidationResult: 验证结果
    """
    if not br_str:
        return ValidationResult.success()
    
    if _BITRATE_PATTERN.match(br_str):
        return ValidationResult.success()
    
    return ValidationResult.failure(
        f"无效的比特率格式 '{br_str}'，应为数字加可选单位 (如 192k, 1M)"
    )


def validate_file_path(file_path: Optional[str], must_exist: bool = True) -> ValidationResult:
    """
    验证文件路径
    
    Args:
        file_path: 文件路径
        must_exist: 是否要求文件必须存在
        
    Returns:
        ValidationResult: 验证结果
    """
    import os
    
    if not file_path:
        return ValidationResult.failure("文件路径不能为空")
    
    if '\x00' in file_path:
        return ValidationResult.failure("路径包含非法空字符")
    
    if must_exist and not os.path.exists(file_path):
        return ValidationResult.failure(f"文件不存在: {file_path}")
    
    if must_exist and not os.path.isfile(file_path):
        return ValidationResult.failure(f"路径不是文件: {file_path}")
    
    return ValidationResult.success()


def validate_output_path(file_path: Optional[str]) -> ValidationResult:
    """
    验证输出文件路径
    
    Args:
        file_path: 输出文件路径
        
    Returns:
        ValidationResult: 验证结果
    """
    if not file_path:
        return ValidationResult.failure("输出文件路径不能为空")
    
    if '\x00' in file_path:
        return ValidationResult.failure("路径包含非法空字符")
    
    # 检查目录是否可写
    import os
    dir_path = os.path.dirname(file_path) or "."
    if os.path.exists(dir_path) and not os.path.isdir(dir_path):
        return ValidationResult.failure(f"输出目录无效: {dir_path}")
    
    return ValidationResult.success()


# 便捷函数：直接返回布尔值
def is_valid_time(time_str: Optional[str]) -> bool:
    """检查时间格式是否有效"""
    return bool(validate_time_format(time_str))


def is_valid_crf(crf_str: Optional[str]) -> bool:
    """检查 CRF 值是否有效"""
    return bool(validate_crf(crf_str))


def is_valid_cq(cq_str: Optional[str]) -> bool:
    """检查 CQ 值是否有效"""
    return bool(validate_cq(cq_str))


def is_valid_fps(fps_str: Optional[str]) -> bool:
    """检查帧率是否有效"""
    return bool(validate_fps(fps_str))


def is_valid_resolution(res_str: Optional[str]) -> bool:
    """检查分辨率格式是否有效"""
    return bool(validate_resolution(res_str))


def is_valid_bitrate(br_str: Optional[str]) -> bool:
    """检查比特率格式是否有效"""
    return bool(validate_bitrate(br_str))
