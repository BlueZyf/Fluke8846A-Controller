"""
日志配置模块
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logging(
    log_dir: Path,
    log_level: str = "INFO",
    console_level: str = "INFO",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    设置日志配置

    Args:
        log_dir: 日志目录
        log_level: 文件日志级别
        console_level: 控制台日志级别
        max_file_size: 最大文件大小（字节）
        backup_count: 备份文件数量
    """
    # 确保日志目录存在
    log_dir.mkdir(parents=True, exist_ok=True)

    # 创建日志文件路径
    log_file = log_dir / f"fluke8846a_{datetime.now().strftime('%Y%m%d')}.log"

    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # 设置为最低级别，由处理器控制实际级别

    # 清除现有的处理器
    logger.handlers.clear()

    # 文件处理器
    try:
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"文件日志处理器创建失败: {e}")

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level.upper()))
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 禁止第三方库的调试日志
    logging.getLogger('PyVISA').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        配置好的日志记录器
    """
    return logging.getLogger(name)


class MeasurementLogger:
    """测量数据日志记录器"""

    def __init__(self, log_dir: Path, prefix: str = "measurement"):
        """
        初始化测量日志记录器

        Args:
            log_dir: 日志目录
            prefix: 日志文件前缀
        """
        self.log_dir = log_dir
        self.prefix = prefix
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_measurement(
        self,
        timestamp: datetime,
        function: str,
        value: float,
        unit: str,
        range_val: Optional[str] = None,
        resolution: Optional[str] = None,
        status: str = "OK",
        metadata: Optional[dict] = None,
    ) -> Path:
        """
        记录测量数据

        Args:
            timestamp: 时间戳
            function: 测量功能
            value: 测量值
            unit: 单位
            range_val: 量程
            resolution: 分辨率
            status: 状态
            metadata: 元数据

        Returns:
            日志文件路径
        """
        # 创建日志文件名
        date_str = timestamp.strftime("%Y%m%d")
        filename = f"{self.prefix}_{date_str}.csv"
        log_file = self.log_dir / filename

        # 准备数据行
        data = {
            "timestamp": timestamp.isoformat(),
            "function": function,
            "value": value,
            "unit": unit,
            "range": range_val or "",
            "resolution": resolution or "",
            "status": status,
        }

        if metadata:
            data.update(metadata)

        # 写入CSV文件
        try:
            import csv

            # 检查文件是否存在，如果不存在则写入表头
            file_exists = log_file.exists()

            with open(log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data.keys())

                if not file_exists:
                    writer.writeheader()

                writer.writerow(data)

            return log_file

        except Exception as e:
            get_logger(__name__).error(f"记录测量数据失败: {e}")
            raise