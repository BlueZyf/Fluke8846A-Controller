"""
FLUKE 8846A 仪器控制核心类

提供FLUKE 8846A数字万用表的完整控制接口。
支持RS-232串口连接（前期主要使用），也支持GPIB和USB。
"""

import time
import threading
from typing import Optional, Dict, Any, Tuple, List, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..communication.visa_manager import VisaManager
from ..communication.serial_adapter import SerialAdapter
from ..communication.gpib_adapter import GPIBAdapter
from ..communication.tcp_adapter import TCPAdapter
from ..communication.base_adapter import BaseAdapter
from ..config.constants import *
from ..utils.logger import get_logger
from ..utils.converters import format_value, parse_measurement
from ..core.commands import build_configure_command


logger = get_logger(__name__)


class InstrumentError(Exception):
    """仪器错误异常"""
    pass


class MeasurementMode(Enum):
    """测量模式枚举"""
    SINGLE = "single"      # 单次测量
    CONTINUOUS = "continuous"  # 连续测量
    TRIGGERED = "triggered"    # 触发测量


@dataclass
class MeasurementData:
    """测量数据结构"""
    timestamp: datetime
    function: str
    value: float
    unit: str
    range: Optional[str] = None
    resolution: Optional[str] = None
    status: str = "OK"
    raw_value: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "function": self.function,
            "value": self.value,
            "unit": self.unit,
            "range": self.range,
            "resolution": self.resolution,
            "status": self.status,
            "raw_value": self.raw_value,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.timestamp.strftime('%H:%M:%S')} {self.function}: {format_value(self.value, precision=6)} {self.unit}"


