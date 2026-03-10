#!/usr/bin/env python
"""测试TCP/IP连接集成"""

import sys
import os
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("测试TCP/IP连接集成")
print("=" * 50)
print("说明：此脚本用于测试通过TCP/IP连接FLUKE 8846A仪器")
print("请确保仪器已通过网线连接到网络，并已配置好IP地址")
print("=" * 50)

# 配置TCP连接参数
tcp_params = {
    "host": "192.168.1.100",  # 请修改为实际的仪器IP地址
    "port": 5025,             # SCPI标准TCP端口
    "timeout": 5.0            # 超时时间（秒）
}

print(f"连接参数: {tcp_params}")
print("提示：如果仪器IP地址不同，请修改host参数")
print()

try:
    # 导入仪器类
    from src.fluke8846a_app.core.instrument import Fluke8846AInstrument

    # 创建仪器实例
    instrument = Fluke8846AInstrument("test_tcp_integration")
    print(f"创建的仪器: {instrument.instrument_id}")

    # 连接TCP设备
    print(f"连接TCP设备 {tcp_params['host']}:{tcp_params['port']}...")

    success = instrument.connect_tcp(
        host=tcp_params["host"],
        port=tcp_params["port"],
        timeout=tcp_params["timeout"]
    )

    print(f"连接结果: {success}")
    print(f"连接状态: {instrument.connected}")
    print(f"接口类型: {instrument.interface}")

    if success:
        # 测试通信
        print("测试通信...")
        status = instrument.get_status()
        print(f"仪器状态: {status}")

        # 获取设备信息
        print("获取设备信息...")
        device_info = instrument.identify()
        if device_info:
            print(f"设备识别: {device_info}")
        else:
            print("设备识别失败")

        # 重置仪器
        print("重置仪器...")
        if instrument.reset():
            print("仪器重置成功")
        else:
            print("仪器重置失败")

        # 配置测量（直流电压）
        print("配置直流电压测量...")
        from src.fluke8846a_app.config.constants import MEASUREMENT_DCV, RANGE_AUTO, RESOLUTION_6_5
        if instrument.configure_measurement(
            function=MEASUREMENT_DCV,
            range_val=RANGE_AUTO,
            resolution=RESOLUTION_6_5
        ):
            print("测量配置成功")
        else:
            print("测量配置失败")

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
        print("连接失败，请检查：")
        print("1. 仪器电源是否打开")
        print("2. 仪器是否已连接到网络")
        print("3. IP地址是否正确")
        print("4. 防火墙是否允许端口5025")
        print("5. 仪器网络配置是否正确")

except ImportError as e:
    print(f"导入错误: {e}")
    import traceback
    traceback.print_exc()
except KeyboardInterrupt:
    print("\n用户中断测试")
except Exception as e:
    print(f"其他错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("测试完成")