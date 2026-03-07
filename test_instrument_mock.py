#!/usr/bin/env python
"""测试仪器类的模拟连接"""

import sys
sys.path.insert(0, '.')

from src.fluke8846a_app.core.instrument import Fluke8846AInstrument

def test_instrument_mock():
    print("测试Fluke8846AInstrument模拟连接...")

    # 创建仪器实例
    instrument = Fluke8846AInstrument("test_mock")

    # 连接模拟设备
    print("1. 连接模拟设备...")
    if instrument.connect_mock(adapter_id="test_instrument", base_value=3.0, noise_level=0.0005):
        print("   连接成功")
    else:
        print("   连接失败")
        return

    # 检查连接状态
    print(f"2. 连接状态: {instrument.connected}")
    print(f"   接口类型: {instrument.interface}")

    # 获取设备信息
    print("3. 获取设备信息...")
    status = instrument.get_status()
    print(f"   设备信息: {status.get('device_info')}")

    # 单次测量
    print("4. 执行单次测量...")
    measurement = instrument.measure_single()
    if measurement:
        print(f"   测量结果: {measurement.value} {measurement.unit}")
        print(f"   原始数据: {measurement}")
    else:
        print("   测量失败")

    # 断开连接
    print("5. 断开连接...")
    if instrument.disconnect():
        print("   断开成功")
    else:
        print("   断开失败")

    print("\n测试完成!")

if __name__ == "__main__":
    test_instrument_mock()