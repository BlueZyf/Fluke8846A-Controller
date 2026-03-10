# FLUKE 8846A 控制应用

一个用于控制FLUKE 8846A数字万用表的跨平台上位机应用。

## 功能特性

### 第一阶段：基本控制测试
- [ ] 仪器连接和识别（GPIB/USB/RS-232）
- [ ] 设备信息显示（型号、序列号、固件版本）
- [ ] 直流电压测量（DCV）
- [ ] 交流电压测量（ACV）
- [ ] 电阻测量（Ω）
- [ ] 电流测量（DCI/ACI）
- [ ] 基本数据记录和显示

### 第二阶段：高级功能（规划中）
- 连续测量模式
- 数据图表显示
- 测量配置保存/加载
- 自动化测试序列
- 报告生成

## 系统要求

- Python 3.8 或更高版本
- PyVISA 和 PyVISA-py
- PySide6 (Qt for Python)
- 可选：NI-VISA 或 Keysight VISA 运行时（用于GPIB支持）

## 安装

### 系统要求
- Python 3.8 或更高版本
- 推荐使用虚拟环境（venv 或 conda）
- 支持的操作系统：Windows 10/11, Linux, macOS
- 可选硬件：FLUKE 8846A 数字万用表（用于实际连接测试）

### 1. 克隆仓库
```bash
git clone <repository-url>
cd 05_Cmd_8846A
```

### 2. 创建并激活虚拟环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. 安装核心依赖
```bash
# 安装项目依赖（包含 PySide6、PyVISA、numpy 等）
pip install -r requirements.txt

# 或者使用可编辑模式安装，便于开发
pip install -e .
```

### 4. 安装平台特定依赖（可选）
```bash
# 串口支持（如果使用 RS-232 接口）
pip install pyserial

# USB 支持（如果使用 USB 接口）
pip install pyusb

# 系统监控功能（用于状态栏显示 CPU/内存使用率）
pip install psutil
```

### 5. 验证安装
```bash
# 检查 Python 版本
python --version

# 检查依赖是否安装成功
python -c "import PySide6, pyqtgraph, pyvisa; print('所有核心依赖导入成功')"

# 运行简单测试（如果有测试用例）
pytest src/fluke8846a_app/tests/ -v
```

