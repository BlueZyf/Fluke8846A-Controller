#!/usr/bin/env python
"""
FLUKE 8846A 模拟测试脚本

在没有实际硬件的情况下测试应用功能。
此脚本演示如何使用模拟适配器进行连接、配置和测量。

使用方法：
1. 确保虚拟环境已激活
2. 运行: python scripts/test_mock.py

注意：此脚本仅用于开发和测试目的。
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.fluke8846a_app.communication.mock_adapter import MockAdapter, MockDataGenerator
from src.fluke8846a_app.core.instrument import Fluke8846AInstrument, MeasurementData
from src.fluke8846a_app.config.settings import AppSettings
from src.fluke8846a_app.utils.logger import setup_logging


def test_mock_adapter_direct():
    """直接测试模拟适配器"""
    print("\n" + "="*60)
    print("测试 1: 直接使用模拟适配器")
    print("="*60)

    # 创建模拟适配器
    adapter = MockAdapter("test_mock")

    # 连接
    print("1. 连接模拟适配器...")
    if adapter.connect():
        print("   ✓ 连接成功")
    else:
        print("   ✗ 连接失败")
        return

    # 发送SCPI命令
    print("\n2. 发送SCPI命令...")

    # 设备识别
    print("   - 发送 *IDN? 命令...")
    adapter.send(b"*IDN?")
    response = adapter.receive()
    print(f"     响应: {response.decode('utf-8', errors='ignore')}")

    # 配置直流电压测量
    print("   - 发送 :CONF:VOLT:DC 10,0.001 命令...")
    adapter.send(b":CONF:VOLT:DC 10,0.001")
    adapter.receive()  # 无响应命令

    # 读取测量值
    print("   - 发送 :READ? 命令...")
    adapter.send(b":READ?")
    response = adapter.receive()
    print(f"     测量值: {response.decode('utf-8', errors='ignore')}")

    # 断开连接
    print("\n3. 断开连接...")
    adapter.disconnect()
    print("   ✓ 已断开")


def test_mock_with_instrument():
    """使用模拟适配器测试仪器控制类"""
    print("\n" + "="*60)
    print("测试 2: 使用Fluke8846AInstrument类（通过模拟适配器）")
    print("="*60)

    print("注意：需要修改Fluke8846AInstrument类以支持模拟适配器")
    print("以下是概念演示...")

    # 创建仪器实例
    instrument = Fluke8846AInstrument("fluke8846a_simulator")

    # 由于Fluke8846AInstrument当前不支持直接使用MockAdapter，
    # 这里演示如何修改该类以支持模拟模式

    # 以下是建议的修改方法：
    # 1. 在Fluke8846AInstrument类中添加connect_mock()方法
    # 2. 或者在connect_serial()等方法中检测模拟端口

    print("\n建议的模拟连接方法：")
    print("1. 添加connect_mock()方法到Fluke8846AInstrument类")
    print("2. 在连接对话框中添加'模拟'选项卡")
    print("3. 或者修改现有连接方法支持模拟端口（如'MOCK::SIMULATOR::INSTR'）")

    return instrument


def test_gui_with_mock():
    """测试GUI与模拟适配器的集成"""
    print("\n" + "="*60)
    print("测试 3: GUI集成测试（概念）")
    print("="*60)

    print("要使GUI支持模拟适配器，需要：")
    print("\n1. 修改连接对话框 (connection_dialog.py):")
    print("   - 添加'模拟'选项卡")
    print("   - 添加模拟设备配置选项")

    print("\n2. 修改仪器控制类 (instrument.py):")
    print("   - 添加connect_mock()方法")
    print("   - 或者修改connect_visa()支持模拟资源字符串")

    print("\n3. 修改VISA管理器 (visa_manager.py):")
    print("   - 添加模拟资源支持")
    print("   - 或者创建单独的模拟管理器")

    print("\n4. 临时解决方案（用于快速测试）：")
    print("   - 手动创建MockAdapter实例")
    print("   - 直接调用测量方法，绕过GUI")


def create_mock_connection_example():
    """创建模拟连接示例代码"""
    print("\n" + "="*60)
    print("示例代码: 如何扩展当前代码支持模拟适配器")
    print("="*60)

    example_code = '''
# 方法1: 在Fluke8846AInstrument类中添加connect_mock方法
def connect_mock(self, **kwargs) -> bool:
    """连接模拟设备"""
    with self._lock:
        try:
            from ..communication.mock_adapter import MockAdapter

            logger.info("连接模拟设备")

            # 创建模拟适配器
            self.adapter = MockAdapter(f"mock_{self.instrument_id}")
            self.interface = "MOCK"

            # 建立连接
            if not self.adapter.connect(**kwargs):
                return False

            self.connected = True

            # 获取设备信息
            self._update_device_info()

            logger.info("模拟设备连接成功")
            return True

        except Exception as e:
            logger.error(f"模拟设备连接失败: {e}")
            self.connected = False
            self.adapter = None
            return False

# 方法2: 修改connect_visa以支持模拟资源
def connect_visa(self, resource_name: str, timeout: int = 5000) -> bool:
    """连接VISA设备（支持模拟资源）"""
    with self._lock:
        try:
            # 检查是否是模拟资源
            if resource_name.startswith("MOCK::"):
                from ..communication.mock_adapter import MockAdapter
                self.adapter = MockAdapter(f"mock_{self.instrument_id}")
                self.interface = "MOCK"
            else:
                # 原有VISA连接代码...
                pass

            # 其余代码...
    '''

    print(example_code)


def quick_mock_test():
    """快速模拟测试（不修改现有代码）"""
    print("\n" + "="*60)
    print("快速测试: 使用模拟适配器进行简单测量")
    print("="*60)

    # 创建模拟适配器
    adapter = MockAdapter("quick_mock")

    # 连接
    print("1. 连接模拟设备...")
    adapter.connect()

    # 设置设备信息
    adapter.set_measurement_mode("DCV", "10V", "6.5")

    # 模拟一系列测量
    print("\n2. 模拟测量序列:")
    functions = ["DCV", "ACV", "OHM", "DCI", "FREQ"]

    for i, func in enumerate(functions, 1):
        adapter.set_measurement_mode(func)

        # 发送读取命令
        adapter.send(b":READ?")
        response = adapter.receive()

        value = response.decode('utf-8', errors='ignore').strip()
        print(f"   {i}. {func}: {value}")

        time.sleep(0.5)

    # 断开连接
    print("\n3. 断开模拟设备...")
    adapter.disconnect()

    print("\n✓ 快速测试完成")


def main():
    """主函数"""
    print("FLUKE 8846A 模拟测试脚本")
    print("版本: 1.0.0")
    print("用途: 在没有实际硬件的情况下测试应用功能")
    print("-"*60)

    # 设置日志
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir)

    try:
        # 执行测试
        test_mock_adapter_direct()
        time.sleep(1)

        test_mock_with_instrument()
        time.sleep(1)

        quick_mock_test()
        time.sleep(1)

        create_mock_connection_example()
        time.sleep(1)

        test_gui_with_mock()

        print("\n" + "="*60)
        print("模拟测试完成!")
        print("="*60)
        print("\n下一步建议:")
        print("1. 如果要通过GUI测试，需要修改连接对话框添加模拟接口")
        print("2. 如果要通过代码测试，可以直接使用MockAdapter类")
        print("3. 参考上面的示例代码扩展现有类支持模拟模式")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())