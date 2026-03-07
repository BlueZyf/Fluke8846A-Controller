"""
USB通信适配器

通过USB接口与FLUKE 8846A进行通信。
需要PyUSB库支持。
"""

from typing import Dict, Any
from .base_adapter import BaseAdapter, ConnectionState


class USBAdapter(BaseAdapter):
    """USB通信适配器"""

    def __init__(self, adapter_id: str = "usb_adapter"):
        """初始化USB适配器"""
        super().__init__(adapter_id, "USB")
        self.device = None
        self.endpoint_in = None
        self.endpoint_out = None

    def connect(self, **kwargs) -> bool:
        """
        建立USB连接

        Args:
            **kwargs: 连接参数
                vendor_id: USB厂商ID
                product_id: USB产品ID
                serial_number: 设备序列号（可选）

        Returns:
            是否连接成功
        """
        try:
            import usb.core
            import usb.util

            vendor_id = kwargs.get("vendor_id", 0x0000)
            product_id = kwargs.get("product_id", 0x0000)
            serial_number = kwargs.get("serial_number")

            # 查找设备
            device = usb.core.find(
                idVendor=vendor_id,
                idProduct=product_id,
                serial_number=serial_number
            )

            if device is None:
                self.set_error("未找到USB设备")
                return False

            # 配置设备
            if device.is_kernel_driver_active(0):
                device.detach_kernel_driver(0)

            device.set_configuration()

            # 获取端点
            cfg = device.get_active_configuration()
            intf = cfg[(0,0)]

            # 查找输入和输出端点
            endpoint_in = None
            endpoint_out = None

            for ep in intf:
                if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN:
                    endpoint_in = ep
                else:
                    endpoint_out = ep

            if endpoint_in is None or endpoint_out is None:
                self.set_error("无法找到USB端点")
                return False

            self.device = device
            self.endpoint_in = endpoint_in
            self.endpoint_out = endpoint_out
            self.state = ConnectionState.CONNECTED
            self.connection_params = kwargs.copy()
            self.update_activity()

            return True

        except ImportError:
            self.set_error("PyUSB库未安装")
            return False
        except Exception as e:
            self.set_error(f"USB连接失败: {str(e)}")
            return False

    def disconnect(self) -> bool:
        """断开USB连接"""
        try:
            if self.device:
                import usb.util
                usb.util.dispose_resources(self.device)
                self.device = None

            self.endpoint_in = None
            self.endpoint_out = None
            self.state = ConnectionState.DISCONNECTED
            self.connection_params = {}
            self.clear_error()

            return True

        except Exception as e:
            self.set_error(f"USB断开连接失败: {str(e)}")
            return False

    def send(self, data: bytes) -> int:
        """发送数据"""
        if not self.is_connected():
            self.set_error("设备未连接")
            return 0

        try:
            sent_bytes = self.endpoint_out.write(data)
            self.update_activity()
            return sent_bytes

        except Exception as e:
            self.set_error(f"USB发送失败: {str(e)}")
            return 0

    def receive(self, timeout: float = 1.0) -> bytes:
        """接收数据"""
        if not self.is_connected():
            self.set_error("设备未连接")
            return b""

        try:
            # 将超时时间转换为毫秒
            timeout_ms = int(timeout * 1000)
            data = self.endpoint_in.read(self.endpoint_in.wMaxPacketSize, timeout_ms)
            self.update_activity()
            return bytes(data)

        except Exception as e:
            self.set_error(f"USB接收失败: {str(e)}")
            return b""

    @classmethod
    def detect_available_ports(cls) -> list:
        """检测可用的USB设备"""
        try:
            import usb.core
            devices = usb.core.find(find_all=True)

            ports = []
            for device in devices:
                try:
                    port_info = {
                        "vendor_id": hex(device.idVendor),
                        "product_id": hex(device.idProduct),
                        "manufacturer": usb.util.get_string(device, device.iManufacturer) if device.iManufacturer else "Unknown",
                        "product": usb.util.get_string(device, device.iProduct) if device.iProduct else "Unknown",
                        "serial_number": usb.util.get_string(device, device.iSerialNumber) if device.iSerialNumber else None,
                        "bus": device.bus,
                        "address": device.address,
                    }
                    ports.append(port_info)
                except:
                    continue

            return ports

        except ImportError:
            return []
        except Exception:
            return []