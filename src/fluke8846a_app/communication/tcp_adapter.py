"""
TCP/IP通信适配器

支持通过以太网连接FLUKE 8846A仪器。
使用TCP Socket进行SCPI命令通信，默认端口5025。
"""

import time
import socket
import threading
from typing import Dict, Any, Optional, List
from .base_adapter import BaseAdapter, ConnectionState
from ..utils.logger import get_logger
from ..utils.validators import validate_ip_address, validate_port


logger = get_logger(__name__)


class TCPAdapter(BaseAdapter):
    """TCP/IP通信适配器"""

    def __init__(self, adapter_id: str = "tcp_adapter"):
        """初始化TCP适配器"""
        super().__init__(adapter_id, "TCP")
        self.host: Optional[str] = None
        self.port: int = 5025  # SCPI标准端口
        self.timeout: float = 5.0  # 默认5秒超时
        self.socket: Optional[socket.socket] = None
        self._lock = threading.RLock()

    def connect(self, **kwargs) -> bool:
        """
        连接TCP/IP设备

        Args:
            **kwargs: 连接参数，包括：
                - host: 设备IP地址或主机名（必需）
                - port: TCP端口（默认5025）
                - timeout: 超时时间（秒，默认5.0）

        Returns:
            是否连接成功
        """
        with self._lock:
            try:
                self.state = ConnectionState.CONNECTING
                self.connection_params = kwargs.copy()

                # 解析参数
                host = kwargs.get("host")
                if not host:
                    raise ValueError("必须提供host参数（IP地址或主机名）")

                port = kwargs.get("port", 5025)
                timeout = kwargs.get("timeout", 5.0)

                # 验证参数
                is_valid_ip, _ = validate_ip_address(host)
                if not is_valid_ip:
                    # 如果不是IP地址，可能是主机名，尝试解析
                    try:
                        import socket as sock
                        # 尝试解析主机名
                        sock.gethostbyname(host)
                    except socket.gaierror:
                        raise ValueError(f"无效的主机名或IP地址: {host}")

                if not validate_port(port):
                    raise ValueError(f"无效的端口号: {port}")

                self.host = host
                self.port = int(port)
                self.timeout = float(timeout)

                # 创建socket
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.timeout)

                # 建立连接
                logger.info(f"尝试TCP连接: {self.host}:{self.port}")
                self.socket.connect((self.host, self.port))

                # 测试连接（发送简单的查询命令）
                try:
                    test_command = b"*IDN?\n"
                    self.socket.send(test_command)
                    response = self.socket.recv(1024)
                    if response:
                        logger.debug(f"连接测试响应: {response.decode('utf-8', errors='ignore').strip()}")
                    else:
                        logger.warning("连接测试无响应，但连接已建立")
                except socket.timeout:
                    logger.warning("连接测试超时，但连接已建立")
                except Exception as e:
                    logger.warning(f"连接测试异常: {e}")

                self.state = ConnectionState.CONNECTED
                self.update_activity()
                logger.info(f"TCP连接成功: {self.host}:{self.port}")
                return True

            except socket.timeout as e:
                error_msg = f"TCP连接超时: {self.host}:{self.port} - {e}"
                self.set_error(error_msg)
                logger.error(error_msg)
                self._cleanup_socket()
                return False

            except ConnectionRefusedError as e:
                error_msg = f"TCP连接被拒绝: {self.host}:{self.port} - {e}"
                self.set_error(error_msg)
                logger.error(error_msg)
                self._cleanup_socket()
                return False

            except Exception as e:
                error_msg = f"TCP连接失败: {e}"
                self.set_error(error_msg)
                logger.error(error_msg)
                self._cleanup_socket()
                return False

    def disconnect(self) -> bool:
        """断开TCP连接"""
        with self._lock:
            try:
                if self.socket:
                    self.socket.shutdown(socket.SHUT_RDWR)
                    self.socket.close()

                self._cleanup_socket()
                self.state = ConnectionState.DISCONNECTED
                self.update_activity()
                logger.info("TCP连接已断开")
                return True

            except Exception as e:
                error_msg = f"TCP断开连接失败: {e}"
                self.set_error(error_msg)
                logger.error(error_msg)
                self._cleanup_socket()
                return False

    def send(self, data: bytes) -> int:
        """发送数据到TCP设备"""
        with self._lock:
            try:
                if not self.is_connected() or not self.socket:
                    raise RuntimeError("TCP适配器未连接")

                # 确保命令以换行符结束（SCPI标准）
                if not data.endswith(b'\n'):
                    data = data + b'\n'

                bytes_sent = self.socket.send(data)
                self.update_activity()
                logger.debug(f"TCP发送数据: {data[:50].decode('utf-8', errors='ignore').strip()}... ({bytes_sent}字节)")
                return bytes_sent

            except socket.timeout as e:
                error_msg = f"TCP发送数据超时: {e}"
                self.set_error(error_msg)
                logger.error(error_msg)
                return 0

            except Exception as e:
                error_msg = f"TCP发送数据失败: {e}"
                self.set_error(error_msg)
                logger.error(error_msg)
                return 0

    def receive(self, timeout: float = 1.0) -> bytes:
        """从TCP设备接收数据"""
        with self._lock:
            try:
                if not self.is_connected() or not self.socket:
                    raise RuntimeError("TCP适配器未连接")

                # 设置临时超时
                original_timeout = self.socket.gettimeout()
                self.socket.settimeout(timeout)

                try:
                    # 接收数据
                    data = b""
                    while True:
                        chunk = self.socket.recv(4096)
                        if not chunk:
                            break
                        data += chunk
                        # 如果数据以换行符结束，停止接收（SCPI响应通常以换行结束）
                        if data.endswith(b'\n'):
                            break
                finally:
                    # 恢复原始超时
                    self.socket.settimeout(original_timeout)

                self.update_activity()
                if data:
                    logger.debug(f"TCP接收数据: {data[:100].decode('utf-8', errors='ignore').strip()}... ({len(data)}字节)")
                return data

            except socket.timeout:
                # 超时不一定是错误，可能只是没有更多数据
                logger.debug(f"TCP接收超时（{timeout}秒）")
                return b""

            except Exception as e:
                error_msg = f"TCP接收数据失败: {e}"
                self.set_error(error_msg)
                logger.error(error_msg)
                return b""

    def query(self, data: bytes, timeout: float = 1.0) -> bytes:
        """TCP查询（发送命令并接收响应）"""
        with self._lock:
            try:
                # 发送数据
                bytes_sent = self.send(data)
                if bytes_sent == 0:
                    raise RuntimeError("发送数据失败")

                # 等待响应
                time.sleep(0.05)  # 给设备一些响应时间

                # 接收数据
                response = self.receive(timeout)

                return response

            except Exception as e:
                error_msg = f"TCP查询失败: {e}"
                self.set_error(error_msg)
                logger.error(error_msg)
                return b""

    def _cleanup_socket(self):
        """清理socket资源"""
        try:
            if self.socket:
                self.socket.close()
        except:
            pass
        finally:
            self.socket = None
            self.host = None
            self.port = 5025

    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        with self._lock:
            if not self.socket:
                return {}

            return {
                "host": self.host,
                "port": self.port,
                "timeout": self.timeout,
                "connected": self.is_connected(),
            }

    @classmethod
    def detect_available_ports(cls) -> List[Dict[str, Any]]:
        """
        检测可用的TCP设备

        注意：TCP设备检测通常需要扫描网络或使用发现协议。
        这里返回空列表，实际应用中可能需要实现设备发现逻辑。
        """
        logger.info("TCP设备检测需要网络扫描或手动配置")
        return []

    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        status = super().get_status()
        status.update({
            "host": self.host,
            "port": self.port,
            "timeout": self.timeout,
            "socket_connected": self.socket is not None,
        })
        return status

    def __del__(self):
        """析构函数，确保断开连接"""
        try:
            self.disconnect()
        except:
            pass