"""
状态栏组件

显示应用状态信息：连接状态、测量状态、设备信息等。
"""

from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QStatusBar, QHBoxLayout, QLabel, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from ...core.measurements import MeasurementData


class StatusBar(QStatusBar):
    """状态栏组件"""

    def __init__(self):
        """初始化状态栏"""
        super().__init__()
        self._setup_ui()
        self._setup_timers()

    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(10)

        # 连接状态
        self.connection_status = QLabel("未连接")
        self.connection_status.setFixedWidth(80)
        self._update_connection_indicator(False)
        layout.addWidget(self.connection_status)

        layout.addSpacing(5)

        # 测量状态
        self.measurement_status = QLabel("就绪")
        self.measurement_status.setFixedWidth(200)
        layout.addWidget(self.measurement_status)

        layout.addSpacing(5)

        # 设备信息
        self.device_info = QLabel("设备: 未连接")
        self.device_info.setFixedWidth(200)
        layout.addWidget(self.device_info)

        layout.addSpacing(5)

        # 最后测量
        self.last_measurement = QLabel("最后测量: --")
        self.last_measurement.setFixedWidth(200)
        layout.addWidget(self.last_measurement)

        layout.addSpacing(5)

        # 数据点数
        self.data_count = QLabel("数据: 0")
        self.data_count.setFixedWidth(80)
        layout.addWidget(self.data_count)

        layout.addSpacing(5)

        # 内存使用
        self.memory_usage = QLabel("内存: --")
        self.memory_usage.setFixedWidth(100)
        layout.addWidget(self.memory_usage)

        layout.addSpacing(5)

        # CPU使用
        self.cpu_usage = QLabel("CPU: --")
        self.cpu_usage.setFixedWidth(80)
        layout.addWidget(self.cpu_usage)

        layout.addSpacing(5)

        # 进度条（用于长时间操作）
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        layout.addStretch(1)

        # 时间显示
        self.time_label = QLabel()
        self.time_label.setFixedWidth(100)
        self.time_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.time_label)

    def _setup_timers(self):
        """设置定时器"""
        # 时间更新定时器
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(1000)  # 1秒更新一次

        # 系统信息更新定时器
        self.system_timer = QTimer()
        self.system_timer.timeout.connect(self._update_system_info)
        self.system_timer.start(5000)  # 5秒更新一次

        # 初始更新
        self._update_time()
        self._update_system_info()

    def _update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(current_time)

    def _update_system_info(self):
        """更新系统信息"""
        try:
            import psutil
            # 内存使用
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.memory_usage.setText(f"内存: {memory_percent}%")

            # CPU使用
            cpu_percent = psutil.cpu_percent(interval=None)
            self.cpu_usage.setText(f"CPU: {cpu_percent:.1f}%")

        except ImportError:
            # psutil未安装
            self.memory_usage.setText("内存: N/A")
            self.cpu_usage.setText("CPU: N/A")

    def _update_connection_indicator(self, connected: bool):
        """更新连接状态指示器

        Args:
            connected: 是否已连接
        """
        if connected:
            self.connection_status.setText("● 已连接")
            self.connection_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.connection_status.setText("○ 未连接")
            self.connection_status.setStyleSheet("color: #F44336;")

    # 公共方法
    def update_connection_status(self, connected: bool, message: str = ""):
        """更新连接状态

        Args:
            connected: 是否已连接
            message: 附加消息
        """
        self._update_connection_indicator(connected)

        if message:
            status_text = "已连接" if connected else "未连接"
            self.connection_status.setToolTip(f"{status_text}: {message}")
        else:
            self.connection_status.setToolTip("")

    def update_measurement_status(self, status: str):
        """更新测量状态

        Args:
            status: 状态文本
        """
        self.measurement_status.setText(status)
        self.measurement_status.setToolTip(status)

        # 根据状态设置颜色
        if "错误" in status or "失败" in status:
            self.measurement_status.setStyleSheet("color: #F44336;")
        elif "测量" in status or "运行" in status:
            self.measurement_status.setStyleSheet("color: #2196F3;")
        else:
            self.measurement_status.setStyleSheet("color: #4CAF50;")

    def update_device_info(self, info: str):
        """更新设备信息

        Args:
            info: 设备信息文本
        """
        self.device_info.setText(f"设备: {info}")
        self.device_info.setToolTip(info)

    def update_last_measurement(self, measurement: Optional[MeasurementData] = None):
        """更新最后测量信息

        Args:
            measurement: 测量数据，为None时清空显示
        """
        if measurement:
            time_str = measurement.timestamp.strftime("%H:%M:%S")
            value_str = f"{measurement.value:.6f}" if measurement.value < 10000 else f"{measurement.value:.2e}"
            text = f"最后: {time_str} {value_str} {measurement.unit}"
            self.last_measurement.setText(text)
            self.last_measurement.setToolTip(f"{measurement.function}: {measurement.value} {measurement.unit}")
        else:
            self.last_measurement.setText("最后测量: --")
            self.last_measurement.setToolTip("")

    def update_data_count(self, count: int):
        """更新数据点数

        Args:
            count: 数据点数
        """
        self.data_count.setText(f"数据: {count}")
        self.data_count.setToolTip(f"当前数据点数: {count}")

    def show_progress(self, message: str = "", maximum: int = 100):
        """显示进度条

        Args:
            message: 进度消息
            maximum: 最大值
        """
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(0)

        if message:
            self.progress_bar.setFormat(f"{message} %p%")
        else:
            self.progress_bar.setFormat("%p%")

    def update_progress(self, value: int):
        """更新进度

        Args:
            value: 进度值
        """
        self.progress_bar.setValue(value)

    def hide_progress(self):
        """隐藏进度条"""
        self.progress_bar.setVisible(False)

    def show_message(self, message: str, timeout: int = 3000):
        """显示临时消息

        Args:
            message: 消息文本
            timeout: 显示时间（毫秒）
        """
        # 保存当前状态
        old_text = self.measurement_status.text()
        old_tooltip = self.measurement_status.toolTip()

        # 显示消息
        self.measurement_status.setText(message)
        self.measurement_status.setStyleSheet("color: #FF9800;")

        # 定时恢复
        QTimer.singleShot(timeout, lambda: self._restore_status(old_text, old_tooltip))

    def _restore_status(self, text: str, tooltip: str):
        """恢复状态

        Args:
            text: 原文本
            tooltip: 原工具提示
        """
        self.measurement_status.setText(text)
        self.measurement_status.setToolTip(tooltip)

        # 恢复颜色
        if "错误" in text or "失败" in text:
            self.measurement_status.setStyleSheet("color: #F44336;")
        elif "测量" in text or "运行" in text:
            self.measurement_status.setStyleSheet("color: #2196F3;")
        else:
            self.measurement_status.setStyleSheet("color: #4CAF50;")

    def clear(self):
        """清空状态"""
        self.update_connection_status(False)
        self.update_measurement_status("就绪")
        self.update_device_info("未连接")
        self.update_last_measurement(None)
        self.update_data_count(0)
        self.hide_progress()

    def set_style(self, style: str):
        """设置样式

        Args:
            style: 样式类型（"light"或"dark"）
        """
        if style == "dark":
            self.setStyleSheet("""
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border-top: 1px solid #444444;
                }
                QLabel {
                    color: #ffffff;
                }
                QProgressBar {
                    border: 1px solid #444444;
                    border-radius: 3px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 3px;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #f0f0f0;
                    color: #333333;
                    border-top: 1px solid #cccccc;
                }
                QLabel {
                    color: #333333;
                }
                QProgressBar {
                    border: 1px solid #cccccc;
                    border-radius: 3px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 3px;
                }
            """)