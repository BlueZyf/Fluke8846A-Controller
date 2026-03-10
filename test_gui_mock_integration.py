#!/usr/bin/env python
"""测试GUI模拟连接集成"""

import sys
import os
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 模拟GUI传递的参数（从connection_dialog.get_connection_params()获取）
mock_params = {
    "interface": "MOCK",
    "adapter_id": "fluke8846a_simulator",
    "mode": "简单模拟",  # 从UI获取，但可能不被使用
    "base_value": 5.0,
    "noise_level": 0.001,
    "response_delay": 50,
    "timeout": 5000  # 默认值
}

print("测试GUI模拟连接集成")
print(f"参数: {mock_params}")

try:
    # 导入仪器类
    from src.fluke8846a_app.core.instrument import Fluke8846AInstrument

    # 创建仪器实例
    instrument = Fluke8846AInstrument("test_gui_integration")
    print(f"创建的仪器: {instrument.instrument_id}")

    # 连接模拟设备 - 使用与GUI相同的方式调用
    print("连接模拟设备...")

    # 注意：main_window.py中只传递了部分参数
    success = instrument.connect_mock(
        adapter_id=mock_params["adapter_id"],
        base_value=mock_params["base_value"],
        noise_level=mock_params["noise_level"],
        response_delay=mock_params["response_delay"]
    )

    print(f"连接结果: {success}")
    print(f"连接状态: {instrument.connected}")
    print(f"接口类型: {instrument.interface}")

    if success:
        # 测试通信
        print("测试通信...")
        status = instrument.get_status()
        print(f"仪器状态: {status}")

        # 单次测量
        print("执行单次测量...")
        measurement = instrument.measure_single()
        if measurement:
            print(f"测量结果: {measurement}")
        else:
            print("测量失败")

        # 断开连接
        print("断开连接...")
        instrument.disconnect()
        print(f"断开后的连接状态: {instrument.connected}")
    else:
        print("连接失败，检查日志获取详细信息")

except ImportError as e:
    print(f"导入错误: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"其他错误: {e}")
    import traceback
    traceback.print_exc()