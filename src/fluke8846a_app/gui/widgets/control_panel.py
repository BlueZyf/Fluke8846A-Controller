"""
控制面板组件

提供仪器控制功能：重置、自检、校准、配置等。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from ...config.settings import AppSettings
from ...config.constants import *


class ControlPanel(QWidget):
    """控制面板组件"""

    # 自定义信号
    function_changed = Signal(str)
    range_changed = Signal(str)
    resolution_changed = Signal(str)
    reset_requested = Signal()
    self_test_requested = Signal()
    calibration_requested = Signal()

    def __init__(self, settings: AppSettings):
        """初始化控制面板

        Args:
            settings: 应用设置
        """
        super().__init__()
        self.settings = settings
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        # 仪器控制组
        control_group = QGroupBox("仪器控制")
        control_layout = QVBoxLayout(control_group)
        control_layout.setSpacing(5)

        # 控制按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        self.reset_button = QPushButton("重置")
        self.reset_button.setToolTip("重置仪器到默认状态")
        self.reset_button.setEnabled(False)
        button_layout.addWidget(self.reset_button)

        self.self_test_button = QPushButton("自检")
        self.self_test_button.setToolTip("执行仪器自检")
        self.self_test_button.setEnabled(False)
        button_layout.addWidget(self.self_test_button)

        self.calibrate_button = QPushButton("校准")
        self.calibrate_button.setToolTip("校准仪器")
        self.calibrate_button.setEnabled(False)
        button_layout.addWidget(self.calibrate_button)

        button_layout.addStretch(1)
        control_layout.addLayout(button_layout)

        # 状态显示
        status_layout = QHBoxLayout()
        status_label = QLabel("状态:")
        self.status_label = QLabel("未连接")
        self.status_label.setStyleSheet("color: #F44336;")
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch(1)
        control_layout.addLayout(status_layout)

        main_layout.addWidget(control_group)

        # 测量配置组
        config_group = QGroupBox("测量配置")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(5)

        # 测量功能选择
        function_layout = QHBoxLayout()
        function_label = QLabel("测量功能:")
        self.function_combo = QComboBox()
        self.function_combo.addItems(MEASUREMENTS)
        self.function_combo.setCurrentText(self.settings.measurement.default_function)
        self.function_combo.setEnabled(False)
        function_layout.addWidget(function_label)
        function_layout.addWidget(self.function_combo, 1)
        config_layout.addLayout(function_layout)

        # 量程选择
        range_layout = QHBoxLayout()
        range_label = QLabel("量程:")
        self.range_combo = QComboBox()
        self.range_combo.addItems(VOLTAGE_RANGES)
        self.range_combo.setCurrentText(self.settings.measurement.default_range)
        self.range_combo.setEnabled(False)
        range_layout.addWidget(range_label)
        range_layout.addWidget(self.range_combo, 1)
        config_layout.addLayout(range_layout)

        # 分辨率选择
        resolution_layout = QHBoxLayout()
        resolution_label = QLabel("分辨率:")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(RESOLUTIONS)
        self.resolution_combo.setCurrentText(self.settings.measurement.default_resolution)
        self.resolution_combo.setEnabled(False)
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo, 1)
        config_layout.addLayout(resolution_layout)

        # 触发设置
        trigger_layout = QHBoxLayout()
        trigger_label = QLabel("触发源:")
        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(["内部", "外部", "总线", "手动"])
        self.trigger_combo.setEnabled(False)
        trigger_layout.addWidget(trigger_label)
        trigger_layout.addWidget(self.trigger_combo, 1)
        config_layout.addLayout(trigger_layout)

        # NPLC设置
        nplc_layout = QHBoxLayout()
        nplc_label = QLabel("NPLC:")
        self.nplc_spin = QDoubleSpinBox()
        self.nplc_spin.setRange(0.01, 10.0)
        self.nplc_spin.setSingleStep(0.01)
        self.nplc_spin.setValue(1.0)
        self.nplc_spin.setDecimals(2)
        self.nplc_spin.setEnabled(False)
        nplc_layout.addWidget(nplc_label)
        nplc_layout.addWidget(self.nplc_spin)
        config_layout.addLayout(nplc_layout)

        # 滤波器设置
        filter_layout = QHBoxLayout()
        filter_label = QLabel("滤波器:")
        self.filter_check = QCheckBox("启用")
        self.filter_check.setEnabled(False)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_check)
        filter_layout.addStretch(1)

        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(["移动平均", "中值", "低通"])
        self.filter_type_combo.setEnabled(False)
        filter_layout.addWidget(self.filter_type_combo)
        config_layout.addLayout(filter_layout)

        main_layout.addWidget(config_group)

        # 高级设置组
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QVBoxLayout(advanced_group)
        advanced_layout.setSpacing(5)

        # 自动零点
        auto_zero_layout = QHBoxLayout()
        self.auto_zero_check = QCheckBox("自动零点")
        self.auto_zero_check.setChecked(True)
        self.auto_zero_check.setEnabled(False)
        auto_zero_layout.addWidget(self.auto_zero_check)
        auto_zero_layout.addStretch(1)
        advanced_layout.addLayout(auto_zero_layout)

        # 自动量程
        auto_range_layout = QHBoxLayout()
        self.auto_range_check = QCheckBox("自动量程")
        self.auto_range_check.setChecked(True)
        self.auto_range_check.setEnabled(False)
        auto_range_layout.addWidget(self.auto_range_check)
        auto_range_layout.addStretch(1)
        advanced_layout.addLayout(auto_range_layout)

        # 延迟设置
        delay_layout = QHBoxLayout()
        delay_label = QLabel("延迟(ms):")
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 10000)
        self.delay_spin.setValue(100)
        self.delay_spin.setEnabled(False)
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.delay_spin)
        delay_layout.addStretch(1)
        advanced_layout.addLayout(delay_layout)

        # 显示位数
        digits_layout = QHBoxLayout()
        digits_label = QLabel("显示位数:")
        self.digits_spin = QSpinBox()
        self.digits_spin.setRange(3, 7)
        self.digits_spin.setValue(6)
        self.digits_spin.setEnabled(False)
        digits_layout.addWidget(digits_label)
        digits_layout.addWidget(self.digits_spin)
        digits_layout.addStretch(1)
        advanced_layout.addLayout(digits_layout)

        main_layout.addWidget(advanced_group)

        # 应用按钮
        apply_layout = QHBoxLayout()
        apply_layout.addStretch(1)

        self.apply_button = QPushButton("应用配置")
        self.apply_button.setEnabled(False)
        apply_layout.addWidget(self.apply_button)

        self.defaults_button = QPushButton("恢复默认")
        self.defaults_button.setEnabled(False)
        apply_layout.addWidget(self.defaults_button)

        main_layout.addLayout(apply_layout)

        main_layout.addStretch(1)

    def _setup_connections(self):
        """设置信号连接"""
        # 按钮连接
        self.reset_button.clicked.connect(self.reset_requested.emit)
        self.self_test_button.clicked.connect(self.self_test_requested.emit)
        self.calibrate_button.clicked.connect(self.calibration_requested.emit)
        self.apply_button.clicked.connect(self._apply_configuration)
        self.defaults_button.clicked.connect(self._restore_defaults)

        # 配置变化连接
        self.function_combo.currentTextChanged.connect(self.function_changed.emit)
        self.range_combo.currentTextChanged.connect(self.range_changed.emit)
        self.resolution_combo.currentTextChanged.connect(self.resolution_changed.emit)

    def _apply_configuration(self):
        """应用配置"""
        # 这里可以添加配置验证和应用逻辑
        QMessageBox.information(self, "信息", "配置已应用")

    def _restore_defaults(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self, "确认",
            "确定要恢复默认设置吗？当前配置将丢失。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.function_combo.setCurrentText(MEASUREMENT_DCV)
            self.range_combo.setCurrentText(RANGE_AUTO)
            self.resolution_combo.setCurrentText(RESOLUTION_6_5)
            self.nplc_spin.setValue(1.0)
            self.filter_check.setChecked(False)
            self.auto_zero_check.setChecked(True)
            self.auto_range_check.setChecked(True)
            self.delay_spin.setValue(100)
            self.digits_spin.setValue(6)

            QMessageBox.information(self, "信息", "已恢复默认设置")

    # 公共方法
    def set_enabled(self, enabled: bool):
        """设置组件启用状态

        Args:
            enabled: 是否启用
        """
        # 控制按钮
        self.reset_button.setEnabled(enabled)
        self.self_test_button.setEnabled(enabled)
        self.calibrate_button.setEnabled(enabled)

        # 配置控件
        self.function_combo.setEnabled(enabled)
        self.range_combo.setEnabled(enabled)
        self.resolution_combo.setEnabled(enabled)
        self.trigger_combo.setEnabled(enabled)
        self.nplc_spin.setEnabled(enabled)
        self.filter_check.setEnabled(enabled)
        self.filter_type_combo.setEnabled(enabled)

        # 高级设置
        self.auto_zero_check.setEnabled(enabled)
        self.auto_range_check.setEnabled(enabled)
        self.delay_spin.setEnabled(enabled)
        self.digits_spin.setEnabled(enabled)

        # 应用按钮
        self.apply_button.setEnabled(enabled)
        self.defaults_button.setEnabled(enabled)

        # 更新状态
        if enabled:
            self.status_label.setText("已连接")
            self.status_label.setStyleSheet("color: #4CAF50;")
        else:
            self.status_label.setText("未连接")
            self.status_label.setStyleSheet("color: #F44336;")

    def refresh(self):
        """刷新组件"""
        # 重新加载设置
        self.settings.load()

        # 更新控件值
        self.function_combo.setCurrentText(self.settings.measurement.default_function)
        self.range_combo.setCurrentText(self.settings.measurement.default_range)
        self.resolution_combo.setCurrentText(self.settings.measurement.default_resolution)

    def update_status(self, status_text: str, is_error: bool = False):
        """更新状态显示

        Args:
            status_text: 状态文本
            is_error: 是否为错误状态
        """
        self.status_label.setText(status_text)
        if is_error:
            self.status_label.setStyleSheet("color: #F44336;")
        else:
            self.status_label.setStyleSheet("color: #4CAF50;")

    def get_configuration(self) -> dict:
        """获取当前配置

        Returns:
            配置字典
        """
        return {
            "function": self.function_combo.currentText(),
            "range": self.range_combo.currentText(),
            "resolution": self.resolution_combo.currentText(),
            "trigger": self.trigger_combo.currentText(),
            "nplc": self.nplc_spin.value(),
            "filter_enabled": self.filter_check.isChecked(),
            "filter_type": self.filter_type_combo.currentText(),
            "auto_zero": self.auto_zero_check.isChecked(),
            "auto_range": self.auto_range_check.isChecked(),
            "delay": self.delay_spin.value(),
            "digits": self.digits_spin.value()
        }

    def set_configuration(self, config: dict):
        """设置配置

        Args:
            config: 配置字典
        """
        if "function" in config:
            self.function_combo.setCurrentText(config["function"])
        if "range" in config:
            self.range_combo.setCurrentText(config["range"])
        if "resolution" in config:
            self.resolution_combo.setCurrentText(config["resolution"])
        if "trigger" in config:
            self.trigger_combo.setCurrentText(config["trigger"])
        if "nplc" in config:
            self.nplc_spin.setValue(config["nplc"])
        if "filter_enabled" in config:
            self.filter_check.setChecked(config["filter_enabled"])
        if "filter_type" in config:
            self.filter_type_combo.setCurrentText(config["filter_type"])
        if "auto_zero" in config:
            self.auto_zero_check.setChecked(config["auto_zero"])
        if "auto_range" in config:
            self.auto_range_check.setChecked(config["auto_range"])
        if "delay" in config:
            self.delay_spin.setValue(config["delay"])
        if "digits" in config:
            self.digits_spin.setValue(config["digits"])

    def show_progress(self, message: str, maximum: int = 100):
        """显示进度

        Args:
            message: 进度消息
            maximum: 最大值
        """
        # 这里可以添加进度显示逻辑
        pass

    def hide_progress(self):
        """隐藏进度"""
        # 这里可以添加进度隐藏逻辑
        pass

    def show_message(self, message: str, is_error: bool = False):
        """显示消息

        Args:
            message: 消息文本
            is_error: 是否为错误消息
        """
        if is_error:
            QMessageBox.critical(self, "错误", message)
        else:
            QMessageBox.information(self, "信息", message)