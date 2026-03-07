"""
串口通信适配器
"""

import time
import threading
from typing import Dict, Any, Optional, List
from .base_adapter import BaseAdapter, ConnectionState
from ..utils.logger import get_logger
from ..utils.validators import validate_serial_port, validate_baudrate


logger = get_logger(__name__)


class SerialAdapter(BaseAdapter):
    """串口通信适配器"""

    def __init__(self, adapter_id: str = "serial_adapter"):
        """初始化串口适配器"""
        super().__init__(adapter_id, "SERIAL")
        self.port: Optional[str] = None
        self.baudrate: int = 9600
        self.bytesize: int = 8
        self.parity: str = 'N'
        self.stopbits: float = 1
        self.timeout: float = 1.0
        self.serial_instance = None
        self._lock = threading.RLock()

    def connect(self, **kwargs) -> bool:
        """
        连接串口设备

        Args:
            **kwargs: 连接参数，包括：
                - port: 串口名称（如"COM3"或"/dev/ttyUSB0"）
                - baudrate: 波特率（默认9600）
                - bytesize: 数据位（默认8）
                - parity: 校验位（默认'N'）
                - stopbits: 停止位（默认1）
                - timeout: 超时时间（秒，默认1.0）

        Returns:
            是否连接成功
        """
        with self._lock:
            try:
                self.state = ConnectionState.CONNECTING
                self.connection_params = kwargs.copy()

                # 解析参数
                port = kwargs.get("port")
                if not port:
                    raise ValueError("必须提供port参数")

                if not validate_serial_port(port):
                    raise ValueError(f"无效的串口名称: {port}")

                baudrate = kwargs.get("baudrate", 9600)
                if not validate_baudrate(baudrate):
                    raise ValueError(f"无效的波特率: {baudrate}")

                self.port = port
                self.baudrate = int(baudrate)
                self.bytesize = kwargs.get("bytesize", 8)
                self.parity = kwargs.get("parity", 'N')
                self.stopbits = kwargs.get("stopbits", 1)
                self.timeout = float(kwargs.get("timeout", 1.0))

                # 导入pyserial
                try:
                    import serial
                except ImportError:
                    raise ImportError("pyserial未安装，请运行: pip install pyserial")

                # 创建串口实例
                self.serial_instance = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=self.bytesize,
                    parity=self.parity,
                    stopbits=self.stopbits,
                    timeout=self.timeout
                )

                # 测试连接
                if not self.serial_instance.is_open:
                    self.serial_instance.open()

                # 简单测试：尝试清空缓冲区
                self.serial_instance.reset_input_buffer()
                self.serial_instance.reset_output_buffer()

                self.state = ConnectionState.CONNECTED
                self.update_activity()
                logger.info(f"串口连接成功: {self.port} @ {self.baudrate} baud")
                return True

            except Exception as e:
                error_msg = f"串口连接失败: {e}"
                self.set_error(error_msg)
                logger.error(error_msg)

                # 清理
                if self.serial_instance and self.serial_instance.is_open:
                    try:
                        self.serial_instance.close()
                    except:
                        pass
                    self.serial_instance = None

                return False

    def disconnect(self) -> bool:
        """断开串口连接"""
        with self._lock:
            try:
                if self.serial_instance and self.serial_instance.is_open:
                    self.serial_instance.close()

                self.serial_instance = None
                self.port = None
                self.state = ConnectionState.DISCONNECTED
                self.update_activity()
                logger.info("串口连接已断开")
                return True

            except Exception as e:
                error_msg = f"串口断开连接失败: {e}"
                self.set_error(error_msg)
                logger.error(error_msg)
                return False

    def send(self, data: bytes) -> int:
        """发送数据到串口设备"""
        with self._lock:
            try:
                if not self.is_connected() or not self.serial_instance:
                    raise RuntimeError("串口适配器未连接")

                if not self.serial_instance.is_open:
                    raise RuntimeError("串口未打开")

                bytes_written = self.serial_instance.write(data)
                self.serial_instance.flush()  # 确保数据发送完成

                self.update_activity()
                logger.debug(f"串口发送数据: {data[:50]}... ({bytes_written}字节)")
                return bytes_written

            except Exception as e:
                error_msg = f"串口发送数据失败: {e}"
                self.set_error(error_msg)
                logger.error(error_msg)
                return 0

    def receive(self, timeout: float = 1.0) -> bytes:
        """从串口设备接收数据"""
        with self._lock:
            try:
                if not self.is_connected() or not self.serial_instance:
                    raise RuntimeError("串口适配器未连接")

                if not self.serial_instance.is_open:
                    raise RuntimeError("串口未打开")

                # 设置临时超时
                original_timeout = self.serial_instance.timeout
                self.serial_instance.timeout = timeout

                try:
                    # 读取可用数据
                    data = self.serial_instance.read(self.serial_instance.in_waiting or 1)

                    # 如果没有数据，尝试读取至少一个字节
                    if not data:
                        data = self.serial_instance.read(1)
                finally:
                    # 恢复原始超时
                    self.serial_instance.timeout = original_timeout

                self.update_activity()
                if data:
                    logger.debug(f"串口接收数据: {data[:50]}... ({len(data)}字节)")
                return data

            except Exception as e:
                error_msg = f"串口接收数据失败: {e}"
                self.set_error(error_msg)
                logger.error(error_msg)
                return b""

    def query(self, data: bytes, timeout: float = 1.0) -> bytes:
        """串口查询（发送命令并接收响应）"""
        with self._lock:
            try:
                # 发送数据
                bytes_sent = self.send(data)
                if bytes_sent == 0:
                    raise RuntimeError("发送数据失败")

                # 等待响应
                time.sleep(0.1)  # 给设备一些响应时间

                # 接收数据
                response = self.receive(timeout)

                return response

            except Exception as e:
                error_msg = f"串口查询失败: {e}"
                self.set_error(error_msg)
                logger.error(error_msg)
                return b""

    def clear_buffers(self):
        """清空输入输出缓冲区"""
        with self._lock:
            try:
                if self.serial_instance and self.serial_instance.is_open:
                    self.serial_instance.reset_input_buffer()
                    self.serial_instance.reset_output_buffer()
                    logger.debug("串口缓冲区已清空")
            except Exception as e:
                logger.warning(f"清空串口缓冲区失败: {e}")

    def get_port_info(self) -> Dict[str, Any]:
        """获取串口信息"""
        with self._lock:
            if not self.serial_instance or not self.serial_instance.is_open:
                return {}

            return {
                "port": self.port,
                "baudrate": self.baudrate,
                "bytesize": self.bytesize,
                "parity": self.parity,
                "stopbits": self.stopbits,
                "timeout": self.timeout,
                "in_waiting": self.serial_instance.in_waiting,
                "out_waiting": self.serial_instance.out_waiting if hasattr(self.serial_instance, 'out_waiting') else 0,
            }

    @classmethod
    def detect_available_ports(cls) -> List[Dict[str, Any]]:
        """检测可用串口"""
        try:
            import serial.tools.list_ports

            ports = []
            for port_info in serial.tools.list_ports.comports():
                ports.append({
                    "device": port_info.device,
                    "name": port_info.name,
                    "description": port_info.description,
                    "hwid": port_info.hwid,
                    "vid": port_info.vid,
                    "pid": port_info.pid,
                    "serial_number": port_info.serial_number,
                    "location": port_info.location,
                    "manufacturer": port_info.manufacturer,
                    "product": port_info.product,
                    "interface": port_info.interface,
                })

            logger.info(f"检测到 {len(ports)} 个串口")
            return ports

        except ImportError:
            logger.error("pyserial未安装，无法检测串口")
            return []
        except Exception as e:
            logger.error(f"检测串口失败: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        status = super().get_status()
        status.update({
            "port": self.port,
            "baudrate": self.baudrate,
            "bytesize": self.bytesize,
            "parity": self.parity,
            "stopbits": self.stopbits,
            "timeout": self.timeout,
            "is_open": self.serial_instance.is_open if self.serial_instance else False,
        })
        return status

    def __del__(self):
        """析构函数，确保断开连接"""
        try:
            self.disconnect()
        except:
            pass