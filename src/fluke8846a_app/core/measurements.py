"""
测量功能模块

提供测量相关的辅助函数和数据处理。
"""

import statistics
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .instrument import MeasurementData
from ..config.constants import *
from ..utils.converters import format_value, convert_units


@dataclass
class Statistics:
    """测量统计信息"""
    count: int
    mean: float
    std_dev: float
    min: float
    max: float
    range: float
    unit: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "count": self.count,
            "mean": self.mean,
            "std_dev": self.std_dev,
            "min": self.min,
            "max": self.max,
            "range": self.range,
            "unit": self.unit,
        }

    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"统计: {self.count}次测量, "
            f"平均值: {format_value(self.mean)} {self.unit}, "
            f"标准差: {format_value(self.std_dev)} {self.unit}, "
            f"范围: {format_value(self.min)} - {format_value(self.max)} {self.unit}"
        )


class MeasurementAnalyzer:
    """测量数据分析器"""

    def __init__(self, measurements: List[MeasurementData]):
        """
        初始化分析器

        Args:
            measurements: 测量数据列表
        """
        self.measurements = measurements

    def calculate_statistics(self, function: Optional[str] = None) -> Optional[Statistics]:
        """
        计算统计信息

        Args:
            function: 过滤特定测量功能

        Returns:
            统计信息，如果无数据返回None
        """
        # 过滤数据
        filtered = self.measurements
        if function:
            filtered = [m for m in self.measurements if m.function == function]

        if not filtered:
            return None

        # 提取数值
        values = [m.value for m in filtered]
        unit = filtered[0].unit if filtered else ""

        # 计算统计量
        try:
            mean = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            min_val = min(values)
            max_val = max(values)
            range_val = max_val - min_val

            return Statistics(
                count=len(values),
                mean=mean,
                std_dev=std_dev,
                min=min_val,
                max=max_val,
                range=range_val,
                unit=unit,
            )
        except statistics.StatisticsError:
            return None

    def filter_by_time(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[MeasurementData]:
        """
        按时间过滤测量数据

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            过滤后的测量数据列表
        """
        filtered = self.measurements

        if start_time:
            filtered = [m for m in filtered if m.timestamp >= start_time]

        if end_time:
            filtered = [m for m in filtered if m.timestamp <= end_time]

        return filtered

    def filter_by_function(self, function: str) -> List[MeasurementData]:
        """
        按测量功能过滤

        Args:
            function: 测量功能

        Returns:
            过滤后的测量数据列表
        """
        return [m for m in self.measurements if m.function == function]

    def get_latest(self, count: int = 1) -> List[MeasurementData]:
        """
        获取最新的测量数据

        Args:
            count: 数据条数

        Returns:
            最新的测量数据列表
        """
        sorted_measurements = sorted(self.measurements, key=lambda m: m.timestamp, reverse=True)
        return sorted_measurements[:count]

    def get_time_series(
        self,
        function: Optional[str] = None
    ) -> Tuple[List[datetime], List[float], str]:
        """
        获取时间序列数据

        Args:
            function: 过滤特定测量功能

        Returns:
            (时间戳列表, 数值列表, 单位)
        """
        filtered = self.measurements
        if function:
            filtered = [m for m in self.measurements if m.function == function]

        if not filtered:
            return [], [], ""

        timestamps = [m.timestamp for m in filtered]
        values = [m.value for m in filtered]
        unit = filtered[0].unit

        return timestamps, values, unit

    def detect_outliers(
        self,
        function: Optional[str] = None,
        threshold: float = 3.0
    ) -> List[MeasurementData]:
        """
        检测异常值

        Args:
            function: 过滤特定测量功能
            threshold: 标准差阈值

        Returns:
            异常值列表
        """
        filtered = self.measurements
        if function:
            filtered = [m for m in self.measurements if m.function == function]

        if len(filtered) < 2:
            return []

        # 计算统计量
        stats = self.calculate_statistics(function)
        if not stats:
            return []

        # 检测异常值
        outliers = []
        for measurement in filtered:
            z_score = abs(measurement.value - stats.mean) / stats.std_dev
            if z_score > threshold:
                outliers.append(measurement)

        return outliers

    def calculate_rate(self, window_seconds: float = 60.0) -> float:
        """
        计算测量速率

        Args:
            window_seconds: 时间窗口（秒）

        Returns:
            测量速率（次/秒）
        """
        if not self.measurements:
            return 0.0

        # 按时间排序
        sorted_measurements = sorted(self.measurements, key=lambda m: m.timestamp)

        if len(sorted_measurements) < 2:
            return 0.0

        # 计算时间跨度
        start_time = sorted_measurements[0].timestamp
        end_time = sorted_measurements[-1].timestamp
        total_seconds = (end_time - start_time).total_seconds()

        if total_seconds <= 0:
            return 0.0

        # 计算速率
        rate = len(sorted_measurements) / total_seconds
        return rate


class MeasurementValidator:
    """测量数据验证器"""

    @staticmethod
    def validate_measurement(measurement: MeasurementData) -> Tuple[bool, str]:
        """
        验证测量数据

        Args:
            measurement: 测量数据

        Returns:
            (是否有效, 错误信息)
        """
        # 检查基本字段
        if not measurement.timestamp:
            return False, "时间戳缺失"

        if not measurement.function:
            return False, "测量功能缺失"

        if measurement.value is None:
            return False, "测量值缺失"

        # 检查数值有效性
        if not isinstance(measurement.value, (int, float)):
            return False, "测量值类型错误"

        if not isinstance(measurement.unit, str):
            return False, "单位类型错误"

        # 检查特定功能的数值范围
        if measurement.function in [MEASUREMENT_DCV, MEASUREMENT_ACV]:
            if abs(measurement.value) > 1000:  # 1000V最大量程
                return False, f"电压值超出范围: {measurement.value} V"

        elif measurement.function in [MEASUREMENT_DCI, MEASUREMENT_ACI]:
            if abs(measurement.value) > 10:  # 10A最大量程
                return False, f"电流值超出范围: {measurement.value} A"

        elif measurement.function == MEASUREMENT_OHM:
            if measurement.value < 0:
                return False, f"电阻值不能为负: {measurement.value} Ω"

        elif measurement.function == MEASUREMENT_FREQ:
            if measurement.value < 0:
                return False, f"频率值不能为负: {measurement.value} Hz"

        return True, "测量数据有效"

    @staticmethod
    def validate_measurement_batch(measurements: List[MeasurementData]) -> List[Tuple[MeasurementData, bool, str]]:
        """
        批量验证测量数据

        Args:
            measurements: 测量数据列表

        Returns:
            [(测量数据, 是否有效, 错误信息), ...]
        """
        results = []
        for measurement in measurements:
            is_valid, message = MeasurementValidator.validate_measurement(measurement)
            results.append((measurement, is_valid, message))
        return results


def calculate_average(measurements: List[MeasurementData], function: Optional[str] = None) -> Optional[float]:
    """
    计算平均值

    Args:
        measurements: 测量数据列表
        function: 过滤特定测量功能

    Returns:
        平均值，如果无数据返回None
    """
    filtered = measurements
    if function:
        filtered = [m for m in measurements if m.function == function]

    if not filtered:
        return None

    values = [m.value for m in filtered]
    return statistics.mean(values)


def calculate_standard_deviation(measurements: List[MeasurementData], function: Optional[str] = None) -> Optional[float]:
    """
    计算标准差

    Args:
        measurements: 测量数据列表
        function: 过滤特定测量功能

    Returns:
        标准差，如果无数据返回None
    """
    filtered = measurements
    if function:
        filtered = [m for m in measurements if m.function == function]

    if len(filtered) < 2:
        return None

    values = [m.value for m in filtered]
    return statistics.stdev(values)


def find_min_max(measurements: List[MeasurementData], function: Optional[str] = None) -> Optional[Tuple[float, float]]:
    """
    查找最小值和最大值

    Args:
        measurements: 测量数据列表
        function: 过滤特定测量功能

    Returns:
        (最小值, 最大值)，如果无数据返回None
    """
    filtered = measurements
    if function:
        filtered = [m for m in measurements if m.function == function]

    if not filtered:
        return None

    values = [m.value for m in filtered]
    return min(values), max(values)