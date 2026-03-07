"""
设置对话框

提供应用设置配置界面。
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QPushButton, QGroupBox, QDialogButtonBox,
    QMessageBox, QFileDialog, QColorDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from ...config.settings import AppSettings
from ...config.constants import *


class SettingsDialog(QDialog):
    """设置对话框"""

    # 自定义信号
    settings_changed = Signal()

    def __init__(self, settings: AppSettings, parent=None):
        """初始化设置对话框

        Args:
            settings: 应用设置
            parent: 父窗口
        """
        super().__init__(parent)
        self.settings = settings
        self.original_settings = settings.to_dict()
        self._setup_ui()
        self._setup_connections()
        self._load_settings()

        self.setWindowTitle("应用设置")
        self.resize(700, 600)

    def _setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # 选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # 设备设置选项卡
        self.device_tab = self._create_device_tab()
        self.tab_widget.addTab(self.device_tab, "设备")

        # 测量设置选项卡
        self.measurement_tab = self._create_measurement_tab()
        self.tab_widget.addTab(self.measurement_tab, "测量")

        # 显示设置选项卡
        self.display_tab = self._create_display_tab()
        self.tab_widget.addTab(self.display_tab, "显示")

        # 数据设置选项卡
        self.data_tab = self._create_data_tab()
        self.tab_widget.addTab(self.data_tab, "数据")

        # 高级设置选项卡
        self.advanced_tab = self._create_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "高级")

        main_layout.addWidget(self.tab_widget, 1)

        # 按钮框
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply | QDialogButtonBox.RestoreDefaults
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.apply_button = button_box.button(QDialogButtonBox.Apply)
        self.apply_button.clicked.connect(self.apply_settings)

        self.defaults_button = button_box.button(QDialogButtonBox.RestoreDefaults)
        self.defaults_button.clicked.connect(self.restore_defaults)

        main_layout.addWidget(button_box)

    def _create_device_tab(self) -> QWidget:
        """创建设备设置选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(10)

        # 接口设置
        interface_label = QLabel("默认接口:")
        self.interface_combo = QComboBox()
        self.interface_combo.addItems(INTERFACES)
        layout.addRow(interface_label, self.interface_combo)

        # GPIB设置
        gpib_group = QGroupBox("GPIB设置")
        gpib_layout = QFormLayout(gpib_group)

        self.gpib_address_spin = QSpinBox()
        self.gpib_address_spin.setRange(0, 30)
        gpib_layout.addRow("GPIB地址:", self.gpib_address_spin)

        layout.addRow(gpib_group)

        # USB设置
        usb_group = QGroupBox("USB设置")
        usb_layout = QFormLayout(usb_group)

        self.usb_vendor_edit = QLineEdit()
        usb_layout.addRow("厂商ID:", self.usb_vendor_edit)

        self.usb_product_edit = QLineEdit()
        usb_layout.addRow("产品ID:", self.usb_product_edit)

        layout.addRow(usb_group)

        # 串口设置
        serial_group = QGroupBox("串口设置")
        serial_layout = QFormLayout(serial_group)

        self.serial_port_edit = QLineEdit()
        serial_layout.addRow("串口号:", self.serial_port_edit)

        self.serial_baudrate_spin = QSpinBox()
        self.serial_baudrate_spin.setRange(1200, 115200)
        self.serial_baudrate_spin.setValue(9600)
        serial_layout.addRow("波特率:", self.serial_baudrate_spin)

        layout.addRow(serial_group)

        # 超时设置
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(100, 60000)
        self.timeout_spin.setSuffix(" ms")
        layout.addRow("默认超时:", self.timeout_spin)

        return widget

    def _create_measurement_tab(self) -> QWidget:
        """创建测量设置选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(10)

        # 默认测量设置
        default_group = QGroupBox("默认测量设置")
        default_layout = QFormLayout(default_group)

        self.default_function_combo = QComboBox()
        self.default_function_combo.addItems(MEASUREMENTS)
        default_layout.addRow("默认功能:", self.default_function_combo)

        self.default_range_combo = QComboBox()
        self.default_range_combo.addItems(VOLTAGE_RANGES)
        default_layout.addRow("默认量程:", self.default_range_combo)

        self.default_resolution_combo = QComboBox()
        self.default_resolution_combo.addItems(RESOLUTIONS)
        default_layout.addRow("默认分辨率:", self.default_resolution_combo)

        layout.addRow(default_group)

        # 采样设置
        sample_group = QGroupBox("采样设置")
        sample_layout = QFormLayout(sample_group)

        self.sample_count_spin = QSpinBox()
        self.sample_count_spin.setRange(1, 10000)
        sample_layout.addRow("默认采样数:", self.sample_count_spin)

        self.measurement_interval_spin = QDoubleSpinBox()
        self.measurement_interval_spin.setRange(0.1, 60.0)
        self.measurement_interval_spin.setDecimals(1)
        self.measurement_interval_spin.setSuffix(" s")
        sample_layout.addRow("测量间隔:", self.measurement_interval_spin)

        layout.addRow(sample_group)

        # 自动记录
        self.auto_record_check = QCheckBox("自动记录测量数据")
        layout.addRow(self.auto_record_check)

        # 记录格式
        self.log_format_combo = QComboBox()
        self.log_format_combo.addItems(["CSV", "JSON", "Excel"])
        layout.addRow("记录格式:", self.log_format_combo)

        return widget

    def _create_display_tab(self) -> QWidget:
        """创建显示设置选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(10)

        # 主题设置
        theme_group = QGroupBox("主题设置")
        theme_layout = QFormLayout(theme_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(THEMES)
        theme_layout.addRow("主题:", self.theme_combo)

        # 语言设置
        self.language_combo = QComboBox()
        self.language_combo.addItems(LANGUAGES)
        theme_layout.addRow("语言:", self.language_combo)

        layout.addRow(theme_group)

        # 窗口设置
        window_group = QGroupBox("窗口设置")
        window_layout = QFormLayout(window_group)

        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 1920)
        window_layout.addRow("窗口宽度:", self.window_width_spin)

        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 1080)
        window_layout.addRow("窗口高度:", self.window_height_spin)

        layout.addRow(window_group)

        # 图表设置
        chart_group = QGroupBox("图表设置")
        chart_layout = QFormLayout(chart_group)

        self.show_grid_check = QCheckBox("显示网格")
        chart_layout.addRow(self.show_grid_check)

        self.auto_scale_check = QCheckBox("自动缩放")
        chart_layout.addRow(self.auto_scale_check)

        self.refresh_rate_spin = QSpinBox()
        self.refresh_rate_spin.setRange(100, 5000)
        self.refresh_rate_spin.setSuffix(" ms")
        chart_layout.addRow("刷新率:", self.refresh_rate_spin)

        layout.addRow(chart_group)

        # 字体设置
        font_group = QGroupBox("字体设置")
        font_layout = QFormLayout(font_group)

        self.font_family_edit = QLineEdit()
        font_layout.addRow("字体:", self.font_family_edit)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 20)
        font_layout.addRow("字体大小:", self.font_size_spin)

        layout.addRow(font_group)

        return widget

    def _create_data_tab(self) -> QWidget:
        """创建数据设置选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(10)

        # 数据存储
        storage_group = QGroupBox("数据存储")
        storage_layout = QFormLayout(storage_group)

        self.data_dir_edit = QLineEdit()
        self.data_dir_edit.setReadOnly(True)
        storage_layout.addRow("数据目录:", self.data_dir_edit)

        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_data_dir)
        storage_layout.addRow("", browse_button)

        layout.addRow(storage_group)

        # 自动保存
        save_group = QGroupBox("自动保存")
        save_layout = QFormLayout(save_group)

        self.auto_save_check = QCheckBox("启用自动保存")
        save_layout.addRow(self.auto_save_check)

        self.auto_save_interval_spin = QSpinBox()
        self.auto_save_interval_spin.setRange(1, 60)
        self.auto_save_interval_spin.setSuffix(" 分钟")
        save_layout.addRow("保存间隔:", self.auto_save_interval_spin)

        layout.addRow(save_group)

        # 备份设置
        backup_group = QGroupBox("备份设置")
        backup_layout = QFormLayout(backup_group)

        self.enable_backup_check = QCheckBox("启用自动备份")
        backup_layout.addRow(self.enable_backup_check)

        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 100)
        backup_layout.addRow("备份数量:", self.backup_count_spin)

        layout.addRow(backup_group)

        # 导出设置
        export_group = QGroupBox("导出设置")
        export_layout = QFormLayout(export_group)

        self.default_export_format_combo = QComboBox()
        self.default_export_format_combo.addItems(["CSV", "Excel", "JSON", "PDF"])
        export_layout.addRow("默认导出格式:", self.default_export_format_combo)

        self.include_timestamp_check = QCheckBox("包含时间戳")
        export_layout.addRow(self.include_timestamp_check)

        self.include_metadata_check = QCheckBox("包含元数据")
        export_layout.addRow(self.include_metadata_check)

        layout.addRow(export_group)

        return widget

    def _create_advanced_tab(self) -> QWidget:
        """创建高级设置选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(10)

        # 日志设置
        log_group = QGroupBox("日志设置")
        log_layout = QFormLayout(log_group)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_layout.addRow("日志级别:", self.log_level_combo)

        self.log_to_file_check = QCheckBox("记录到文件")
        log_layout.addRow(self.log_to_file_check)

        self.log_file_size_spin = QSpinBox()
        self.log_file_size_spin.setRange(1, 100)
        self.log_file_size_spin.setSuffix(" MB")
        log_layout.addRow("日志文件大小:", self.log_file_size_spin)

        layout.addRow(log_group)

        # 性能设置
        perf_group = QGroupBox("性能设置")
        perf_layout = QFormLayout(perf_group)

        self.max_history_spin = QSpinBox()
        self.max_history_spin.setRange(100, 100000)
        perf_layout.addRow("最大历史记录:", self.max_history_spin)

        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(10, 1000)
        self.cache_size_spin.setSuffix(" MB")
        perf_layout.addRow("缓存大小:", self.cache_size_spin)

        layout.addRow(perf_group)

        # 网络设置
        network_group = QGroupBox("网络设置")
        network_layout = QFormLayout(network_group)

        self.enable_remote_check = QCheckBox("启用远程访问")
        network_layout.addRow(self.enable_remote_check)

        self.remote_port_spin = QSpinBox()
        self.remote_port_spin.setRange(1024, 65535)
        network_layout.addRow("远程端口:", self.remote_port_spin)

        layout.addRow(network_group)

        # 调试设置
        debug_group = QGroupBox("调试设置")
        debug_layout = QFormLayout(debug_group)

        self.enable_debug_check = QCheckBox("启用调试模式")
        debug_layout.addRow(self.enable_debug_check)

        self.show_debug_info_check = QCheckBox("显示调试信息")
        debug_layout.addRow(self.show_debug_info_check)

        layout.addRow(debug_group)

        return widget

    def _setup_connections(self):
        """设置信号连接"""
        # 应用按钮
        self.apply_button.clicked.connect(self.apply_settings)

        # 恢复默认按钮
        self.defaults_button.clicked.connect(self.restore_defaults)

    def _load_settings(self):
        """加载设置到UI"""
        # 设备设置
        self.interface_combo.setCurrentText(self.settings.device.interface)
        self.gpib_address_spin.setValue(self.settings.device.gpib_address)
        self.usb_vendor_edit.setText(self.settings.device.usb_vendor_id)
        self.usb_product_edit.setText(self.settings.device.usb_product_id)
        self.serial_port_edit.setText(self.settings.device.serial_port)
        self.serial_baudrate_spin.setValue(self.settings.device.serial_baudrate)
        self.timeout_spin.setValue(self.settings.device.timeout)

        # 测量设置
        self.default_function_combo.setCurrentText(self.settings.measurement.default_function)
        self.default_range_combo.setCurrentText(self.settings.measurement.default_range)
        self.default_resolution_combo.setCurrentText(self.settings.measurement.default_resolution)
        self.sample_count_spin.setValue(self.settings.measurement.sample_count)
        self.measurement_interval_spin.setValue(self.settings.measurement.measurement_interval)
        self.auto_record_check.setChecked(self.settings.measurement.auto_record)
        self.log_format_combo.setCurrentText(self.settings.measurement.log_format.upper())

        # 显示设置
        self.theme_combo.setCurrentText(self.settings.display.theme)
        self.language_combo.setCurrentText(self.settings.display.language)
        self.window_width_spin.setValue(self.settings.display.window_width)
        self.window_height_spin.setValue(self.settings.display.window_height)
        self.show_grid_check.setChecked(self.settings.display.show_grid)
        self.auto_scale_check.setChecked(self.settings.display.auto_scale)
        self.refresh_rate_spin.setValue(self.settings.display.refresh_rate)

        # 数据目录
        from ...config.paths import paths
        self.data_dir_edit.setText(str(paths.data_dir))

    def browse_data_dir(self):
        """浏览数据目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择数据目录",
            self.data_dir_edit.text(),
            QFileDialog.ShowDirsOnly
        )

        if dir_path:
            self.data_dir_edit.setText(dir_path)

    def apply_settings(self):
        """应用设置"""
        try:
            # 设备设置
            self.settings.device.interface = self.interface_combo.currentText()
            self.settings.device.gpib_address = self.gpib_address_spin.value()
            self.settings.device.usb_vendor_id = self.usb_vendor_edit.text()
            self.settings.device.usb_product_id = self.usb_product_edit.text()
            self.settings.device.serial_port = self.serial_port_edit.text()
            self.settings.device.serial_baudrate = self.serial_baudrate_spin.value()
            self.settings.device.timeout = self.timeout_spin.value()

            # 测量设置
            self.settings.measurement.default_function = self.default_function_combo.currentText()
            self.settings.measurement.default_range = self.default_range_combo.currentText()
            self.settings.measurement.default_resolution = self.default_resolution_combo.currentText()
            self.settings.measurement.sample_count = self.sample_count_spin.value()
            self.settings.measurement.measurement_interval = self.measurement_interval_spin.value()
            self.settings.measurement.auto_record = self.auto_record_check.isChecked()
            self.settings.measurement.log_format = f".{self.log_format_combo.currentText().lower()}"

            # 显示设置
            self.settings.display.theme = self.theme_combo.currentText()
            self.settings.display.language = self.language_combo.currentText()
            self.settings.display.window_width = self.window_width_spin.value()
            self.settings.display.window_height = self.window_height_spin.value()
            self.settings.display.show_grid = self.show_grid_check.isChecked()
            self.settings.display.auto_scale = self.auto_scale_check.isChecked()
            self.settings.display.refresh_rate = self.refresh_rate_spin.value()

            # 保存设置
            self.settings.save()

            # 发射信号
            self.settings_changed.emit()

            QMessageBox.information(self, "成功", "设置已应用并保存")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用设置失败: {str(e)}")

    def restore_defaults(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self, "确认",
            "确定要恢复所有设置为默认值吗？当前设置将丢失。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.settings.reset_to_defaults()
            self._load_settings()
            QMessageBox.information(self, "成功", "已恢复默认设置")

    def accept(self):
        """接受对话框"""
        self.apply_settings()
        super().accept()

    def reject(self):
        """拒绝对话框"""
        # 检查是否有未保存的更改
        current_settings = self.settings.to_dict()
        if current_settings != self.original_settings:
            reply = QMessageBox.question(
                self, "未保存的更改",
                "有未保存的更改，确定要放弃吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                return

        super().reject()

    def closeEvent(self, event):
        """关闭事件"""
        self.reject()
        event.accept()