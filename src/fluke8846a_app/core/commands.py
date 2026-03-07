"""
FLUKE 8846A SCPI命令定义

根据FLUKE 8846A编程手册定义的SCPI命令。
"""

# 通用命令
CMD_IDENTIFY = "*IDN?"  # 识别仪器
CMD_RESET = "*RST"  # 重置仪器
CMD_CLEAR_STATUS = "*CLS"  # 清除状态
CMD_SELF_TEST = "*TST?"  # 自检

# 系统命令
CMD_SYSTEM_ERROR = "SYST:ERR?"  # 读取系统错误
CMD_SYSTEM_VERSION = "SYST:VERS?"  # 读取系统版本
CMD_SYSTEM_LOCAL = "SYST:LOC"  # 返回本地控制
CMD_SYSTEM_REMOTE = "SYST:REM"  # 进入远程控制

# 测量命令
# 直流电压
CMD_MEASURE_DCV = "MEAS:VOLT:DC?"  # 测量直流电压
CMD_CONFIGURE_DCV = "CONF:VOLT:DC"  # 配置直流电压测量
CMD_CONFIGURE_DCV_AUTO = "CONF:VOLT:DC AUTO"  # 配置直流电压自动量程

# 交流电压
CMD_MEASURE_ACV = "MEAS:VOLT:AC?"  # 测量交流电压
CMD_CONFIGURE_ACV = "CONF:VOLT:AC"  # 配置交流电压测量
CMD_CONFIGURE_ACV_AUTO = "CONF:VOLT:AC AUTO"  # 配置交流电压自动量程

# 直流电流
CMD_MEASURE_DCI = "MEAS:CURR:DC?"  # 测量直流电流
CMD_CONFIGURE_DCI = "CONF:CURR:DC"  # 配置直流电流测量
CMD_CONFIGURE_DCI_AUTO = "CONF:CURR:DC AUTO"  # 配置直流电流自动量程

# 交流电流
CMD_MEASURE_ACI = "MEAS:CURR:AC?"  # 测量交流电流
CMD_CONFIGURE_ACI = "CONF:CURR:AC"  # 配置交流电流测量
CMD_CONFIGURE_ACI_AUTO = "CONF:CURR:AC AUTO"  # 配置交流电流自动量程

# 电阻
CMD_MEASURE_OHM = "MEAS:RES?"  # 测量电阻
CMD_CONFIGURE_OHM = "CONF:RES"  # 配置电阻测量
CMD_CONFIGURE_OHM_AUTO = "CONF:RES AUTO"  # 配置电阻自动量程
CMD_CONFIGURE_OHM_2W = "CONF:RES"  # 2线制电阻测量
CMD_CONFIGURE_OHM_4W = "CONF:FRES"  # 4线制电阻测量

# 频率
CMD_MEASURE_FREQ = "MEAS:FREQ?"  # 测量频率
CMD_CONFIGURE_FREQ = "CONF:FREQ"  # 配置频率测量

# 温度
CMD_MEASURE_TEMP = "MEAS:TEMP?"  # 测量温度
CMD_CONFIGURE_TEMP = "CONF:TEMP"  # 配置温度测量

# 电容
CMD_MEASURE_CAP = "MEAS:CAP?"  # 测量电容
CMD_CONFIGURE_CAP = "CONF:CAP"  # 配置电容测量

# 二极管测试
CMD_MEASURE_DIODE = "MEAS:DIOD?"  # 测量二极管
CMD_CONFIGURE_DIODE = "CONF:DIOD"  # 配置二极管测试

# 连续性测试
CMD_MEASURE_CONT = "MEAS:CONT?"  # 连续性测试
CMD_CONFIGURE_CONT = "CONF:CONT"  # 配置连续性测试

# 配置命令
CMD_SET_RANGE = "RANG"  # 设置量程（后跟数值）
CMD_SET_RANGE_AUTO = "RANG:AUTO ON"  # 设置自动量程
CMD_SET_RANGE_MANUAL = "RANG:AUTO OFF"  # 设置手动量程

CMD_SET_RESOLUTION = "RES"  # 设置分辨率（后跟数值）
CMD_SET_NPLC = "NPLC"  # 设置NPLC值（后跟数值）

CMD_SET_TRIGGER_SOURCE = "TRIG:SOUR"  # 设置触发源
CMD_SET_TRIGGER_COUNT = "TRIG:COUN"  # 设置触发计数
CMD_SET_TRIGGER_DELAY = "TRIG:DEL"  # 设置触发延迟

