"""
模拟通信适配器

用于在没有实际硬件连接的情况下测试应用功能。
模拟FLUKE 8846A的响应行为，生成随机测量数据。
"""

import time
import random
from typing import Dict, Any, Optional, List
from .base_adapter import BaseAdapter, ConnectionState


class MockAdapter(BaseAdapter):
    """模拟通信适配器"""

    def __init__(self, adapter_id: str = "mock_adapter"):
        """初始化模拟适配器"""
        super().__init__(adapter_id, "MOCK")
        self._response_buffer = b""
        self._data_generator = MockDataGenerator()
        self._device_info = {
            "manufacturer": "FLUKE",
            "model": "8846A",
            "serial_number": "SIM001",
            "firmware_version": "1.0.0",
            "device_type": "Digital Multimeter"
        }
        self._measurement_mode = "DCV"  # 直流电压
        self._measurement_range = "AUTO"
        self._measurement_resolution = "6.5"
        self._response_delay = 0.05  # 默认50ms

    def connect(self, **kwargs) -> bool:
        """
        建立模拟连接

        Args:
            **kwargs: 连接参数（模拟模式忽略大部分参数）
                - base_value: 基准值
                - noise_level: 噪声水平
                - response_delay: 响应延迟（毫秒）

        Returns:
            总是返回True（模拟连接成功）
        """
        try:
            self.state = ConnectionState.CONNECTING
            self.connection_params = kwargs.copy()

            # 应用参数到数据生成器
            base_value = kwargs.get("base_value")
            if base_value is not None:
                # 为所有测量功能设置基准值
                for func in ["DCV", "ACV", "DCI", "ACI", "OHM", "FREQ"]:
                    self._data_generator.set_base_value(func, base_value)

            noise_level = kwargs.get("noise_level")
            if noise_level is not None:
                self._data_generator.set_noise_level(noise_level)

            response_delay = kwargs.get("response_delay")
            if response_delay is not None:
                # 存储响应延迟参数，在receive方法中使用
                self._response_delay = response_delay / 1000.0  # 转换为秒
            else:
                self._response_delay = 0.05  # 默认50ms

            # 模拟连接延迟
            time.sleep(0.5)

            self.state = ConnectionState.CONNECTED
            self.update_activity()

            print("模拟适配器：连接成功（模拟模式）")
            print(f"设备信息：{self._device_info}")
            print(f"连接参数：基准值={base_value}, 噪声水平={noise_level}, 响应延迟={response_delay}ms")

            return True

        except Exception as e:
            self.set_error(f"模拟连接失败: {e}")
            return False

    def disconnect(self) -> bool:
        """断开模拟连接"""
        try:
            self.state = ConnectionState.DISCONNECTED
            self.connection_params = {}
            self._response_buffer = b""
            self.clear_error()

            print("模拟适配器：连接已断开")
            return True

        except Exception as e:
            self.set_error(f"模拟断开连接失败: {e}")
            return False

    def send(self, data: bytes) -> int:
        """
        发送数据（模拟）

        解析SCPI命令并准备相应的模拟响应。

        Args:
            data: 要发送的数据（SCPI命令）

        Returns:
            发送的字节数
        """
        if not self.is_connected():
            self.set_error("设备未连接")
            return 0

        try:
            command = data.decode('utf-8', errors='ignore').strip()
            print(f"模拟适配器：收到命令: {command}")

            # 处理常见SCPI命令
            response = self._process_scpi_command(command)

            # 将响应存入缓冲区
            self._response_buffer = response.encode('utf-8') if response else b""

            self.update_activity()
            return len(data)

        except Exception as e:
            self.set_error(f"模拟发送失败: {e}")
            return 0

    def receive(self, timeout: float = 1.0) -> bytes:
        """
        接收数据（模拟）

        返回之前通过send()命令准备的响应。

        Args:
            timeout: 超时时间（秒，模拟模式忽略）

        Returns:
            响应数据
        """
        if not self.is_connected():
            self.set_error("设备未连接")
            return b""

        try:
            # 模拟接收延迟
            time.sleep(self._response_delay)

            response = self._response_buffer
            self._response_buffer = b""  # 清空缓冲区

            if response:
                print(f"模拟适配器：发送响应: {response.decode('utf-8', errors='ignore')[:50]}...")
            else:
                # 如果没有特定响应，返回随机测量数据
                measurement = self._data_generator.generate_measurement(
                    function=self._measurement_mode,
                    range_val=self._measurement_range,
                    resolution=self._measurement_resolution
                )
                response = measurement.encode('utf-8')
                print(f"模拟适配器：返回测量数据: {measurement}")

            self.update_activity()
            return response

        except Exception as e:
            self.set_error(f"模拟接收失败: {e}")
            return b""

    def _process_scpi_command(self, command: str) -> Optional[str]:
        """
        处理SCPI命令并生成模拟响应

        Args:
            command: SCPI命令字符串

        Returns:
            响应字符串，None表示无响应
        """
        # 转换为大写并去除空白
        cmd = command.upper().strip()

        # 识别和响应常见SCPI命令
        if cmd == "*IDN?":
            # 设备识别
            return f"FLUKE,8846A,{self._device_info['serial_number']},V{self._device_info['firmware_version']}"

        elif cmd == "*RST":
            # 重置设备
            self._measurement_mode = "DCV"
            self._measurement_range = "AUTO"
            self._measurement_resolution = "6.5"
            return None

        elif cmd.startswith(":CONF:"):
            # 配置测量
            # 示例：:CONF:VOLT:DC 10,0.001
            parts = cmd.split()
            if len(parts) >= 2:
                measurement_part = parts[1]
                if "VOLT:DC" in measurement_part:
                    self._measurement_mode = "DCV"
                elif "VOLT:AC" in measurement_part:
                    self._measurement_mode = "ACV"
                elif "CURR:DC" in measurement_part:
                    self._measurement_mode = "DCI"
                elif "CURR:AC" in measurement_part:
                    self._measurement_mode = "ACI"
                elif "RES" in measurement_part:
                    self._measurement_mode = "OHM"
                elif "FREQ" in measurement_part:
                    self._measurement_mode = "FREQ"
            return None

        elif cmd == ":READ?":
            # 读取测量值
            measurement = self._data_generator.generate_measurement(
                function=self._measurement_mode,
                range_val=self._measurement_range,
                resolution=self._measurement_resolution
            )
            return measurement

        elif cmd.startswith("MEAS:"):
            # 测量命令，如MEAS:VOLT:DC?、MEAS:VOLT:AC?等
            # 根据命令确定测量模式
            if "VOLT:DC" in cmd:
                self._measurement_mode = "DCV"
            elif "VOLT:AC" in cmd:
                self._measurement_mode = "ACV"
            elif "CURR:DC" in cmd:
                self._measurement_mode = "DCI"
            elif "CURR:AC" in cmd:
                self._measurement_mode = "ACI"
            elif "RES" in cmd:
                self._measurement_mode = "OHM"
            elif "FREQ" in cmd:
                self._measurement_mode = "FREQ"

            # 返回测量值
            measurement = self._data_generator.generate_measurement(
                function=self._measurement_mode,
                range_val=self._measurement_range,
                resolution=self._measurement_resolution
            )
            return measurement

        elif cmd.startswith(":SENSE:"):
            # 传感器/测量设置
            if ":VOLT:DC:RANGE" in cmd:
                # 设置直流电压量程
                self._measurement_range = self._extract_value(cmd)
            elif ":VOLT:DC:RESOLUTION" in cmd:
                # 设置分辨率
                self._measurement_resolution = self._extract_value(cmd)
            return None

        elif cmd == "*OPC?":
            # 操作完成查询
            return "1"

        elif cmd == ":SYST:ERR?":
            # 系统错误查询
            return '0,"No error"'

        else:
            # 未知命令，返回通用确认
            print(f"模拟适配器：未知命令 '{cmd}'，返回通用确认")
            return None

    def _extract_value(self, command: str) -> str:
        """从SCPI命令中提取数值"""
        parts = command.split()
        if len(parts) > 0:
            last_part = parts[-1]
            # 移除可能的前缀或后缀
            return last_part.replace('"', '').replace("'", '')
        return "AUTO"

    def set_measurement_mode(self, mode: str, range_val: str = "AUTO", resolution: str = "6.5"):
        """设置测量模式（用于直接控制）"""
        self._measurement_mode = mode
        self._measurement_range = range_val
        self._measurement_resolution = resolution
        print(f"模拟适配器：测量模式设置为 {mode}, 量程 {range_val}, 分辨率 {resolution}")

    def get_device_info(self) -> Dict[str, str]:
        """获取设备信息"""
        return self._device_info.copy()

    @classmethod
    def detect_available_ports(cls) -> List[Dict[str, Any]]:
        """检测可用的模拟端口（总是返回一个模拟端口）"""
        return [{
            "device": "MOCK::SIMULATOR::INSTR",
            "description": "FLUKE 8846A 模拟器",
            "manufacturer": "FLUKE",
            "model": "8846A",
            "serial_number": "SIM001",
            "interface": "MOCK"
        }]


