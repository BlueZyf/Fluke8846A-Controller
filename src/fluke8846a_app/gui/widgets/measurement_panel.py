"""
测量面板组件

显示当前测量值、历史记录和测量配置。
"""

from typing import List, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QHeaderView,
    QTextEdit, QSplitter, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor

from ...config.settings import AppSettings, MeasurementSettings
from ...core.measurements import MeasurementData
from ...utils.converters import format_value
from ...config.constants import *


class MeasurementPanel(QWidget):
    """测量面板组件"""

    # 自定义信号
    measurement_requested = Signal()
    configuration_changed = Signal(dict)

    def __init__(self, settings: AppSettings):
        """初始化测量面板

        Args:
            settings: 应用设置
        """
        super().__init__()
        self.settings = settings
        self.measurement_settings = settings.measurement
        self.current_measurements: List[MeasurementData] = []
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter, 1)

        # 当前测量显示区域
        current_widget = self._create_current_measurement_widget()
        splitter.addWidget(current_widget)

        # 历史记录区域
        history_widget = self._create_history_widget()
        splitter.addWidget(history_widget)

        # 配置区域
        config_widget = self._create_config_widget()
        splitter.addWidget(config_widget)

        # 设置分割器初始比例
        splitter.setSizes([200, 200, 150])

        # 测量控制按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        self.measure_button = QPushButton("单次测量")
        self.measure_button.setToolTip("执行单次测量")
        button_layout.addWidget(self.measure_button)

        self.continuous_button = QPushButton("连续测量")
        self.continuous_button.setCheckable(True)
        self.continuous_button.setToolTip("开始/停止连续测量")
        button_layout.addWidget(self.continuous_button)

        self.clear_button = QPushButton("清空数据")
        self.clear_button.setToolTip("清空所有测量数据")
        button_layout.addWidget(self.clear_button)

        button_layout.addStretch(1)

        main_layout.addLayout(button_layout)

    def _create_current_measurement_widget(self) -> QWidget:
        """创建当前测量显示部件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # 标题
        title_label = QLabel("当前测量")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 测量值显示
        value_widget = QWidget()
        value_layout = QHBoxLayout(value_widget)
        value_layout.setContentsMargins(0, 0, 0, 0)

        self.value_label = QLabel("---")
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("color: #2E7D32;")
        value_layout.addWidget(self.value_label, 1)

        self.unit_label = QLabel("V")
        unit_font = QFont()
        unit_font.setPointSize(16)
        self.unit_label.setFont(unit_font)
        self.unit_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        value_layout.addWidget(self.unit_label)

        layout.addWidget(value_widget, 1)

        # 测量信息
        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)

        self.function_label = QLabel("功能: DCV")
        self.range_label = QLabel("量程: AUTO")
        self.resolution_label = QLabel("分辨率: 6.5")

        info_layout.addWidget(self.function_label)
        info_layout.addWidget(self.range_label)
        info_layout.addWidget(self.resolution_label)
        info_layout.addStretch(1)

        layout.addWidget(info_widget)

        # 时间戳
        self.timestamp_label = QLabel("时间: --:--:--")
        self.timestamp_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.timestamp_label)

        return widget

    def _create_history_widget(self) -> QWidget:
        """创建历史记录部件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # 标题
        title_label = QLabel("历史记录")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["时间", "功能", "值", "单位"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setMaximumHeight(150)

        layout.addWidget(self.history_table, 1)

        return widget

    def _create_config_widget(self) -> QWidget:
        """创建设置部件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # 标题
        title_label = QLabel("测量设置")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 测量功能选择
        function_layout = QHBoxLayout()
        function_label = QLabel("功能:")
        self.function_combo = QComboBox()
        self.function_combo.addItems(MEASUREMENTS)
        self.function_combo.setCurrentText(self.measurement_settings.default_function)
        function_layout.addWidget(function_label)
        function_layout.addWidget(self.function_combo, 1)
        layout.addLayout(function_layout)

        # 量程选择
        range_layout = QHBoxLayout()
        range_label = QLabel("量程:")
        self.range_combo = QComboBox()
        self.range_combo.addItems(VOLTAGE_RANGES)
        self.range_combo.setCurrentText(self.measurement_settings.default_range)
        range_layout.addWidget(range_label)
        range_layout.addWidget(self.range_combo, 1)
        layout.addLayout(range_layout)

        # 分辨率选择
        resolution_layout = QHBoxLayout()
        resolution_label = QLabel("分辨率:")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(RESOLUTIONS)
        self.resolution_combo.setCurrentText(self.measurement_settings.default_resolution)
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo, 1)
        layout.addLayout(resolution_layout)

        # 采样设置
        sample_layout = QHBoxLayout()
        sample_label = QLabel("采样数:")
        self.sample_spin = QSpinBox()
        self.sample_spin.setRange(1, 1000)
        self.sample_spin.setValue(self.measurement_settings.sample_count)
        sample_layout.addWidget(sample_label)
        sample_layout.addWidget(self.sample_spin)
        layout.addLayout(sample_layout)

        # 间隔设置
        interval_layout = QHBoxLayout()
        interval_label = QLabel("间隔(s):")
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 60.0)
        self.interval_spin.setSingleStep(0.1)
        self.interval_spin.setValue(self.measurement_settings.measurement_interval)
        self.interval_spin.setDecimals(1)
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spin)
        layout.addLayout(interval_layout)

        # 自动记录
        self.auto_record_check = QCheckBox("自动记录")
        self.auto_record_check.setChecked(self.measurement_settings.auto_record)
        layout.addWidget(self.auto_record_check)

        return widget

    def _setup_connections(self):
        """设置信号连接"""
        # 按钮连接
        self.measure_button.clicked.connect(self.measurement_requested.emit)
        self.clear_button.clicked.connect(self.clear_measurements)

        # 配置变化连接
        self.function_combo.currentTextChanged.connect(self._on_config_changed)
        self.range_combo.currentTextChanged.connect(self._on_config_changed)
        self.resolution_combo.currentTextChanged.connect(self._on_config_changed)
        self.sample_spin.valueChanged.connect(self._on_config_changed)
        self.interval_spin.valueChanged.connect(self._on_config_changed)
        self.auto_record_check.stateChanged.connect(self._on_config_changed)

    def _on_config_changed(self):
        """配置变化处理"""
        config = {
            "function": self.function_combo.currentText(),
            "range": self.range_combo.currentText(),
            "resolution": self.resolution_combo.currentText(),
            "sample_count": self.sample_spin.value(),
            "interval": self.interval_spin.value(),
            "auto_record": self.auto_record_check.isChecked()
        }
        self.configuration_changed.emit(config)

    # 公共方法
    def add_measurement(self, measurement: MeasurementData):
        """添加测量数据

        Args:
            measurement: 测量数据
        """
        # 更新当前测量显示
        self.value_label.setText(format_value(measurement.value, precision=6))
        self.unit_label.setText(measurement.unit)

        # 更新测量信息
        self.function_label.setText(f"功能: {measurement.function}")
        if measurement.range:
            self.range_label.setText(f"量程: {measurement.range}")
        if measurement.resolution:
            self.resolution_label.setText(f"分辨率: {measurement.resolution}")

        # 更新时间戳
        self.timestamp_label.setText(f"时间: {measurement.timestamp.strftime('%H:%M:%S')}")

        # 添加到历史记录
        self.current_measurements.append(measurement)
        self._update_history_table()

        # 限制历史记录大小
        if len(self.current_measurements) > 100:
            self.current_measurements = self.current_measurements[-100:]

    def clear_measurements(self):
        """清空测量数据"""
        self.current_measurements.clear()
        self._update_history_table()

        # 重置当前测量显示
        self.value_label.setText("---")
        self.unit_label.setText("V")
        self.timestamp_label.setText("时间: --:--:--")

    def set_continuous_measuring(self, measuring: bool):
        """设置连续测量状态

        Args:
            measuring: 是否正在连续测量
        """
        if measuring:
            self.continuous_button.setText("停止测量")
            self.continuous_button.setChecked(True)
        else:
            self.continuous_button.setText("连续测量")
            self.continuous_button.setChecked(False)

    def set_enabled(self, enabled: bool):
        """设置组件启用状态

        Args:
            enabled: 是否启用
        """
        self.measure_button.setEnabled(enabled)
        self.continuous_button.setEnabled(enabled)
        self.clear_button.setEnabled(enabled)
        self.function_combo.setEnabled(enabled)
        self.range_combo.setEnabled(enabled)
        self.resolution_combo.setEnabled(enabled)
        self.sample_spin.setEnabled(enabled)
        self.interval_spin.setEnabled(enabled)
        self.auto_record_check.setEnabled(enabled)

    def refresh(self):
        """刷新组件"""
        # 重新加载设置
        self.settings.load()
        self.measurement_settings = self.settings.measurement

        # 更新控件值
        self.function_combo.setCurrentText(self.measurement_settings.default_function)
        self.range_combo.setCurrentText(self.measurement_settings.default_range)
        self.resolution_combo.setCurrentText(self.measurement_settings.default_resolution)
        self.sample_spin.setValue(self.measurement_settings.sample_count)
        self.interval_spin.setValue(self.measurement_settings.measurement_interval)
        self.auto_record_check.setChecked(self.measurement_settings.auto_record)

    def get_config(self) -> dict:
        """获取当前配置

        Returns:
            配置字典
        """
        return {
            "function": self.function_combo.currentText(),
            "range": self.range_combo.currentText(),
            "resolution": self.resolution_combo.currentText(),
            "sample_count": self.sample_spin.value(),
            "interval": self.interval_spin.value(),
            "auto_record": self.auto_record_check.isChecked()
        }

    def update_current_measurement(self, value: float, unit: str, function: str = None):
        """更新当前测量显示

        Args:
            value: 测量值
            unit: 单位
            function: 测量功能
        """
        self.value_label.setText(format_value(value, precision=6))
        self.unit_label.setText(unit)
        if function:
            self.function_label.setText(f"功能: {function}")

    # 私有方法
    def _update_history_table(self):
        """更新历史记录表格"""
        self.history_table.setRowCount(len(self.current_measurements))

        for i, measurement in enumerate(reversed(self.current_measurements)):
            # 时间
            time_item = QTableWidgetItem(measurement.timestamp.strftime("%H:%M:%S"))
            time_item.setTextAlignment(Qt.AlignCenter)

            # 功能
            function_item = QTableWidgetItem(measurement.function)
            function_item.setTextAlignment(Qt.AlignCenter)

            # 值
            value_item = QTableWidgetItem(format_value(measurement.value, precision=6))
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # 单位
            unit_item = QTableWidgetItem(measurement.unit)
            unit_item.setTextAlignment(Qt.AlignCenter)

            self.history_table.setItem(i, 0, time_item)
            self.history_table.setItem(i, 1, function_item)
            self.history_table.setItem(i, 2, value_item)
            self.history_table.setItem(i, 3, unit_item)

        # 滚动到最后一行
        if self.current_measurements:
            self.history_table.scrollToBottom()

    def _create_status_indicator(self) -> QLabel:
        """创建状态指示器"""
        indicator = QLabel("●")
        indicator.setFixedSize(12, 12)
        indicator.setStyleSheet("color: #F44336;")
        return indicator