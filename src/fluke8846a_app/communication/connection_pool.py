"""
连接池管理

管理多个通信适配器的连接，提供连接复用和负载均衡。
"""

from typing import Dict, Any, Optional, List
from .base_adapter import BaseAdapter


class ConnectionPool:
    """连接池类"""

    def __init__(self, max_connections: int = 10):
        """
        初始化连接池

        Args:
            max_connections: 最大连接数
        """
        self.max_connections = max_connections
        self.connections: Dict[str, BaseAdapter] = {}
        self.connection_count = 0

    def get_connection(self, adapter_id: str) -> Optional[BaseAdapter]:
        """
        获取连接

        Args:
            adapter_id: 适配器ID

        Returns:
            适配器实例，如果不存在则返回None
        """
        return self.connections.get(adapter_id)

    def add_connection(self, adapter: BaseAdapter) -> bool:
        """
        添加连接

        Args:
            adapter: 适配器实例

        Returns:
            是否添加成功
        """
        if self.connection_count >= self.max_connections:
            return False

        self.connections[adapter.adapter_id] = adapter
        self.connection_count += 1
        return True

    def remove_connection(self, adapter_id: str) -> bool:
        """
        移除连接

        Args:
            adapter_id: 适配器ID

        Returns:
            是否移除成功
        """
        if adapter_id in self.connections:
            del self.connections[adapter_id]
            self.connection_count -= 1
            return True
        return False

    def clear(self):
        """清空连接池"""
        for adapter in self.connections.values():
            adapter.disconnect()
        self.connections.clear()
        self.connection_count = 0

    def get_all_connections(self) -> List[BaseAdapter]:
        """
        获取所有连接

        Returns:
            适配器列表
        """
        return list(self.connections.values())

    def get_active_connections(self) -> List[BaseAdapter]:
        """
        获取活动连接

        Returns:
            已连接的适配器列表
        """
        return [adapter for adapter in self.connections.values() if adapter.is_connected()]

    def __len__(self) -> int:
        """获取连接数量"""
        return self.connection_count

    def __contains__(self, adapter_id: str) -> bool:
        """检查连接是否存在"""
        return adapter_id in self.connections