class MockDataGenerator:
    """模拟数据生成器"""

    def __init__(self):
        self._base_values = {
            "DCV": 5.123456,      # 直流电压：约5.1V
            "ACV": 3.456789,      # 交流电压：约3.5V
            "DCI": 0.012345,      # 直流电流：约12.3mA
            "ACI": 0.008765,      # 交流电流：约8.8mA
            "OHM": 1000.123,      # 电阻：约1kΩ
            "FREQ": 1000.0        # 频率：约1kHz
        }
        self._noise_level = 0.001  # 噪声水平
        self._trend_direction = 1  # 趋势方向
        self._trend_counter = 0

    def generate_measurement(self, function: str, range_val: str = "AUTO", resolution: str = "6.5") -> str:
        """
        生成模拟测量数据

        Args:
            function: 测量功能 (DCV, ACV, DCI, ACI, OHM, FREQ)
            range_val: 量程
            resolution: 分辨率

        Returns:
            格式化后的测量值字符串
        """
        # 获取基准值
        base_value = self._base_values.get(function, 1.0)

        # 添加一些变化（模拟真实测量）
        self._trend_counter += 1
        if self._trend_counter >= 10:
            self._trend_direction *= -1
            self._trend_counter = 0

        # 计算变化
        noise = random.uniform(-self._noise_level, self._noise_level)
        trend = self._trend_direction * 0.0001 * base_value
        drift = 0.00001 * base_value * random.random()

        # 应用变化
        value = base_value + noise + trend + drift

        # 根据分辨率格式化
        if resolution == "3.5":
            # 3.5位：最大1999，精度较低
            value = round(value, 3)
        elif resolution == "4.5":
            # 4.5位：最大19999
            value = round(value, 4)
        elif resolution == "5.5":
            # 5.5位：最大199999
            value = round(value, 5)
        else:  # 6.5位
            value = round(value, 6)

        # 确保值在合理范围内
        value = max(0.000001, value)  # 避免零或负值

        # 根据量程调整（简化处理）
        if range_val != "AUTO":
            try:
                # 解析量程，如"10V" -> 10.0
                if "MV" in range_val.upper():
                    range_num = float(range_val.upper().replace("MV", "")) / 1000
                elif "V" in range_val.upper():
                    range_num = float(range_val.upper().replace("V", ""))
                elif "MA" in range_val.upper():
                    range_num = float(range_val.upper().replace("MA", "")) / 1000
                elif "A" in range_val.upper():
                    range_num = float(range_val.upper().replace("A", ""))
                elif "KOHM" in range_val.upper():
                    range_num = float(range_val.upper().replace("KOHM", "")) * 1000
                elif "MOHM" in range_val.upper():
                    range_num = float(range_val.upper().replace("MOHM", "")) * 1000000
                elif "OHM" in range_val.upper():
                    range_num = float(range_val.upper().replace("OHM", ""))
                else:
                    range_num = 10.0

                # 确保值不超过量程的90%
                max_value = range_num * 0.9
                if value > max_value:
                    value = max_value * random.uniform(0.7, 0.9)
            except:
                pass

        # 返回格式化字符串
        return f"{value:.6f}"

    def set_base_value(self, function: str, value: float):
        """设置基准值"""
        self._base_values[function] = value

    def set_noise_level(self, level: float):
        """设置噪声水平"""
        self._noise_level = max(0.0, min(1.0, level))