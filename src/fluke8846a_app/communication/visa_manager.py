"""
VISA通信管理器

提供统一的VISA资源管理接口，支持GPIB、USB、RS-232等多种通信方式。
"""

import threading
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

try:
    import pyvisa as visa
    VISA_AVAILABLE = True
except ImportError:
    VISA_AVAILABLE = False
    visa = None

from ..utils.logger import get_logger
from ..config.constants import INTERFACE_GPIB, INTERFACE_USB, INTERFACE_SERIAL


logger = get_logger(__name__)


class ConnectionStatus(Enum):
    """连接状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class ConnectionInfo:
    """连接信息"""
    resource_name: str
    interface: str
    status: ConnectionStatus
    connected_at: Optional[float] = None
    last_activity: Optional[float] = None
    error_message: Optional[str] = None
    timeout: int = 5000  # 毫秒


class VisaManager:
    """VISA通信管理器"""

    def __init__(self):
        """初始化VISA管理器"""
        self.rm: Optional[visa.ResourceManager] = None
        self.connections: Dict[str, visa.Resource] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}
        self._lock = threading.RLock()

    def initialize(self) -> bool:
        """
        初始化VISA资源管理器

        Returns:
            是否初始化成功
        """
        with self._lock:
            try:
                if not VISA_AVAILABLE:
                    logger.error("PyVISA未安装")
                    return False

                self.rm = visa.ResourceManager()
                logger.info(f"VISA资源管理器初始化成功，后端: {self.rm}")
                return True

            except Exception as e:
                logger.error(f"VISA资源管理器初始化失败: {e}")
                return False

    def list_resources(self, query: str = "?*") -> List[str]:
        """
        列出可用资源

        Args:
            query: 资源查询字符串

        Returns:
            可用资源列表
        """
        with self._lock:
            try:
                if not self.rm:
                    if not self.initialize():
                        return []

                resources = self.rm.list_resources(query)
                logger.debug(f"发现资源: {resources}")
                return resources

            except Exception as e:
                logger.error(f"列出资源失败: {e}")
                return []

    def open_resource(
        self,
        resource_name: str,
        timeout: int = 5000,
        read_termination: str = '\n',
        write_termination: str = '\n',
        **kwargs
    ) -> Optional[visa.Resource]:
        """
        打开VISA资源

        Args:
            resource_name: 资源名称
            timeout: 超时时间（毫秒）
            read_termination: 读取终止符
            write_termination: 写入终止符
            **kwargs: 其他VISA参数

        Returns:
            VISA资源对象，失败返回None
        """
        with self._lock:
            try:
                if not self.rm:
                    if not self.initialize():
                        return None

                # 检查是否已连接
                if resource_name in self.connections:
                    logger.warning(f"资源已连接: {resource_name}")
                    return self.connections[resource_name]

                # 打开资源
                logger.info(f"正在打开资源: {resource_name}")
                resource = self.rm.open_resource(
                    resource_name,
                    timeout=timeout,
                    read_termination=read_termination,
                    write_termination=write_termination,
                    **kwargs
                )

                # 更新连接信息
                interface = self._detect_interface(resource_name)
                self.connections[resource_name] = resource
                self.connection_info[resource_name] = ConnectionInfo(
                    resource_name=resource_name,
                    interface=interface,
                    status=ConnectionStatus.CONNECTED,
                    connected_at=time.time(),
                    last_activity=time.time(),
                    timeout=timeout,
                )

                logger.info(f"资源打开成功: {resource_name}")
                return resource

            except visa.Error as e:
                logger.error(f"打开资源失败: {resource_name}, 错误: {e}")
                self.connection_info[resource_name] = ConnectionInfo(
                    resource_name=resource_name,
                    interface=self._detect_interface(resource_name),
                    status=ConnectionStatus.ERROR,
                    error_message=str(e),
                    timeout=timeout,
                )
                return None

            except Exception as e:
                logger.error(f"打开资源时发生未知错误: {resource_name}, 错误: {e}")
                return None

    def close_resource(self, resource_name: str) -> bool:
        """
        关闭VISA资源

        Args:
            resource_name: 资源名称

        Returns:
            是否成功关闭
        """
        with self._lock:
            try:
                if resource_name not in self.connections:
                    logger.warning(f"资源未连接: {resource_name}")
                    return True

                resource = self.connections[resource_name]
                resource.close()

                # 移除连接信息
                del self.connections[resource_name]
                if resource_name in self.connection_info:
                    del self.connection_info[resource_name]

                logger.info(f"资源关闭成功: {resource_name}")
                return True

            except Exception as e:
                logger.error(f"关闭资源失败: {resource_name}, 错误: {e}")
                return False

    def send_command(self, resource_name: str, command: str) -> bool:
        """
        发送命令到设备

        Args:
            resource_name: 资源名称
            command: 命令字符串

        Returns:
            是否发送成功
        """
        with self._lock:
            try:
                if resource_name not in self.connections:
                    logger.error(f"资源未连接: {resource_name}")
                    return False

                resource = self.connections[resource_name]
                resource.write(command)

                # 更新最后活动时间
                if resource_name in self.connection_info:
                    self.connection_info[resource_name].last_activity = time.time()

                logger.debug(f"发送命令: {command}")
                return True

            except Exception as e:
                logger.error(f"发送命令失败: {command}, 错误: {e}")
                if resource_name in self.connection_info:
                    self.connection_info[resource_name].status = ConnectionStatus.ERROR
                    self.connection_info[resource_name].error_message = str(e)
                return False

    def query(self, resource_name: str, command: str) -> Optional[str]:
        """
        查询设备

        Args:
            resource_name: 资源名称
            command: 查询命令

        Returns:
            查询结果，失败返回None
        """
        with self._lock:
            try:
                if resource_name not in self.connections:
                    logger.error(f"资源未连接: {resource_name}")
                    return None

                resource = self.connections[resource_name]
                response = resource.query(command)

                # 更新最后活动时间
                if resource_name in self.connection_info:
                    self.connection_info[resource_name].last_activity = time.time()

                logger.debug(f"查询命令: {command}, 响应: {response}")
                return response.strip()

            except visa.Error as e:
                logger.error(f"查询命令失败: {command}, VISA错误: {e}")
                if resource_name in self.connection_info:
                    self.connection_info[resource_name].status = ConnectionStatus.ERROR
                    self.connection_info[resource_name].error_message = str(e)
                return None

            except Exception as e:
                logger.error(f"查询命令时发生未知错误: {command}, 错误: {e}")
                return None

    def test_connection(self, resource_name: str) -> Tuple[bool, str]:
        """
        测试连接

        Args:
            resource_name: 资源名称

        Returns:
            (是否成功, 消息)
        """
        with self._lock:
            try:
                # 尝试打开资源
                resource = self.open_resource(resource_name)
                if not resource:
                    return False, "无法打开资源"

                # 尝试发送识别命令
                try:
                    response = resource.query("*IDN?")
                    if response:
                        return True, f"连接成功: {response.strip()}"
                    else:
                        return False, "设备无响应"
                except:
                    # 如果识别命令失败，尝试其他方式
                    try:
                        # 尝试简单查询
                        resource.write("*CLS")
                        return True, "连接成功（基本通信正常）"
                    except:
                        return False, "基本通信测试失败"

            except Exception as e:
                return False, f"连接测试失败: {e}"

    def get_connection_status(self, resource_name: str) -> Optional[ConnectionInfo]:
        """
        获取连接状态

        Args:
            resource_name: 资源名称

        Returns:
            连接信息，如果资源不存在返回None
        """
        with self._lock:
            return self.connection_info.get(resource_name)

    def cleanup(self):
        """清理所有连接"""
        with self._lock:
            try:
                # 复制连接名称列表，避免在迭代时修改
                resource_names = list(self.connections.keys())

                for resource_name in resource_names:
                    try:
                        self.close_resource(resource_name)
                    except Exception as e:
                        logger.warning(f"关闭资源时发生错误 {resource_name}: {e}")

                logger.info("所有连接已清理")
            except Exception as e:
                logger.error(f"清理连接时发生错误: {e}")

    def _detect_interface(self, resource_name: str) -> str:
        """
        检测接口类型

        Args:
            resource_name: 资源名称

        Returns:
            接口类型
        """
        resource_name = resource_name.upper()

        if "GPIB" in resource_name:
            return INTERFACE_GPIB
        elif "USB" in resource_name:
            return INTERFACE_USB
        elif "ASRL" in resource_name or "COM" in resource_name:
            return INTERFACE_SERIAL
        else:
            # 默认返回GPIB
            return INTERFACE_GPIB

    def __del__(self):
        """析构函数，确保清理连接"""
        self.cleanup()