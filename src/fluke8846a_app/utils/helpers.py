"""
辅助函数工具
"""

import os
import sys
import platform
import hashlib
import json
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from contextlib import contextmanager
import tempfile


def ensure_directory(directory: Union[str, Path]) -> Path:
    """
    确保目录存在，如果不存在则创建

    Args:
        directory: 目录路径

    Returns:
        目录路径对象
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_filename(
    prefix: str = "measurement",
    suffix: str = "",
    extension: str = ".csv",
    timestamp: bool = True,
    date_format: str = "%Y%m%d_%H%M%S"
) -> str:
    """
    生成文件名

    Args:
        prefix: 文件名前缀
        suffix: 文件名后缀
        extension: 文件扩展名
        timestamp: 是否包含时间戳
        date_format: 时间戳格式

    Returns:
        生成的文件名
    """
    parts = [prefix]

    if timestamp:
        timestamp_str = datetime.now().strftime(date_format)
        parts.append(timestamp_str)

    if suffix:
        parts.append(suffix)

    # 移除扩展名中的点（如果存在）
    if extension.startswith('.'):
        extension = extension[1:]

    filename = "_".join(parts)
    if extension:
        filename += f".{extension}"

    return filename


def format_timestamp(
    dt: Optional[datetime] = None,
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    格式化时间戳

    Args:
        dt: 日期时间对象，如果为None则使用当前时间
        format_str: 格式字符串

    Returns:
        格式化后的时间字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)


def get_system_info() -> Dict[str, str]:
    """
    获取系统信息

    Returns:
        系统信息字典
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }


def calculate_file_hash(filepath: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    计算文件哈希值

    Args:
        filepath: 文件路径
        algorithm: 哈希算法（sha256, md5等）

    Returns:
        哈希值字符串
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")

    hash_func = hashlib.new(algorithm)

    with open(filepath, 'rb') as f:
        # 分块读取大文件
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def safe_json_dump(data: Any, filepath: Union[str, Path], **kwargs) -> bool:
    """
    安全地保存JSON数据

    Args:
        data: 要保存的数据
        filepath: 文件路径
        **kwargs: 传递给json.dump的其他参数

    Returns:
        是否成功
    """
    try:
        filepath = Path(filepath)
        ensure_directory(filepath.parent)

        # 使用临时文件避免写入过程中出错导致原文件损坏
        temp_file = filepath.with_suffix(filepath.suffix + '.tmp')

        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, **kwargs)

        # 写入成功，重命名临时文件
        temp_file.rename(filepath)
        return True

    except Exception as e:
        # 清理临时文件
        if 'temp_file' in locals() and temp_file.exists():
            try:
                temp_file.unlink()
            except:
                pass
        print(f"保存JSON文件失败: {e}")
        return False


def safe_csv_write(
    data: List[Dict[str, Any]],
    filepath: Union[str, Path],
    fieldnames: Optional[List[str]] = None
) -> bool:
    """
    安全地保存CSV数据

    Args:
        data: 要保存的数据列表
        filepath: 文件路径
        fieldnames: 字段名列表

    Returns:
        是否成功
    """
    try:
        filepath = Path(filepath)
        ensure_directory(filepath.parent)

        if not data:
            return False

        # 如果未提供字段名，使用第一条数据的键
        if fieldnames is None:
            fieldnames = list(data[0].keys())

        # 使用临时文件
        temp_file = filepath.with_suffix(filepath.suffix + '.tmp')

        with open(temp_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        # 写入成功，重命名临时文件
        temp_file.rename(filepath)
        return True

    except Exception as e:
        # 清理临时文件
        if 'temp_file' in locals() and temp_file.exists():
            try:
                temp_file.unlink()
            except:
                pass
        print(f"保存CSV文件失败: {e}")
        return False


@contextmanager
def temporary_file(suffix: str = ".tmp", delete: bool = True):
    """
    创建临时文件的上下文管理器

    Args:
        suffix: 文件后缀
        delete: 是否在退出时删除

    Yields:
        临时文件路径
    """
    temp_file = None
    try:
        # 创建临时文件
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(temp_fd)
        temp_file = Path(temp_path)

        yield temp_file

    finally:
        # 清理临时文件
        if delete and temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except:
                pass


def human_readable_size(size_bytes: int) -> str:
    """
    将字节大小转换为人类可读的格式

    Args:
        size_bytes: 字节大小

    Returns:
        人类可读的字符串
    """
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1

    return f"{size:.2f} {units[i]}"


def is_valid_email(email: str) -> bool:
    """
    验证邮箱地址格式

    Args:
        email: 邮箱地址

    Returns:
        是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def normalize_path(path: Union[str, Path]) -> Path:
    """
    规范化路径

    Args:
        path: 路径

    Returns:
        规范化后的Path对象
    """
    path = Path(path)
    # 解析相对路径和符号链接
    try:
        return path.resolve()
    except:
        return path.absolute()


# 导入re模块用于正则表达式
import re