#!/usr/bin/env python
"""最小化模拟连接测试 - 绕过包导入问题"""

import sys
import os
import importlib

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

try:
    # 直接导入模块，避免触发__init__.py
    mock_adapter_spec = importlib.util.spec_from_file_location(
        "mock_adapter",
        os.path.join(os.path.dirname(__file__), "src", "fluke8846a_app", "communication", "mock_adapter.py")
    )
    mock_adapter_module = importlib.util.module_from_spec(mock_adapter_spec)
    sys.modules["mock_adapter"] = mock_adapter_module
    mock_adapter_spec.loader.exec_module(mock_adapter_module)

    from mock_adapter import MockAdapter

    print("成功导入 MockAdapter")

    # 测试适配器
    adapter = MockAdapter("test_minimal")
    print(f"适配器状态: {adapter.state}")

    # 连接
    result = adapter.connect(base_value=5.0, noise_level=0.001, response_delay=50)
    print(f"连接结果: {result}")
    print(f"连接后状态: {adapter.state}")

    if result:
        # 测试通信
        print("测试通信...")
        adapter.send(b"*IDN?")
        response = adapter.receive()
        print(f"*IDN? 响应: {response}")

        if response:
            print(f"解码响应: {response.decode('utf-8', errors='ignore')}")

        # 断开
        adapter.disconnect()
        print("断开连接成功")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()