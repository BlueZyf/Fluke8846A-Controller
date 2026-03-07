"""
数据处理模块

提供测量数据的处理、转换和导出功能。
"""

import csv
import json
import pandas as pd
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime

from .instrument import MeasurementData
from ..utils.logger import get_logger
from ..utils.helpers import ensure_directory, generate_filename


logger = get_logger(__name__)


class DataProcessor:
    """数据处理类"""

    def __init__(self):
        """初始化数据处理类"""
        self.measurements: List[MeasurementData] = []

    def add_measurement(self, measurement: MeasurementData):
        """添加测量数据"""
        self.measurements.append(measurement)

    def add_measurements(self, measurements: List[MeasurementData]):
        """批量添加测量数据"""
        self.measurements.extend(measurements)

    def clear(self):
        """清空数据"""
        self.measurements.clear()

    def export_to_csv(
        self,
        filepath: Union[str, Path],
        include_header: bool = True,
        delimiter: str = ',',
        encoding: str = 'utf-8'
    ) -> bool:
        """
        导出为CSV文件

        Args:
            filepath: 文件路径
            include_header: 是否包含表头
            delimiter: 分隔符
            encoding: 文件编码

        Returns:
            是否导出成功
        """
        try:
            filepath = Path(filepath)
            ensure_directory(filepath.parent)

            # 转换为字典列表
            data = [m.to_dict() for m in self.measurements]

            if not data:
                logger.warning("没有数据可导出")
                return False

            # 获取所有字段名
            fieldnames = list(data[0].keys())

            with open(filepath, 'w', newline='', encoding=encoding) as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)

                if include_header:
                    writer.writeheader()

                writer.writerows(data)

            logger.info(f"数据已导出到CSV文件: {filepath}, 共 {len(data)} 条记录")
            return True

        except Exception as e:
            logger.error(f"导出CSV文件失败: {e}")
            return False

    def export_to_json(
        self,
        filepath: Union[str, Path],
        indent: int = 2,
        ensure_ascii: bool = False,
        encoding: str = 'utf-8'
    ) -> bool:
        """
        导出为JSON文件

        Args:
            filepath: 文件路径
            indent: 缩进空格数
            ensure_ascii: 是否确保ASCII编码
            encoding: 文件编码

        Returns:
            是否导出成功
        """
        try:
            filepath = Path(filepath)
            ensure_directory(filepath.parent)

            # 转换为字典列表
            data = [m.to_dict() for m in self.measurements]

            with open(filepath, 'w', encoding=encoding) as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)

            logger.info(f"数据已导出到JSON文件: {filepath}, 共 {len(data)} 条记录")
            return True

        except Exception as e:
            logger.error(f"导出JSON文件失败: {e}")
            return False

    def export_to_excel(
        self,
        filepath: Union[str, Path],
        sheet_name: str = "Measurements",
        index: bool = False
    ) -> bool:
        """
        导出为Excel文件

        Args:
            filepath: 文件路径
            sheet_name: 工作表名称
            index: 是否包含索引列

        Returns:
            是否导出成功
        """
        try:
            filepath = Path(filepath)
            ensure_directory(filepath.parent)

            # 转换为字典列表
            data = [m.to_dict() for m in self.measurements]

            if not data:
                logger.warning("没有数据可导出")
                return False

            # 创建DataFrame
            df = pd.DataFrame(data)

            # 导出到Excel
            df.to_excel(filepath, sheet_name=sheet_name, index=index)

            logger.info(f"数据已导出到Excel文件: {filepath}, 共 {len(data)} 条记录")
            return True

        except ImportError:
            logger.error("pandas未安装，无法导出Excel文件")
            return False
        except Exception as e:
            logger.error(f"导出Excel文件失败: {e}")
            return False

    def import_from_csv(
        self,
        filepath: Union[str, Path],
        delimiter: str = ',',
        encoding: str = 'utf-8'
    ) -> bool:
        """
        从CSV文件导入数据

        Args:
            filepath: 文件路径
            delimiter: 分隔符
            encoding: 文件编码

        Returns:
            是否导入成功
        """
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                logger.error(f"文件不存在: {filepath}")
                return False

            with open(filepath, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                rows = list(reader)

            # 转换为MeasurementData对象
            measurements = []
            for row in rows:
                try:
                    # 解析时间戳
                    timestamp_str = row.get('timestamp', '')
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                    except ValueError:
                        timestamp = datetime.now()

                    # 解析测量值
                    value = float(row.get('value', 0))
                    unit = row.get('unit', '')

                    # 创建MeasurementData对象
                    measurement = MeasurementData(
                        timestamp=timestamp,
                        function=row.get('function', ''),
                        value=value,
                        unit=unit,
                        range=row.get('range'),
                        resolution=row.get('resolution'),
                        status=row.get('status', 'OK'),
                        raw_value=row.get('raw_value'),
                        metadata={}
                    )

                    measurements.append(measurement)

                except Exception as e:
                    logger.warning(f"解析CSV行失败: {row}, 错误: {e}")

            self.measurements = measurements
            logger.info(f"从CSV文件导入 {len(measurements)} 条记录: {filepath}")
            return True

        except Exception as e:
            logger.error(f"导入CSV文件失败: {e}")
            return False

    def import_from_json(
        self,
        filepath: Union[str, Path],
        encoding: str = 'utf-8'
    ) -> bool:
        """
        从JSON文件导入数据

        Args:
            filepath: 文件路径
            encoding: 文件编码

        Returns:
            是否导入成功
        """
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                logger.error(f"文件不存在: {filepath}")
                return False

            with open(filepath, 'r', encoding=encoding) as f:
                data = json.load(f)

            # 转换为MeasurementData对象
            measurements = []
            for item in data:
                try:
                    # 解析时间戳
                    timestamp_str = item.get('timestamp', '')
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                    except ValueError:
                        timestamp = datetime.now()

                    # 解析测量值
                    value = float(item.get('value', 0))
                    unit = item.get('unit', '')

                    # 创建MeasurementData对象
                    measurement = MeasurementData(
                        timestamp=timestamp,
                        function=item.get('function', ''),
                        value=value,
                        unit=unit,
                        range=item.get('range'),
                        resolution=item.get('resolution'),
                        status=item.get('status', 'OK'),
                        raw_value=item.get('raw_value'),
                        metadata=item.get('metadata', {})
                    )

                    measurements.append(measurement)

                except Exception as e:
                    logger.warning(f"解析JSON项失败: {item}, 错误: {e}")

            self.measurements = measurements
            logger.info(f"从JSON文件导入 {len(measurements)} 条记录: {filepath}")
            return True

        except Exception as e:
            logger.error(f"导入JSON文件失败: {e}")
            return False

    def filter_by_function(self, function: str) -> List[MeasurementData]:
        """
        按测量功能过滤

        Args:
            function: 测量功能

        Returns:
            过滤后的测量数据列表
        """
        return [m for m in self.measurements if m.function == function]

    def filter_by_time_range(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[MeasurementData]:
        """
        按时间范围过滤

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

    def get_summary(self) -> Dict[str, Any]:
        """
        获取数据摘要

        Returns:
            摘要字典
        """
        if not self.measurements:
            return {"total_count": 0, "functions": {}}

        # 按功能分组
        functions = {}
        for measurement in self.measurements:
            func = measurement.function
            if func not in functions:
                functions[func] = {
                    "count": 0,
                    "unit": measurement.unit,
                    "values": []
                }
            functions[func]["count"] += 1
            functions[func]["values"].append(measurement.value)

        # 计算统计信息
        for func, data in functions.items():
            values = data["values"]
            if values:
                data["min"] = min(values)
                data["max"] = max(values)
                data["mean"] = sum(values) / len(values)
                if len(values) > 1:
                    import statistics
                    data["std_dev"] = statistics.stdev(values)
                else:
                    data["std_dev"] = 0
                del data["values"]

        return {
            "total_count": len(self.measurements),
            "time_range": {
                "start": min(m.timestamp for m in self.measurements).isoformat(),
                "end": max(m.timestamp for m in self.measurements).isoformat()
            } if self.measurements else {},
            "functions": functions
        }

    def convert_units(self, target_unit: str, function: Optional[str] = None) -> bool:
        """
        转换单位

        Args:
            target_unit: 目标单位
            function: 只转换特定功能的测量数据

        Returns:
            是否转换成功
        """
        try:
            from ..utils.converters import convert_units

            converted_count = 0
            for measurement in self.measurements:
                if function and measurement.function != function:
                    continue

                if measurement.unit == target_unit:
                    continue

                # 尝试转换
                converted_value = convert_units(
                    measurement.value,
                    measurement.unit,
                    target_unit
                )

                if converted_value is not None:
                    measurement.value = converted_value
                    measurement.unit = target_unit
                    converted_count += 1

            logger.info(f"单位转换完成: {converted_count} 条记录转换为 {target_unit}")
            return converted_count > 0

        except Exception as e:
            logger.error(f"单位转换失败: {e}")
            return False

    def generate_report(
        self,
        output_dir: Union[str, Path],
        report_name: Optional[str] = None,
        formats: List[str] = None
    ) -> Dict[str, Path]:
        """
        生成数据报告

        Args:
            output_dir: 输出目录
            report_name: 报告名称
            formats: 输出格式列表，如 ["csv", "json", "excel"]

        Returns:
            生成的文件路径字典
        """
        if formats is None:
            formats = ["csv", "json"]

        output_dir = Path(output_dir)
        ensure_directory(output_dir)

        if report_name is None:
            report_name = generate_filename(
                prefix="measurement_report",
                timestamp=True,
                extension=""
            ).rstrip('.')

        generated_files = {}

        # 生成各种格式的报告
        for fmt in formats:
            if fmt.lower() == "csv":
                filepath = output_dir / f"{report_name}.csv"
                if self.export_to_csv(filepath):
                    generated_files["csv"] = filepath

            elif fmt.lower() == "json":
                filepath = output_dir / f"{report_name}.json"
                if self.export_to_json(filepath):
                    generated_files["json"] = filepath

            elif fmt.lower() in ["excel", "xlsx"]:
                filepath = output_dir / f"{report_name}.xlsx"
                if self.export_to_excel(filepath):
                    generated_files["excel"] = filepath

        # 生成摘要文件
        summary = self.get_summary()
        summary_file = output_dir / f"{report_name}_summary.json"
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            generated_files["summary"] = summary_file
        except Exception as e:
            logger.error(f"生成摘要文件失败: {e}")

        logger.info(f"报告生成完成: {len(generated_files)} 个文件")
        return generated_files