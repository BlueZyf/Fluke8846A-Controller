"""
通信适配器基类

定义所有通信适配器的统一接口。
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from enum import Enum


class ConnectionState(Enum):
    """连接状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class BaseAdapter(ABC):
    """通信适配器基类"""

    def __init__(self, adapter_id: str, protocol: str):
        """
        初始化适配器

        Args:
            adapter_id: 适配器ID
            protocol: 协议名称
        """
        self.adapter_id = adapter_id
        self.protocol = protocol
        self.state = ConnectionState.DISCONNECTED
        self.connection_params: Dict[str, Any] = {}
        self.last_activity: Optional[float] = None
        self.error_message: Optional[str] = None

    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """
        建立连接

        Args:
            **kwargs: 连接参数

        Returns:
            是否连接成功
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        断开连接

        Returns:
            是否断开成功
        """
        pass

    @abstractmethod
    def send(self, data: bytes) -> int:
        """
        发送数据

        Args:
            data: 要发送的数据

        Returns:
            发送的字节数
        """
        pass

    @abstractmethod
    def receive(self, timeout: float = 1.0) -> bytes:
        """
        接收数据

        Args:
            timeout: 超时时间（秒）

        Returns:
            接收到的数据
        """
        pass

    def query(self, data: bytes, timeout: float = 1.0) -> bytes:
        """
        查询（发送后接收）

        Args:
            data: 要发送的数据
            timeout: 超时时间（秒）

        Returns:
            接收到的数据
        """
        self.send(data)
        return self.receive(timeout)

    def is_connected(self) -> bool:
        """
        检查是否已连接

        Returns:
            是否已连接
        """
        return self.state == ConnectionState.CONNECTED

    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = time.time()

    def set_error(self, message: str):
        """设置错误信息"""
        self.state = ConnectionState.ERROR
        self.error_message = message

    def clear_error(self):
        """清除错误信息"""
        if self.state == ConnectionState.ERROR:
            self.state = ConnectionState.DISCONNECTED
        self.error_message = None

    def get_status(self) -> Dict[str, Any]:
        """
        获取适配器状态

        Returns:
            状态字典
        """
        return {
            "adapter_id": self.adapter_id,
            "protocol": self.protocol,
            "state": self.state.value,
            "last_activity": self.last_activity,
            "error_message": self.error_message,
            "connection_params": self.connection_params.copy(),
        }

    @classmethod
    def detect_available_ports(cls) -> list:
        """
        检测可用端口

        Returns:
            可用端口列表
        """
        return []

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(id={self.adapter_id}, protocol={self.protocol}, state={self.state.value})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"{self.__class__.__name__}(adapter_id={self.adapter_id!r}, protocol={self.protocol!r})"