"""
数据验证工具
"""

import re
from typing import Union, Optional, Tuple
from ipaddress import ip_address, IPv4Address, IPv6Address


def validate_ip_address(ip_str: str) -> Tuple[bool, Optional[Union[IPv4Address, IPv6Address]]]:
    """
    验证IP地址

    Args:
        ip_str: IP地址字符串

    Returns:
        (是否有效, IP地址对象或None)
    """
    try:
        ip = ip_address(ip_str)
        return True, ip
    except ValueError:
        return False, None


def validate_port(port: Union[str, int]) -> bool:
    """
    验证端口号

    Args:
        port: 端口号

    Returns:
        是否有效
    """
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False


def validate_float(value: str, min_val: Optional[float] = None, max_val: Optional[float] = None) -> bool:
    """
    验证浮点数

    Args:
        value: 浮点数字符串
        min_val: 最小值
        max_val: 最大值

    Returns:
        是否有效
    """
    try:
        num = float(value)
        if min_val is not None and num < min_val:
            return False
        if max_val is not None and num > max_val:
            return False
        return True
    except (ValueError, TypeError):
        return False


def validate_int(value: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> bool:
    """
    验证整数

    Args:
        value: 整数字符串
        min_val: 最小值
        max_val: 最大值

    Returns:
        是否有效
    """
    try:
        num = int(value)
        if min_val is not None and num < min_val:
            return False
        if max_val is not None and num > max_val:
            return False
        return True
    except (ValueError, TypeError):
        return False


def validate_gpib_address(address: Union[str, int]) -> bool:
    """
    验证GPIB地址

    Args:
        address: GPIB地址

    Returns:
        是否有效
    """
    try:
        addr = int(address)
        return 0 <= addr <= 30  # GPIB地址范围通常是0-30
    except (ValueError, TypeError):
        return False


def validate_serial_port(port: str) -> bool:
    """
    验证串口名称

    Args:
        port: 串口名称

    Returns:
        是否有效
    """
    # Windows: COM1-COM256
    # Linux: /dev/ttyS0, /dev/ttyUSB0等
    pattern = r'^(COM[1-9][0-9]?[0-9]?$|/dev/tty[A-Za-z0-9]+$)'
    return bool(re.match(pattern, port))


def validate_baudrate(baudrate: Union[str, int]) -> bool:
    """
    验证波特率

    Args:
        baudrate: 波特率

    Returns:
        是否有效
    """
    valid_baudrates = {
        110, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200,
        38400, 57600, 115200, 128000, 256000
    }

    try:
        rate = int(baudrate)
        return rate in valid_baudrates
    except (ValueError, TypeError):
        return False


def validate_measurement_range(range_val: str, function: str) -> bool:
    """
    验证测量范围

    Args:
        range_val: 范围值
        function: 测量功能

    Returns:
        是否有效
    """
    from ..config.constants import (
        RANGE_AUTO, RANGE_100mV, RANGE_1V, RANGE_10V, RANGE_100V, RANGE_1000V,
        MEASUREMENT_DCV, MEASUREMENT_ACV
    )

    valid_ranges = {
        MEASUREMENT_DCV: [RANGE_AUTO, RANGE_100mV, RANGE_1V, RANGE_10V, RANGE_100V, RANGE_1000V],
        MEASUREMENT_ACV: [RANGE_AUTO, RANGE_100mV, RANGE_1V, RANGE_10V, RANGE_100V, RANGE_1000V],
        # 其他功能的范围验证...
    }

    if function not in valid_ranges:
        return True  # 如果功能没有定义范围，则视为有效

    return range_val in valid_ranges[function]


def validate_resolution(resolution: str) -> bool:
    """
    验证分辨率

    Args:
        resolution: 分辨率字符串

    Returns:
        是否有效
    """
    from ..config.constants import RESOLUTIONS
    return resolution in RESOLUTIONS


def validate_hex_string(hex_str: str, prefix: bool = True) -> bool:
    """
    验证十六进制字符串

    Args:
        hex_str: 十六进制字符串
        prefix: 是否包含0x前缀

    Returns:
        是否有效
    """
    pattern = r'^0x[0-9A-Fa-f]+$' if prefix else r'^[0-9A-Fa-f]+$'
    return bool(re.match(pattern, hex_str))


def validate_filename(filename: str, allowed_extensions: Optional[list] = None) -> bool:
    """
    验证文件名

    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名列表

    Returns:
        是否有效
    """
    # 基本文件名验证
    if not filename or len(filename) > 255:
        return False

    # 检查非法字符
    illegal_chars = r'[<>:"/\\|?*\x00-\x1F]'
    if re.search(illegal_chars, filename):
        return False

    # 检查扩展名
    if allowed_extensions:
        ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        if ext and ext not in allowed_extensions:
            return False

    return True