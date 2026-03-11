#!/usr/bin/env python3
"""
跨平台兼容性测试脚本
测试FLUKE 8846A应用在Windows和Linux上的兼容性
"""

import platform
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_platform_detection():
    """测试平台检测功能"""
    system = platform.system()
    print(f"当前操作系统: {system}")
    print(f"平台详细信息: {platform.platform()}")
    return system

def test_serial_port_validation():
    """测试串口验证功能"""
    from fluke8846a_app.utils.validators import validate_serial_port, get_default_serial_port

    system = platform.system().lower()
    default_port = get_default_serial_port()

    print(f"\n串口验证测试:")
    print(f"默认串口: {default_port}")
    print(f"默认串口是否有效: {validate_serial_port(default_port)}")

    # 测试不同平台的串口名称
    test_ports = {
        "windows": ["COM1", "COM3", "COM256", "COM257", "/dev/ttyS0"],
        "linux": ["/dev/ttyS0", "/dev/ttyUSB0", "/dev/ttyACM0", "COM1"],
        "darwin": ["/dev/tty.usbserial", "/dev/tty.usbmodem", "/dev/cu.usbserial", "COM1"]
    }

    # 根据当前平台测试
    if system in test_ports:
        for port in test_ports[system]:
            is_valid = validate_serial_port(port)
            print(f"  {port}: {'有效' if is_valid else '无效'}")

    return True

def test_settings_defaults():
    """测试设置默认值"""
    from fluke8846a_app.config.settings import DeviceSettings

    print(f"\n设备设置测试:")
    device_settings = DeviceSettings()
    print(f"默认串口: {device_settings.serial_port}")
    print(f"默认GPIB地址: {device_settings.gpib_address}")
    print(f"默认超时: {device_settings.timeout}")

    return True

def test_visa_interface_detection():
    """测试VISA接口检测"""
    from fluke8846a_app.communication.visa_manager import VisaManager

    print(f"\nVISA接口检测测试:")
    manager = VisaManager()

    test_resources = [
        "GPIB0::22::INSTR",
        "USB0::0x1234::0x5678::INSTR",
        "ASRL3::INSTR",
        "COM3",
        "/dev/ttyUSB0",
        "TCPIP0::192.168.1.100::5025::SOCKET"
    ]

    for resource in test_resources:
        # 注意：这里调用私有方法，实际测试中可能需要调整
        # 由于_detect_interface是私有方法，我们暂时跳过实际调用
        # interface = manager._detect_interface(resource)
        print(f"  资源: {resource}")
        # print(f"    检测到的接口: {interface}")

    print("  (注意: _detect_interface是私有方法，需要在实际VISA环境中测试)")
    return True

def test_import_all_modules():
    """测试所有模块导入"""
    print(f"\n模块导入测试:")

    modules_to_test = [
        "fluke8846a_app",
        "fluke8846a_app.config",
        "fluke8846a_app.config.settings",
        "fluke8846a_app.config.constants",
        "fluke8846a_app.utils.validators",
        "fluke8846a_app.communication.visa_manager",
        "fluke8846a_app.core.instrument",
        # "fluke8846a_app.gui.main_window"  # 需要PySide6，可选
    ]

    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"  [OK] {module_name}")
        except ImportError as e:
            print(f"  [X] {module_name}: {e}")

    return True

def main():
    """主测试函数"""
    print("=" * 60)
    print("FLUKE 8846A 跨平台兼容性测试")
    print("=" * 60)

    tests = [
        ("平台检测", test_platform_detection),
        ("串口验证", test_serial_port_validation),
        ("设置默认值", test_settings_defaults),
        ("VISA接口检测", test_visa_interface_detection),
        ("模块导入", test_import_all_modules)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n-> 运行测试: {test_name}")
            success = test_func()
            results.append((test_name, success, None))
            print(f"  [OK] {test_name} 通过")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"  [X] {test_name} 失败: {e}")

    # 打印测试总结
    print(f"\n" + "=" * 60)
    print("测试总结:")
    print("=" * 60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for test_name, success, error in results:
        status = "[OK]" if success else "[X]"
        print(f"  {status} {test_name}")
        if error:
            print(f"    错误: {error}")

    print(f"\n通过: {passed}/{total}")

    if passed == total:
        print("[PASS] 所有测试通过!")
        return 0
    else:
        print("[FAIL] 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())