CMD_INITIATE = "INIT"  # 启动测量
CMD_FETCH = "FETCH?"  # 读取测量结果

# 显示命令
CMD_DISPLAY_TEXT = "DISP:TEXT"  # 设置显示文本
CMD_DISPLAY_CLEAR = "DISP:TEXT:CLE"  # 清除显示文本
CMD_DISPLAY_ENABLE = "DISP ON"  # 启用显示
CMD_DISPLAY_DISABLE = "DISP OFF"  # 禁用显示

# 校准命令（谨慎使用）
CMD_CALIBRATION_STATE = "CAL:STAT?"  # 查询校准状态
CMD_CALIBRATION_UNLOCK = "CAL:UNLOCK"  # 解锁校准
CMD_CALIBRATION_LOCK = "CAL:LOCK"  # 锁定校准

# 量程值定义
RANGE_VALUES = {
    "100mV": 0.1,
    "1V": 1,
    "10V": 10,
    "100V": 100,
    "1000V": 1000,
    "AUTO": None,
}

# 分辨率值定义
RESOLUTION_VALUES = {
    "3.5": 3.5,  # 3.5位
    "4.5": 4.5,  # 4.5位
    "5.5": 5.5,  # 5.5位
    "6.5": 6.5,  # 6.5位
}

# 命令构建函数
def build_configure_command(function: str, range_val: str = None, resolution: str = None) -> str:
    """
    构建配置命令

    Args:
        function: 测量功能
        range_val: 量程
        resolution: 分辨率

    Returns:
        配置命令字符串
    """
    # 基础命令映射
    base_commands = {
        "DCV": CMD_CONFIGURE_DCV,
        "ACV": CMD_CONFIGURE_ACV,
        "DCI": CMD_CONFIGURE_DCI,
        "ACI": CMD_CONFIGURE_ACI,
        "OHM": CMD_CONFIGURE_OHM,
        "FREQ": CMD_CONFIGURE_FREQ,
    }

    if function not in base_commands:
        raise ValueError(f"不支持的测量功能: {function}")

    command = base_commands[function]

    # 添加量程
    if range_val:
        if range_val == "AUTO":
            command += " AUTO"
        elif range_val in RANGE_VALUES:
            command += f" {RANGE_VALUES[range_val]}"
        else:
            # 尝试作为数值处理
            try:
                float(range_val)
                command += f" {range_val}"
            except ValueError:
                raise ValueError(f"无效的量程值: {range_val}")

    # 注意：分辨率参数可能需要单独的RES命令
    return command


def build_measure_command(function: str) -> str:
    """
    构建测量命令

    Args:
        function: 测量功能

    Returns:
        测量命令字符串
    """
    command_map = {
        "DCV": CMD_MEASURE_DCV,
        "ACV": CMD_MEASURE_ACV,
        "DCI": CMD_MEASURE_DCI,
        "ACI": CMD_MEASURE_ACI,
        "OHM": CMD_MEASURE_OHM,
        "FREQ": CMD_MEASURE_FREQ,
        "TEMP": CMD_MEASURE_TEMP,
        "CAP": CMD_MEASURE_CAP,
        "DIOD": CMD_MEASURE_DIODE,
        "CONT": CMD_MEASURE_CONT,
    }

    if function not in command_map:
        raise ValueError(f"不支持的测量功能: {function}")

    return command_map[function]


def parse_measurement_response(response: str, function: str) -> tuple:
    """
    解析测量响应

    Args:
        response: 仪器响应字符串
        function: 测量功能

    Returns:
        (值, 单位)
    """
    if not response:
        return None, None

    response = response.strip()

    try:
        # 尝试解析为浮点数
        value = float(response)
        # 根据功能确定单位
        units = {
            "DCV": "V",
            "ACV": "V",
            "DCI": "A",
            "ACI": "A",
            "OHM": "Ω",
            "FREQ": "Hz",
            "TEMP": "°C",
            "CAP": "F",
        }
        unit = units.get(function, "")
        return value, unit
    except ValueError:
        # 如果无法解析为浮点数，尝试其他格式
        # 例如 "1.234E-3 V"
        parts = response.split()
        if len(parts) >= 2:
            try:
                value = float(parts[0])
                unit = parts[1]
                return value, unit
            except ValueError:
                pass

        return None, None