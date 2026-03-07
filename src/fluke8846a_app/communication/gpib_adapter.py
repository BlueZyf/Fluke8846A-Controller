"""
GPIB通信适配器
"""

import time
from typing import Dict, Any, Optional
from .base_adapter import BaseAdapter, ConnectionState
from .visa_manager import VisaManager
from ..utils.logger import get_logger


logger = get_logger(__name__)


class GPIBAdapter(BaseAdapter):
    """GPIB通信适配器"""

    def __init__(self, adapter_id: str = "gpib_adapter"):
        """初始化GPIB适配器"""
        super().__init__(adapter_id, "GPIB")
        self.visa_manager: Optional[VisaManager] = None
        self.resource_name: Optional[str] = None
        self.resource = None
        self.gpib_address: Optional[int] = None
        self.board_index: int = 0
        self.timeout: int = 5000

    def connect(self, **kwargs) -> bool:
        """
        连接GPIB设备

        Args:
            **kwargs: 连接参数，包括：
                - resource_name: VISA资源名称（可选）
                - gpib_address: GPIB地址（可选）
                - board_index: GPIB板卡索引（默认0）
                - timeout: 超时时间（毫秒，默认5000）

        Returns:
            是否连接成功
        """
        try:
            self.state = ConnectionState.CONNECTING
            self.connection_params = kwargs.copy()

            # 解析参数
            resource_name = kwargs.get("resource_name")
            gpib_address = kwargs.get("gpib_address")
            self.board_index = kwargs.get("board_index", 0)
            self.timeout = kwargs.get("timeout", 5000)

            # 确定资源名称
            if resource_name:
                self.resource_name = resource_name
            elif gpib_address is not None:
                self.gpib_address = int(gpib_address)
                self.resource_name = f"GPIB{self.board_index}::{self.gpib_address}::INSTR"
            else:
                raise ValueError("必须提供resource_name或gpib_address参数")

            # 初始化VISA管理器
            self.visa_manager = VisaManager()
            if not self.visa_manager.initialize():
                raise RuntimeError("VISA管理器初始化失败")

            # 打开资源
            self.resource = self.visa_manager.open_resource(
                self.resource_name,
                timeout=self.timeout
            )

            if not self.resource:
                raise RuntimeError(f"无法打开GPIB资源: {self.resource_name}")

            # 测试连接
            success, message = self.visa_manager.test_connection(self.resource_name)
            if not success:
                raise RuntimeError(f"GPIB连接测试失败: {message}")

            self.state = ConnectionState.CONNECTED
            self.update_activity()
            logger.info(f"GPIB连接成功: {self.resource_name}")
            return True

        except Exception as e:
            error_msg = f"GPIB连接失败: {e}"
            self.set_error(error_msg)
            logger.error(error_msg)
            return False

    def disconnect(self) -> bool:
        """断开GPIB连接"""
        try:
            if self.visa_manager and self.resource_name:
                self.visa_manager.close_resource(self.resource_name)

            self.resource = None
            self.resource_name = None
            self.state = ConnectionState.DISCONNECTED
            self.update_activity()
            logger.info("GPIB连接已断开")
            return True

        except Exception as e:
            error_msg = f"GPIB断开连接失败: {e}"
            self.set_error(error_msg)
            logger.error(error_msg)
            return False

    def send(self, data: bytes) -> int:
        """发送数据到GPIB设备"""
        try:
            if not self.is_connected() or not self.resource_name or not self.visa_manager:
                raise RuntimeError("GPIB适配器未连接")

            # 将字节数据转换为字符串
            command = data.decode('utf-8', errors='ignore').strip()
            success = self.visa_manager.send_command(self.resource_name, command)

            if not success:
                raise RuntimeError("发送命令失败")

            self.update_activity()
            return len(data)

        except Exception as e:
            error_msg = f"GPIB发送数据失败: {e}"
            self.set_error(error_msg)
            logger.error(error_msg)
            return 0

    def receive(self, timeout: float = 1.0) -> bytes:
        """从GPIB设备接收数据"""
        try:
            if not self.is_connected() or not self.resource_name or not self.visa_manager:
                raise RuntimeError("GPIB适配器未连接")

            # 注意：VISA查询通常是发送和接收的组合
            # 对于纯接收，我们需要更复杂的逻辑
            # 这里简单返回空数据，实际应用应该根据需要实现
            self.update_activity()
            return b""

        except Exception as e:
            error_msg = f"GPIB接收数据失败: {e}"
            self.set_error(error_msg)
            logger.error(error_msg)
            return b""

    def query(self, data: bytes, timeout: float = 1.0) -> bytes:
        """GPIB查询（发送命令并接收响应）"""
        try:
            if not self.is_connected() or not self.resource_name or not self.visa_manager:
                raise RuntimeError("GPIB适配器未连接")

            # 将字节数据转换为字符串
            command = data.decode('utf-8', errors='ignore').strip()
            response = self.visa_manager.query(self.resource_name, command)

            if response is None:
                raise RuntimeError("查询无响应")

            self.update_activity()
            return response.encode('utf-8')

        except Exception as e:
            error_msg = f"GPIB查询失败: {e}"
            self.set_error(error_msg)
            logger.error(error_msg)
            return b""

    def identify(self) -> Optional[str]:
        """
        识别设备

        Returns:
            设备识别字符串
        """
        try:
            if not self.is_connected() or not self.resource_name or not self.visa_manager:
                return None

            response = self.visa_manager.query(self.resource_name, "*IDN?")
            return response

        except Exception as e:
            logger.error(f"设备识别失败: {e}")
            return None

    @classmethod
    def detect_available_ports(cls) -> list:
        """检测可用GPIB端口"""
        try:
            visa_manager = VisaManager()
            if not visa_manager.initialize():
                return []

            resources = visa_manager.list_resources()
            gpib_resources = [r for r in resources if "GPIB" in r.upper()]

            return gpib_resources

        except Exception as e:
            logger.error(f"检测GPIB端口失败: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        status = super().get_status()
        status.update({
            "resource_name": self.resource_name,
            "gpib_address": self.gpib_address,
            "board_index": self.board_index,
            "timeout": self.timeout,
        })
        return status