class Fluke8846AInstrument:
    """FLUKE 8846A 仪器控制类"""

    def __init__(self, instrument_id: str = "fluke8846a"):
        """
        初始化仪器控制类

        Args:
            instrument_id: 仪器ID
        """
        self.instrument_id = instrument_id
        self.connected = False
        self.interface: Optional[str] = None
        self.adapter: Optional[BaseAdapter] = None
        self.visa_manager: Optional[VisaManager] = None

        # 测量状态
        self.measurement_mode = MeasurementMode.SINGLE
        self.current_function = MEASUREMENT_DCV
        self.current_range = RANGE_AUTO
        self.current_resolution = RESOLUTION_6_5

        # 数据存储
        self.measurement_history: List[MeasurementData] = []
        self.max_history_size = 1000

        # 线程安全
        self._lock = threading.RLock()
        self._measurement_thread: Optional[threading.Thread] = None
        self._stop_measurement = threading.Event()

        # 仪器信息
        self.device_info: Dict[str, str] = {}

        logger.info(f"FLUKE 8846A仪器控制类初始化: {instrument_id}")

    def connect_serial(
        self,
        port: str,
        baudrate: int = 9600,
        bytesize: int = 8,
        parity: str = 'N',
        stopbits: float = 1,
        timeout: float = 1.0,
    ) -> bool:
        """
        通过串口连接仪器

        Args:
            port: 串口名称（如"COM3"）
            baudrate: 波特率（默认9600）
            bytesize: 数据位（默认8）
            parity: 校验位（默认'N'）
            stopbits: 停止位（默认1）
            timeout: 超时时间（秒，默认1.0）

        Returns:
            是否连接成功
        """
        with self._lock:
            try:
                logger.info(f"尝试串口连接: {port} @ {baudrate} baud")

                # 创建串口适配器
                self.adapter = SerialAdapter(f"serial_{port}")
                self.interface = INTERFACE_SERIAL

                # 连接参数
                connection_params = {
                    "port": port,
                    "baudrate": baudrate,
                    "bytesize": bytesize,
                    "parity": parity,
                    "stopbits": stopbits,
                    "timeout": timeout,
                }

                # 建立连接
                if not self.adapter.connect(**connection_params):
                    raise InstrumentError("串口连接失败")

                # 测试通信
                if not self._test_communication():
                    raise InstrumentError("通信测试失败")

                self.connected = True
                logger.info(f"串口连接成功: {port}")

                # 获取设备信息
                self._read_device_info()

                return True

            except Exception as e:
                logger.error(f"串口连接失败: {e}")
                self.disconnect()
                return False

    def connect_visa(self, resource_name: str, timeout: int = 5000) -> bool:
        """
        通过VISA连接仪器

        Args:
            resource_name: VISA资源名称
            timeout: 超时时间（毫秒，默认5000）

        Returns:
            是否连接成功
        """
        with self._lock:
            try:
                logger.info(f"尝试VISA连接: {resource_name}")

                # 创建VISA管理器
                self.visa_manager = VisaManager()
                if not self.visa_manager.initialize():
                    raise InstrumentError("VISA管理器初始化失败")

                # 打开资源
                resource = self.visa_manager.open_resource(resource_name, timeout=timeout)
                if not resource:
                    raise InstrumentError(f"无法打开VISA资源: {resource_name}")

                # 检测接口类型
                self.interface = self.visa_manager._detect_interface(resource_name)

                # 测试通信
                success, message = self.visa_manager.test_connection(resource_name)
                if not success:
                    raise InstrumentError(f"VISA连接测试失败: {message}")

                self.connected = True
                logger.info(f"VISA连接成功: {resource_name}")

                # 获取设备信息
                self._read_device_info()

                return True

            except Exception as e:
                logger.error(f"VISA连接失败: {e}")
                self.disconnect()
                return False

    def connect_tcp(self, host: str, port: int = 5025, timeout: float = 5.0) -> bool:
        """
        通过TCP/IP连接仪器

        Args:
            host: 设备IP地址或主机名
            port: TCP端口（默认5025）
            timeout: 超时时间（秒，默认5.0）

        Returns:
            是否连接成功
        """
        with self._lock:
            try:
                logger.info(f"尝试TCP连接: {host}:{port}")

                # 创建TCP适配器
                adapter_id = f"tcp_{self.instrument_id}"
                self.adapter = TCPAdapter(adapter_id)
                self.interface = INTERFACE_TCP

                # 建立连接
                if not self.adapter.connect(host=host, port=port, timeout=timeout):
                    raise InstrumentError("TCP连接失败")

                # 测试通信
                if not self._test_communication():
                    raise InstrumentError("TCP通信测试失败")

                self.connected = True
                logger.info(f"TCP连接成功: {host}:{port}")

                # 获取设备信息
                self._read_device_info()

                return True

            except Exception as e:
                logger.error(f"TCP连接失败: {e}")
                self.disconnect()
                return False

    def connect_mock(self, **kwargs) -> bool:
        """
        连接模拟设备

        Args:
            **kwargs: 连接参数（模拟模式忽略大部分参数）

        Returns:
            是否连接成功
        """
        with self._lock:
            try:
                # 动态导入MockAdapter以避免循环导入
                from ..communication.mock_adapter import MockAdapter

                logger.info("尝试连接模拟设备")
                logger.debug(f"连接参数: {kwargs}")

                # 创建模拟适配器
                adapter_id = kwargs.get("adapter_id", f"mock_{self.instrument_id}")
                self.adapter = MockAdapter(adapter_id)
                self.interface = INTERFACE_MOCK

                # 建立连接
                if not self.adapter.connect(**kwargs):
                    raise InstrumentError("模拟设备连接失败")

                # 测试通信
                if not self._test_communication():
                    raise InstrumentError("模拟设备通信测试失败")

                self.connected = True
                logger.info("模拟设备连接成功")

                # 获取设备信息
                self._read_device_info()

                return True

            except Exception as e:
                logger.error(f"模拟设备连接失败: {e}")
                self.disconnect()
                return False

    def disconnect(self) -> bool:
        """断开仪器连接"""
        with self._lock:
            try:
                # 停止测量线程
                self.stop_continuous_measurement()

                # 断开适配器
                if self.adapter:
                    self.adapter.disconnect()
                    self.adapter = None

                # 关闭VISA连接
                if self.visa_manager:
                    self.visa_manager.cleanup()
                    self.visa_manager = None

                self.connected = False
                self.interface = None
                self.device_info.clear()

                logger.info("仪器连接已断开")
                return True

            except Exception as e:
                logger.error(f"断开连接失败: {e}")
                return False

    def identify(self) -> Optional[str]:
        """
        识别仪器

        Returns:
            仪器识别字符串
        """
        with self._lock:
            try:
                if not self.connected:
                    raise InstrumentError("仪器未连接")

                response = self._send_command("*IDN?")
                if response:
                    # 解析识别信息
                    parts = response.split(',')
                    if len(parts) >= 4:
                        self.device_info = {
                            "manufacturer": parts[0].strip(),
                            "model": parts[1].strip(),
                            "serial_number": parts[2].strip(),
                            "firmware_version": parts[3].strip(),
                        }
                        logger.info(f"仪器识别: {self.device_info}")
                    return response
                return None

            except Exception as e:
                logger.error(f"识别仪器失败: {e}")
                return None

    def reset(self) -> bool:
        """
        重置仪器到默认状态

        Returns:
            是否重置成功
        """
        with self._lock:
            try:
                if not self.connected:
                    raise InstrumentError("仪器未连接")

                success = self._send_command("*RST")
                if success:
                    # 重置本地状态
                    self.current_function = MEASUREMENT_DCV
                    self.current_range = RANGE_AUTO
                    self.current_resolution = RESOLUTION_6_5
                    logger.info("仪器已重置")
                    return True
                return False

            except Exception as e:
                logger.error(f"重置仪器失败: {e}")
                return False

    def configure_measurement(
        self,
        function: str,
        range_val: Optional[str] = None,
        resolution: Optional[str] = None,
        nplc: Optional[float] = None,
    ) -> bool:
        """
        配置测量参数

        Args:
            function: 测量功能
            range_val: 量程
            resolution: 分辨率
            nplc: NPLC值（电源线周期数）

        Returns:
            是否配置成功
        """
        with self._lock:
            try:
                if not self.connected:
                    raise InstrumentError("仪器未连接")

                # 验证参数
                if function not in MEASUREMENTS:
                    raise ValueError(f"无效的测量功能: {function}")

                # 量程和分辨率验证由build_configure_command函数处理
                # 这里只做基本验证

                # 使用命令构建函数创建配置命令
                try:
                    cmd = build_configure_command(function, range_val, resolution)
                except ValueError as e:
                    logger.error(f"构建配置命令失败: {e}")
                    return False

                # 发送配置命令
                if not self._send_command(cmd):
                    return False

                # 更新本地状态
                self.current_function = function
                if range_val:
                    self.current_range = range_val
                if resolution:
                    self.current_resolution = resolution

                logger.info(f"测量配置: {function}, 量程: {range_val}, 分辨率: {resolution}")
                return True

            except Exception as e:
                logger.error(f"配置测量参数失败: {e}")
                return False

    def measure_single(self) -> Optional[MeasurementData]:
        """
        单次测量

        Returns:
            测量数据，失败返回None
        """
        with self._lock:
            try:
                if not self.connected:
                    raise InstrumentError("仪器未连接")

                logger.info(f"单次测量开始，当前功能: {self.current_function}")

                # 确保仪器已配置为当前测量功能
                # 有些仪器需要在测量前发送配置命令
                self._ensure_measurement_configured()

                # 发送测量命令
                command = self._get_measurement_command()
                logger.info(f"测量命令: {command}")
                response = self._send_command(command)

                if not response:
                    raise InstrumentError("测量无响应")

                # 解析测量结果
                measurement = self._parse_measurement_response(response)
                if measurement:
                    # 添加到历史记录
                    self._add_to_history(measurement)
                    logger.info(f"单次测量成功: {measurement}")
                    return measurement
                else:
                    logger.warning(f"无法解析测量响应: {response}")
                    return None

            except Exception as e:
                logger.error(f"单次测量失败: {e}")
                return None

    def start_continuous_measurement(self, interval: float = 1.0) -> bool:
        """
        开始连续测量

        Args:
            interval: 测量间隔（秒）

        Returns:
            是否启动成功
        """
        with self._lock:
            try:
                if not self.connected:
                    raise InstrumentError("仪器未连接")

                # 停止现有的测量线程
                self.stop_continuous_measurement()

                # 创建新的测量线程
                self._stop_measurement.clear()
                self._measurement_thread = threading.Thread(
                    target=self._continuous_measurement_loop,
                    args=(interval,),
                    daemon=True
                )
                self._measurement_thread.start()

                self.measurement_mode = MeasurementMode.CONTINUOUS
                logger.info(f"开始连续测量，间隔: {interval}秒")
                return True

            except Exception as e:
                logger.error(f"启动连续测量失败: {e}")
                return False

    def stop_continuous_measurement(self) -> bool:
        """停止连续测量"""
        with self._lock:
            try:
                if self._measurement_thread and self._measurement_thread.is_alive():
                    self._stop_measurement.set()
                    self._measurement_thread.join(timeout=2.0)

                self._measurement_thread = None
                self.measurement_mode = MeasurementMode.SINGLE
                logger.info("连续测量已停止")
                return True

            except Exception as e:
                logger.error(f"停止连续测量失败: {e}")
                return False

    def get_status(self) -> Dict[str, Any]:
        """
        获取仪器状态

        Returns:
            状态字典
        """
        with self._lock:
            status = {
                "connected": self.connected,
                "interface": self.interface,
                "measurement_mode": self.measurement_mode.value,
                "current_function": self.current_function,
                "current_range": self.current_range,
                "current_resolution": self.current_resolution,
                "device_info": self.device_info.copy(),
                "history_size": len(self.measurement_history),
                "adapter_status": self.adapter.get_status() if self.adapter else None,
            }
            return status

    def clear_history(self):
        """清空测量历史"""
        with self._lock:
            self.measurement_history.clear()
            logger.info("测量历史已清空")

    def get_history(self, limit: Optional[int] = None) -> List[MeasurementData]:
        """
        获取测量历史

        Args:
            limit: 返回的最大记录数

        Returns:
            测量历史列表
        """
        with self._lock:
            if limit:
                return self.measurement_history[-limit:]
            return self.measurement_history.copy()

    # 私有方法
    def _test_communication(self) -> bool:
        """测试通信"""
        try:
            # 尝试识别命令
            response = self._send_command("*IDN?")
            logger.debug(f"通信测试响应: {response}")
            return response is not None and len(response) > 0
        except Exception as e:
            logger.debug(f"通信测试异常: {e}")
            return False

    def _read_device_info(self):
        """读取设备信息"""
        try:
            self.identify()
        except Exception as e:
            logger.warning(f"读取设备信息失败: {e}")

    def _send_command(self, command: str) -> Optional[str]:
        """发送命令到仪器"""
        try:
            if self.adapter:
                # 使用适配器
                logger.debug(f"通过适配器发送命令: {command}")
                response = self.adapter.query(command.encode('utf-8'))
                logger.debug(f"适配器响应原始字节: {response}")
                logger.debug(f"适配器响应长度: {len(response) if response else 0}")
                if response:
                    decoded = response.decode('utf-8', errors='ignore')
                    logger.debug(f"适配器响应解码: '{decoded}'")
                    return decoded
                return None
            elif self.visa_manager and self.interface:
                # 使用VISA管理器
                # 需要资源名称，这里简化处理
                # 实际应该保存资源名称
                return None
            else:
                logger.debug("没有可用的适配器或VISA管理器")
                return None
        except Exception as e:
            logger.error(f"发送命令失败: {command}, 错误: {e}")
            return None

    def _get_measurement_command(self) -> str:
        """获取测量命令"""
        commands = {
            MEASUREMENT_DCV: "MEAS:VOLT:DC?",
            MEASUREMENT_ACV: "MEAS:VOLT:AC?",
            MEASUREMENT_DCI: "MEAS:CURR:DC?",
            MEASUREMENT_ACI: "MEAS:CURR:AC?",
            MEASUREMENT_OHM: "MEAS:RES?",
            MEASUREMENT_FREQ: "MEAS:FREQ?",
        }
        return commands.get(self.current_function, "MEAS:VOLT:DC?")

    def _parse_measurement_response(self, response: str) -> Optional[MeasurementData]:
        """解析测量响应"""
        try:
            # 移除空白字符
            response = response.strip()

            # 解析数值和单位
            value, unit = parse_measurement(response)
            if value is None:
                logger.warning(f"无法解析测量响应: {response}")
                return None

            # 创建测量数据
            measurement = MeasurementData(
                timestamp=datetime.now(),
                function=self.current_function,
                value=value,
                unit=unit or self._get_default_unit(),
                range=self.current_range,
                resolution=self.current_resolution,
                raw_value=response,
            )

            return measurement

        except Exception as e:
            logger.error(f"解析测量响应失败: {response}, 错误: {e}")
            return None

    def _get_default_unit(self) -> str:
        """获取默认单位"""
        units = {
            MEASUREMENT_DCV: "V",
            MEASUREMENT_ACV: "V",
            MEASUREMENT_DCI: "A",
            MEASUREMENT_ACI: "A",
            MEASUREMENT_OHM: "Ω",
            MEASUREMENT_FREQ: "Hz",
        }
        return units.get(self.current_function, "")

    def _ensure_measurement_configured(self):
        """确保仪器已配置为当前测量功能"""
        try:
            # 检查是否需要配置
            # 这里可以添加更复杂的逻辑，比如检查上次配置的时间
            # 目前总是发送配置命令以确保仪器处于正确状态
            logger.info(f"确保仪器配置: {self.current_function}")
            success = self.configure_measurement(
                function=self.current_function,
                range_val=self.current_range,
                resolution=self.current_resolution
            )
            if not success:
                logger.warning(f"仪器配置失败，但继续尝试测量")
        except Exception as e:
            logger.warning(f"仪器配置检查失败: {e}")

    def _add_to_history(self, measurement: MeasurementData):
        """添加到历史记录"""
        self.measurement_history.append(measurement)
        # 限制历史记录大小
        if len(self.measurement_history) > self.max_history_size:
            self.measurement_history = self.measurement_history[-self.max_history_size:]

    def _continuous_measurement_loop(self, interval: float):
        """连续测量循环"""
        logger.info(f"连续测量线程启动，间隔: {interval}秒")

        while not self._stop_measurement.is_set():
            try:
                # 执行单次测量
                measurement = self.measure_single()
                if measurement:
                    # 这里可以触发事件或回调
                    pass

                # 等待间隔时间
                time.sleep(interval)

            except Exception as e:
                logger.error(f"连续测量循环错误: {e}")
                time.sleep(1.0)  # 错误后等待1秒

        logger.info("连续测量线程结束")

    def __del__(self):
        """析构函数，确保断开连接"""
        try:
            self.disconnect()
        except:
            pass