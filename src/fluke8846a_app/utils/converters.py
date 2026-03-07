"""
数据转换工具
"""

import re
from typing import Union, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP


def convert_units(value: float, from_unit: str, to_unit: str) -> Optional[float]:
    """
    转换单位

    Args:
        value: 原始值
        from_unit: 原始单位
        to_unit: 目标单位

    Returns:
        转换后的值，如果转换失败返回None
    """
    # 电压单位转换
    voltage_conversions = {
        ('V', 'mV'): lambda x: x * 1000,
        ('V', 'kV'): lambda x: x / 1000,
        ('mV', 'V'): lambda x: x / 1000,
        ('mV', 'kV'): lambda x: x / 1e6,
        ('kV', 'V'): lambda x: x * 1000,
        ('kV', 'mV'): lambda x: x * 1e6,
    }

    # 电流单位转换
    current_conversions = {
        ('A', 'mA'): lambda x: x * 1000,
        ('A', 'uA'): lambda x: x * 1e6,
        ('A', 'nA'): lambda x: x * 1e9,
        ('mA', 'A'): lambda x: x / 1000,
        ('mA', 'uA'): lambda x: x * 1000,
        ('mA', 'nA'): lambda x: x * 1e6,
        ('uA', 'A'): lambda x: x / 1e6,
        ('uA', 'mA'): lambda x: x / 1000,
        ('uA', 'nA'): lambda x: x * 1000,
        ('nA', 'A'): lambda x: x / 1e9,
        ('nA', 'mA'): lambda x: x / 1e6,
        ('nA', 'uA'): lambda x: x / 1000,
    }

    # 电阻单位转换
    resistance_conversions = {
        ('Ω', 'kΩ'): lambda x: x / 1000,
        ('Ω', 'MΩ'): lambda x: x / 1e6,
        ('kΩ', 'Ω'): lambda x: x * 1000,
        ('kΩ', 'MΩ'): lambda x: x / 1000,
        ('MΩ', 'Ω'): lambda x: x * 1e6,
        ('MΩ', 'kΩ'): lambda x: x * 1000,
    }

    # 频率单位转换
    frequency_conversions = {
        ('Hz', 'kHz'): lambda x: x / 1000,
        ('Hz', 'MHz'): lambda x: x / 1e6,
        ('Hz', 'GHz'): lambda x: x / 1e9,
        ('kHz', 'Hz'): lambda x: x * 1000,
        ('kHz', 'MHz'): lambda x: x / 1000,
        ('kHz', 'GHz'): lambda x: x / 1e6,
        ('MHz', 'Hz'): lambda x: x * 1e6,
        ('MHz', 'kHz'): lambda x: x * 1000,
        ('MHz', 'GHz'): lambda x: x / 1000,
        ('GHz', 'Hz'): lambda x: x * 1e9,
        ('GHz', 'kHz'): lambda x: x * 1e6,
        ('GHz', 'MHz'): lambda x: x * 1000,
    }

    # 合并所有转换表
    conversions = {}
    conversions.update(voltage_conversions)
    conversions.update(current_conversions)
    conversions.update(resistance_conversions)
    conversions.update(frequency_conversions)

    # 相同单位不需要转换
    if from_unit == to_unit:
        return value

    # 查找转换函数
    conversion_key = (from_unit, to_unit)
    if conversion_key in conversions:
        return conversions[conversion_key](value)

    # 尝试通过中间单位转换
    # 这里可以添加更复杂的转换逻辑
    return None


def format_value(
    value: float,
    precision: int = 6,
    scientific_notation: bool = False,
    unit: str = "",
    include_unit: bool = True
) -> str:
    """
    格式化数值显示

    Args:
        value: 数值
        precision: 精度（小数位数）
        scientific_notation: 是否使用科学计数法
        unit: 单位
        include_unit: 是否包含单位

    Returns:
        格式化后的字符串
    """
    if value == 0:
        formatted = "0"
        if precision > 0:
            formatted += "." + "0" * precision
    elif scientific_notation or abs(value) >= 1e6 or (abs(value) < 1e-3 and value != 0):
        # 使用科学计数法
        formatted = f"{value:.{precision}e}"
    else:
        # 使用常规小数表示
        formatted = f"{value:.{precision}f}".rstrip('0').rstrip('.')

    if include_unit and unit:
        formatted += f" {unit}"

    return formatted


def parse_measurement(measurement_str: str) -> Tuple[Optional[float], Optional[str]]:
    """
    解析测量字符串

    Args:
        measurement_str: 测量字符串，如 "3.1415 V" 或 "1.23e-3 A"

    Returns:
        (数值, 单位) 或 (None, None)
    """
    if not measurement_str:
        return None, None

    # 移除多余空格
    measurement_str = measurement_str.strip()

    # 匹配数值和单位
    pattern = r'^([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)\s*([a-zA-ZΩμµ°]+)?$'
    match = re.match(pattern, measurement_str)

    if not match:
        return None, None

    value_str, unit = match.groups()

    try:
        value = float(value_str)
        return value, unit
    except ValueError:
        return None, None


def si_prefix(value: float) -> Tuple[float, str]:
    """
    根据值的大小选择合适的SI前缀

    Args:
        value: 原始值

    Returns:
        (缩放后的值, 前缀)
    """
    prefixes = [
        (1e12, 'T'),
        (1e9, 'G'),
        (1e6, 'M'),
        (1e3, 'k'),
        (1, ''),
        (1e-3, 'm'),
        (1e-6, 'μ'),
        (1e-9, 'n'),
        (1e-12, 'p'),
        (1e-15, 'f'),
    ]

    abs_value = abs(value)

    for factor, prefix in prefixes:
        if abs_value >= factor:
            return value / factor, prefix

    # 如果值太小，返回最小的前缀
    return value / prefixes[-1][0], prefixes[-1][1]


def round_to_significant(value: float, significant_digits: int) -> float:
    """
    四舍五入到指定有效数字

    Args:
        value: 原始值
        significant_digits: 有效数字位数

    Returns:
        四舍五入后的值
    """
    if value == 0:
        return 0.0

    # 计算数量级
    magnitude = 10 ** (significant_digits - 1 - int(Decimal(str(abs(value))).log10()))

    # 四舍五入
    rounded = round(value * magnitude) / magnitude

    return float(rounded)


def db_to_linear(db_value: float) -> float:
    """
    分贝值转换为线性值

    Args:
        db_value: 分贝值

    Returns:
        线性值
    """
    return 10 ** (db_value / 20)


def linear_to_db(linear_value: float) -> float:
    """
    线性值转换为分贝值

    Args:
        linear_value: 线性值

    Returns:
        分贝值
    """
    if linear_value <= 0:
        return -float('inf')
    return 20 * math.log10(linear_value)


# 导入math模块用于对数计算
import math