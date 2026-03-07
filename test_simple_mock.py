#!/usr/bin/env python
"""简单的模拟适配器测试"""

import sys
sys.path.insert(0, '.')

from src.fluke8846a_app.communication.mock_adapter import MockAdapter

def test_simple():
    print("测试模拟适配器...")

    # 创建适配器
    adapter = MockAdapter("test_simple")

    # 连接
    print("1. 连接...")
    if adapter.connect(base_value=5.0, noise_level=0.001, response_delay=100):
        print("   连接成功")
    else:
        print("   连接失败")
        return

    # 发送命令
    print("2. 发送*IDN?命令...")
    adapter.send(b"*IDN?")
    response = adapter.receive()
    print(f"   响应: {response.decode('utf-8')}")

    # 发送测量命令
    print("3. 发送:READ?命令...")
    adapter.send(b":READ?")
    response = adapter.receive()
    print(f"   测量值: {response.decode('utf-8')}")

    # 断开连接
    print("4. 断开连接...")
    adapter.disconnect()
    print("   断开成功")

    print("\n测试完成!")

if __name__ == "__main__":
    test_simple()