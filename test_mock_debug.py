#!/usr/bin/env python
"""调试模拟连接问题"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 尝试导入
try:
    from src.fluke8846a_app.communication.mock_adapter import MockAdapter
    print("成功导入 MockAdapter")

    # 测试适配器连接
    adapter = MockAdapter("test_debug")
    print(f"创建的适配器: {adapter}")

    # 连接参数（模拟GUI传递的参数）
    params = {
        "base_value": 5.0,
        "noise_level": 0.001,
        "response_delay": 50
    }

    print(f"连接参数: {params}")
    result = adapter.connect(**params)
    print(f"连接结果: {result}")
    print(f"连接状态: {adapter.state}")

    if result:
        # 测试通信
        print("测试通信...")
        adapter.send(b"*IDN?")
        response = adapter.receive()
        print(f"*IDN? 响应: {response}")

        adapter.send(b":READ?")
        response = adapter.receive()
        print(f":READ? 响应: {response}")

        # 断开连接
        adapter.disconnect()
        print("断开连接成功")

except ImportError as e:
    print(f"导入错误: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"其他错误: {e}")
    import traceback
    traceback.print_exc()