### 6. 安装 VISA 运行时（可选）
如需通过 GPIB 或 USB-VISA 连接仪器，需要安装 VISA 运行时：
- **Windows**: 安装 [NI-VISA](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html) 或 [Keysight VISA](https://www.keysight.com/us/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html)
- **Linux**: 安装 `linux-gpib` 和 `pyvisa-py`
- **macOS**: 使用 `brew install libusb` 并配置 PyVISA-py

### 7. 运行应用
```bash
# 确保虚拟环境已激活
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 运行主程序
python -m fluke8846a_app.main
```

### 故障排除
#### 常见问题 1: 模块导入错误
```
ModuleNotFoundError: No module named 'fluke8846a_app'
```
**解决方案**:
- 确保已使用 `pip install -e .` 安装项目
- 检查是否在项目根目录（`05_Cmd_8846A`）下运行命令
- 确认虚拟环境已激活

#### 常见问题 2: PySide6 相关错误
```
This application failed to start because no Qt platform plugin could be initialized.
```
**解决方案**:
- Windows: 确保安装了 [Visual C++ Redistributable](https://aka.ms/vs/16/release/vc_redist.x64.exe)
- Linux: 安装 Qt 运行时 `sudo apt-get install libxcb-xinerama0`
- 设置环境变量：`export QT_QPA_PLATFORM=windows`（Windows）或 `export QT_QPA_PLATFORM=xcb`（Linux）

#### 常见问题 3: VISA 连接错误
```
VisaIOError: VI_ERROR_RSRC_NFOUND
```
**解决方案**:
- 确认 VISA 运行时已安装
- 检查仪器是否开机并正确连接
- 使用 `pyvisa-info` 命令查看可用资源

#### 常见问题 4: 状态栏显示异常
```
'PySide6.QtWidgets.QMainWindow.setStatusBar' called with wrong argument types
```
**解决方案**:
- 已修复，确保使用最新代码
- 如果问题仍然存在，重新安装依赖：`pip install --upgrade PySide6`

#### 获取更多帮助
如遇到其他问题，请：
1. 查看 `data/logs/app.log` 日志文件
2. 在项目 Issues 页面提交问题
3. 联系开发者提供详细错误信息

## 使用说明

### 运行应用
确保虚拟环境已激活，然后在项目根目录执行：

```bash
python -m fluke8846a_app.main
```

应用启动后，将显示主窗口界面。

### 图形界面概述
FLUKE 8846A 控制应用提供完整的图形用户界面，包含以下主要区域：

1. **菜单栏** - 文件、测量、视图、设置、帮助菜单
2. **工具栏** - 常用功能快捷按钮（连接、测量、导出等）
3. **左侧面板** - 测量面板（实时数据显示、历史记录）和控制面板（仪器功能设置）
4. **右侧面板** - 实时数据图表（基于 pyqtgraph）
5. **状态栏** - 连接状态、测量状态、设备信息、系统资源监控

### 基本操作流程
#### 步骤 1: 连接仪器
1. 点击工具栏的 **"连接"** 按钮或菜单栏 **文件 → 连接设备**
2. 在连接对话框中选择通信接口：
   - **GPIB**: 输入 GPIB 地址（例如 `GPIB0::22::INSTR`）
   - **USB**: 选择 USB 设备（需要 VISA 运行时或 PyUSB）
   - **RS-232**: 选择串口、波特率等参数
3. 点击 **连接** 按钮，状态栏会显示连接状态

#### 步骤 2: 配置测量
1. 在控制面板选择测量功能：
   - 直流电压（DCV）
   - 交流电压（ACV）
   - 电阻（Ω）
   - 直流电流（DCI）
   - 交流电流（ACI）
   - 频率（FREQ）
2. 设置量程和分辨率（可选）
3. 配置测量参数（如滤波、触发等）

#### 步骤 3: 执行测量
- **单次测量**: 点击 **单次测量** 按钮或按 **F5** 键
- **连续测量**: 点击 **开始连续测量** 按钮或按 **F6** 键
- **停止测量**: 点击 **停止** 按钮或按 **F7** 键

测量数据将实时显示在测量面板和图表面板中。

#### 步骤 4: 数据管理
- **查看历史**: 测量面板显示所有历史测量记录
- **清空数据**: 点击 **清空数据** 按钮或按 **Ctrl+D**
- **导出数据**: 点击 **文件 → 导出数据...** 或按 **Ctrl+E**，支持 CSV、Excel、JSON 格式

#### 步骤 5: 断开连接
完成测量后，点击 **断开** 按钮或菜单栏 **文件 → 断开连接**，安全断开仪器连接。

### 高级功能
- **主题切换**: 支持浅色/深色主题，在设置中切换
- **多语言**: 支持中文/英文界面（需配置语言文件）
- **自动化测试**: 可编写脚本通过 `core/instrument.py` 进行自动化控制
- **远程监控**: 通过网络接口远程访问测量数据（规划中）

### 快捷键参考
| 快捷键 | 功能 |
|--------|------|
| Ctrl+C | 连接设备 |
| Ctrl+D | 清空数据 |
| Ctrl+E | 导出数据 |
| Ctrl+Q | 退出应用 |
| F5 | 单次测量 |
| F6 | 开始连续测量 |
| F7 | 停止连续测量 |
| Ctrl++ | 放大图表 |
| Ctrl+- | 缩小图表 |
| Ctrl+0 | 重置图表缩放 |

### 注意事项
1. 首次使用前，请确保仪器固件为最新版本
2. 进行高精度测量时，建议预热仪器 30 分钟
3. 连续测量时注意数据量，避免内存占用过高
4. 导出数据前建议先停止测量

## 项目结构

```
05_Cmd_8846A/
├── src/fluke8846a_app/          # 主应用代码
│   ├── __init__.py              # 包定义
│   ├── main.py                  # 应用入口点
│   ├── app.py                   # 主应用类
│   ├── config/                  # 配置管理
│   │   ├── __init__.py
│   │   ├── constants.py         # 常量定义
│   │   ├── paths.py             # 路径配置
│   │   └── settings.py          # 应用设置
│   ├── core/                    # 核心仪器控制逻辑
│   │   ├── __init__.py
│   │   ├── instrument.py        # 仪器控制主类
│   │   ├── measurements.py      # 测量数据模型
│   │   └── commands.py          # SCPI命令定义
│   ├── communication/           # 通信模块
│   │   ├── __init__.py
│   │   ├── base_adapter.py      # 适配器基类
│   │   ├── visa_manager.py      # VISA通信管理
│   │   ├── gpib_adapter.py      # GPIB适配器
│   │   ├── serial_adapter.py    # 串口适配器
│   │   ├── tcp_adapter.py       # TCP/IP适配器
│   │   ├── usb_adapter.py       # USB适配器
│   │   ├── mock_adapter.py      # 模拟通信适配器
│   │   └── connection_pool.py   # 连接池
│   ├── gui/                     # 图形用户界面
│   │   ├── __init__.py
│   │   ├── main_window.py       # 主窗口
│   │   ├── widgets/             # 自定义控件
│   │   │   ├── measurement_panel.py
│   │   │   ├── control_panel.py
│   │   │   ├── plot_widget.py
│   │   │   └── status_bar.py
│   │   ├── dialogs/             # 对话框
│   │   │   ├── connection_dialog.py
│   │   │   ├── settings_dialog.py
│   │   │   └── about_dialog.py
│   │   └── styles/              # 样式表
│   │       ├── light.qss
│   │       └── dark.qss
│   ├── models/                  # 数据模型
│   │   ├── __init__.py
│   │   └── database.py          # 数据库模型
│   ├── utils/                   # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py            # 日志配置
│   │   ├── validators.py        # 数据验证
│   │   ├── converters.py        # 数据转换
│   │   └── helpers.py           # 辅助函数
│   └── tests/                   # 单元测试
│       ├── __init__.py
│       ├── test_instrument.py
│       └── fixtures/            # 测试夹具
├── docs/                        # 文档
│   ├── user_manual.md           # 用户手册
│   └── developer_guide.md       # 开发者指南
├── scripts/                     # 实用脚本
│   ├── setup_visa.py            # VISA配置脚本
│   └── backup_data.py           # 数据备份脚本
├── examples/                    # 示例代码
│   ├── basic_measurement.py     # 基础测量示例
│   └── automation_test.py       # 自动化测试示例
├── data/                        # 数据存储
│   ├── logs/                    # 日志文件
│   ├── measurements/            # 测量数据
│   └── config/                  # 配置文件
├── resources/                   # 资源文件
│   ├── icons/                   # 图标资源
│   └── translations/            # 多语言文件
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git忽略文件
├── LICENSE                      # 许可证文件
├── pyproject.toml               # 项目配置
├── requirements.txt             # Python依赖
└── README.md                    # 项目说明文档
```

## 开发

### 开发环境设置
```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black src/
flake8 src/
```

### 代码结构
- `src/fluke8846a_app/core/` - 核心仪器控制逻辑
- `src/fluke8846a_app/communication/` - 通信模块（VISA、GPIB、USB、串口、TCP、模拟）
- `src/fluke8846a_app/gui/` - 用户界面组件
- `src/fluke8846a_app/models/` - 数据模型
- `src/fluke8846a_app/utils/` - 工具函数

## 通信接口支持

| 接口类型 | 支持状态 | 备注 |
|---------|---------|------|
| GPIB    | ✓       | 需要VISA运行时 |
| USB     | ✓       | 支持VISA-USB和PyUSB |
| RS-232  | ✓       | 通过PySerial支持 |
| TCP/IP  | ✓       | 通过以太网连接（端口5025） |
| 模拟连接 | ✓       | 无硬件测试模式 |

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 支持

如有问题或建议，请提交 Issue 或联系开发者。

我已经完成了FLUKE 8846A上位机GUI的剩余编程。以下是完成的工作总结：

✅ 已完成的任务
1. GUI主窗口系统
main_window.py - 完整的Qt主窗口，包含菜单栏、工具栏、状态栏
实现了仪器连接、测量控制、数据管理等功能集成
支持响应式布局和主题切换
2. 核心GUI组件
测量面板 (measurement_panel.py) - 实时数据显示、历史记录、测量配置
控制面板 (control_panel.py) - 仪器控制功能（重置、自检、校准）
绘图组件 (plot_widget.py) - 基于pyqtgraph的实时数据图表
状态栏 (status_bar.py) - 连接状态、测量状态、系统信息显示
3. 对话框系统
连接对话框 (connection_dialog.py) - GPIB/USB/串口连接配置
设置对话框 (settings_dialog.py) - 应用设置管理
关于对话框 (about_dialog.py) - 应用信息显示
4. 样式和主题
light.qss - 浅色主题样式表
dark.qss - 深色主题样式表
完整的Qt控件样式定制
🎯 实现的功能特性
多接口支持 - GPIB、USB、RS-232全接口连接
测量功能 - 直流电压(DCV)、交流电压(ACV)、电阻(Ω)、电流(DCI/ACI)、频率测量
数据可视化 - 实时图表显示、历史数据表格、统计信息
仪器控制 - 重置、自检、校准、配置管理
数据管理 - 自动记录、导出、备份、清空
用户界面 - 多主题、多语言、可定制的界面布局
🏗️ 项目结构现状

05_Cmd_8846A/
├── src/fluke8846a_app/
│   ├── core/              # 仪器控制核心（已存在）
│   ├── communication/     # 通信模块（已存在）
│   ├── config/           # 配置管理（已存在）
│   ├── utils/            # 工具函数（已存在）
│   └── gui/              # ✅ 新增完整GUI模块
│       ├── main_window.py
│       ├── widgets/      # 所有UI组件
│       ├── dialogs/      # 所有对话框
│       └── styles/       # 主题样式表
└── requirements.txt      # 依赖配置
🚀 运行准备
要运行完整的应用，需要：


# 1. 激活虚拟环境（Windows）
venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行应用
python -m fluke8846a_app.main
📝 下一步建议
安装依赖测试 - 确保PySide6、pyqtgraph等GUI依赖安装正确
连接实际设备 - 测试与FLUKE 8846A的实际通信
功能验证 - 逐一测试各项测量和控制功能
UI优化 - 根据实际使用体验调整界面布局
项目现在已具备完整的上位机功能，可以进行FLUKE 8846A仪器的完整控制和数据采集。您需要我帮忙进行依赖安装或运行测试吗？