"""
连接对话框

提供仪器连接配置界面，支持GPIB、USB、串口等多种接口。
"""

import sys
from typing import List, Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton, QTabWidget,
    QFormLayout, QCheckBox, QMessageBox, QProgressBar,
    QListWidget, QListWidgetItem, QDialogButtonBox, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QFont

from ...config.settings import AppSettings
from ...config.constants import *
from ...communication.visa_manager import VisaManager
from ...communication.serial_adapter import SerialAdapter


class ConnectionDialog(QDialog):
    """连接对话框"""

    # 自定义信号
    connection_test_started = Signal()
    connection_test_finished = Signal(bool, str)

    def __init__(self, settings: AppSettings, parent=None):
        """初始化连接对话框

        Args:
            settings: 应用设置
            parent: 父窗口
        """
        super().__init__(parent)
        self.settings = settings
        self.visa_manager: Optional[VisaManager] = None
        self._setup_ui()
        self._setup_connections()
        self._load_settings()

        self.setWindowTitle("连接仪器")
        self.resize(600, 500)

    def _setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # 接口类型选择
        interface_group = QGroupBox("接口类型")
        interface_layout = QHBoxLayout(interface_group)
        interface_layout.setSpacing(10)

        self.interface_combo = QComboBox()
        self.interface_combo.addItems(INTERFACES)
        self.interface_combo.setCurrentText(self.settings.device.interface)
        interface_layout.addWidget(QLabel("选择接口:"))
        interface_layout.addWidget(self.interface_combo, 1)
        interface_layout.addStretch(1)

        main_layout.addWidget(interface_group)

        # 选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # GPIB选项卡
        self.gpib_tab = self._create_gpib_tab()
        self.tab_widget.addTab(self.gpib_tab, "GPIB")

        # USB选项卡
        self.usb_tab = self._create_usb_tab()
        self.tab_widget.addTab(self.usb_tab, "USB")

        # 串口选项卡
        self.serial_tab = self._create_serial_tab()
        self.tab_widget.addTab(self.serial_tab, "串口")

        # 模拟选项卡
        self.mock_tab = self._create_mock_tab()
        self.tab_widget.addTab(self.mock_tab, "模拟")

        main_layout.addWidget(self.tab_widget, 1)

        # 自动检测区域
        detect_group = QGroupBox("自动检测")
        detect_layout = QVBoxLayout(detect_group)

        # 可用资源列表
        self.resource_list = QListWidget()
        self.resource_list.setMaximumHeight(100)
        detect_layout.addWidget(QLabel("可用资源:"))

        list_layout = QHBoxLayout()
        list_layout.addWidget(self.resource_list, 1)

        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_resources)
        list_layout.addWidget(refresh_button)

        detect_layout.addLayout(list_layout)

        # 检测按钮
        detect_button_layout = QHBoxLayout()
        self.detect_button = QPushButton("检测设备")
        self.detect_button.clicked.connect(self.detect_devices)
        detect_button_layout.addWidget(self.detect_button)

        self.test_button = QPushButton("测试连接")
        self.test_button.clicked.connect(self.test_connection)
        detect_button_layout.addWidget(self.test_button)

        detect_button_layout.addStretch(1)
        detect_layout.addLayout(detect_button_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        detect_layout.addWidget(self.progress_bar)

        main_layout.addWidget(detect_group)

        # 按钮框
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.ok_button = button_box.button(QDialogButtonBox.Ok)
        self.ok_button.setText("连接")
        self.ok_button.setEnabled(False)

        main_layout.addWidget(button_box)

    def _create_gpib_tab(self) -> QWidget:
        """创建GPIB选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(10)

        # GPIB地址
        self.gpib_address_spin = QSpinBox()
        self.gpib_address_spin.setRange(0, 30)
        self.gpib_address_spin.setValue(self.settings.device.gpib_address)
        layout.addRow("GPIB地址:", self.gpib_address_spin)

        # 超时设置
        self.gpib_timeout_spin = QSpinBox()
        self.gpib_timeout_spin.setRange(100, 60000)
        self.gpib_timeout_spin.setValue(self.settings.device.timeout)
        self.gpib_timeout_spin.setSuffix(" ms")
        layout.addRow("超时时间:", self.gpib_timeout_spin)

        # VISA资源字符串
        self.gpib_resource_label = QLabel()
        self.gpib_resource_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addRow("资源字符串:", self.gpib_resource_label)

        layout.addRow(QLabel(""))  # 空行

        # 信息标签
        info_label = QLabel(
            "GPIB连接需要安装NI-VISA或Keysight VISA运行时。\n"
            "确保GPIB接口卡已正确安装并配置。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addRow(info_label)

        return widget

    def _create_usb_tab(self) -> QWidget:
        """创建USB选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(10)

        # 厂商ID
        self.usb_vendor_edit = QLineEdit(self.settings.device.usb_vendor_id)
        layout.addRow("厂商ID:", self.usb_vendor_edit)

        # 产品ID
        self.usb_product_edit = QLineEdit(self.settings.device.usb_product_id)
        layout.addRow("产品ID:", self.usb_product_edit)

        # 序列号
        self.usb_serial_edit = QLineEdit()
        self.usb_serial_edit.setPlaceholderText("可选")
        layout.addRow("序列号:", self.usb_serial_edit)

        # 超时设置
        self.usb_timeout_spin = QSpinBox()
        self.usb_timeout_spin.setRange(100, 60000)
        self.usb_timeout_spin.setValue(self.settings.device.timeout)
        self.usb_timeout_spin.setSuffix(" ms")
        layout.addRow("超时时间:", self.usb_timeout_spin)

        # VISA资源字符串
        self.usb_resource_label = QLabel()
        self.usb_resource_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addRow("资源字符串:", self.usb_resource_label)

        layout.addRow(QLabel(""))  # 空行

        # 信息标签
        info_label = QLabel(
            "USB连接支持VISA-USB和PyUSB两种方式。\n"
            "如果使用PyUSB，需要安装libusb驱动。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addRow(info_label)

        return widget

    def _create_serial_tab(self) -> QWidget:
        """创建串口选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(10)

        # 串口选择
        self.serial_port_combo = QComboBox()
        self.serial_port_combo.setEditable(True)
        self.serial_port_combo.addItem(self.settings.device.serial_port)
        layout.addRow("串口:", self.serial_port_combo)

        # 波特率
        self.serial_baudrate_combo = QComboBox()
        self.serial_baudrate_combo.setEditable(True)
        baudrates = ["9600", "19200", "38400", "57600", "115200"]
        self.serial_baudrate_combo.addItems(baudrates)
        self.serial_baudrate_combo.setCurrentText(str(self.settings.device.serial_baudrate))
        layout.addRow("波特率:", self.serial_baudrate_combo)

        # 数据位
        self.serial_bytesize_combo = QComboBox()
        self.serial_bytesize_combo.addItems(["5", "6", "7", "8"])
        self.serial_bytesize_combo.setCurrentText("8")
        layout.addRow("数据位:", self.serial_bytesize_combo)

        # 校验位
        self.serial_parity_combo = QComboBox()
        self.serial_parity_combo.addItems(["N", "E", "O", "M", "S"])
        self.serial_parity_combo.setCurrentText("N")
        layout.addRow("校验位:", self.serial_parity_combo)

        # 停止位
        self.serial_stopbits_combo = QComboBox()
        self.serial_stopbits_combo.addItems(["1", "1.5", "2"])
        self.serial_stopbits_combo.setCurrentText("1")
        layout.addRow("停止位:", self.serial_stopbits_combo)

        # 超时设置
        self.serial_timeout_spin = QSpinBox()
        self.serial_timeout_spin.setRange(100, 10000)
        self.serial_timeout_spin.setValue(1000)
        self.serial_timeout_spin.setSuffix(" ms")
        layout.addRow("超时时间:", self.serial_timeout_spin)

        # 流控制
        self.serial_flowcontrol_check = QCheckBox("启用硬件流控制")
        layout.addRow("流控制:", self.serial_flowcontrol_check)

        layout.addRow(QLabel(""))  # 空行

        # 信息标签
        info_label = QLabel(
            "串口连接需要正确配置串口参数。\n"
            "FLUKE 8846A通常使用9600波特率，8位数据，无校验，1位停止位。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addRow(info_label)

        return widget

    def _create_mock_tab(self) -> QWidget:
        """创建模拟选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(10)

        # 模拟设备ID
        self.mock_device_id_edit = QLineEdit("fluke8846a_simulator")
        layout.addRow("设备ID:", self.mock_device_id_edit)

        # 模拟模式
        self.mock_mode_combo = QComboBox()
        self.mock_mode_combo.addItems(["简单模拟", "高级模拟", "随机数据", "固定数据"])
        self.mock_mode_combo.setCurrentText("简单模拟")
        layout.addRow("模拟模式:", self.mock_mode_combo)

        # 基准值设置
        self.mock_base_value_spin = QDoubleSpinBox()
        self.mock_base_value_spin.setRange(0.0, 1000.0)
        self.mock_base_value_spin.setValue(5.0)
        self.mock_base_value_spin.setSuffix(" V")
        layout.addRow("基准值:", self.mock_base_value_spin)

        # 噪声水平
        self.mock_noise_spin = QDoubleSpinBox()
        self.mock_noise_spin.setRange(0.0, 1.0)
        self.mock_noise_spin.setValue(0.001)
        self.mock_noise_spin.setSingleStep(0.001)
        layout.addRow("噪声水平:", self.mock_noise_spin)

        # 响应延迟
        self.mock_delay_spin = QSpinBox()
        self.mock_delay_spin.setRange(0, 5000)
        self.mock_delay_spin.setValue(50)
        self.mock_delay_spin.setSuffix(" ms")
        layout.addRow("响应延迟:", self.mock_delay_spin)

        layout.addRow(QLabel(""))  # 空行

        # 信息标签
        info_label = QLabel(
            "模拟模式用于在没有实际硬件的情况下测试应用功能。\n"
            "模拟FLUKE 8846A的基本响应行为，生成模拟测量数据。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addRow(info_label)

        # 测试按钮
        test_button = QPushButton("测试模拟连接")
        test_button.clicked.connect(self.test_mock_connection)
        layout.addRow(test_button)

        return widget

    def _setup_connections(self):
        """设置信号连接"""
        # 接口类型变化
        self.interface_combo.currentTextChanged.connect(self._on_interface_changed)

        # 参数变化
        self.gpib_address_spin.valueChanged.connect(self._update_gpib_resource)
        self.usb_vendor_edit.textChanged.connect(self._update_usb_resource)
        self.usb_product_edit.textChanged.connect(self._update_usb_resource)

        # 初始更新
        self._on_interface_changed(self.interface_combo.currentText())
        self._update_gpib_resource()
        self._update_usb_resource()

    def _load_settings(self):
        """加载设置"""
        # 串口列表
        self._refresh_serial_ports()

    def _on_interface_changed(self, interface: str):
        """接口类型变化处理

        Args:
            interface: 接口类型
        """
        # 显示对应的选项卡
        if interface == INTERFACE_GPIB:
            self.tab_widget.setCurrentWidget(self.gpib_tab)
        elif interface == INTERFACE_USB:
            self.tab_widget.setCurrentWidget(self.usb_tab)
        elif interface == INTERFACE_SERIAL:
            self.tab_widget.setCurrentWidget(self.serial_tab)
        elif interface == INTERFACE_MOCK:
            self.tab_widget.setCurrentWidget(self.mock_tab)

        # 更新资源列表
        self.refresh_resources()

    def _update_gpib_resource(self):
        """更新GPIB资源字符串"""
        address = self.gpib_address_spin.value()
        resource = f"GPIB0::{address}::INSTR"
        self.gpib_resource_label.setText(resource)

    def _update_usb_resource(self):
        """更新USB资源字符串"""
        vendor = self.usb_vendor_edit.text()
        product = self.usb_product_edit.text()

        if vendor and product:
            resource = f"USB0::{vendor}::{product}::INSTR"
            self.usb_resource_label.setText(resource)
        else:
            self.usb_resource_label.setText("请填写厂商ID和产品ID")

    def _refresh_serial_ports(self):
        """刷新串口列表"""
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()

            self.serial_port_combo.clear()
            for port in ports:
                description = port.description if port.description else "Unknown"
                self.serial_port_combo.addItem(f"{port.device} - {description}")

        except ImportError:
            self.serial_port_combo.clear()
            self.serial_port_combo.addItem("COM3")
            self.serial_port_combo.addItem("COM4")
            self.serial_port_combo.addItem("COM5")

    def refresh_resources(self):
        """刷新可用资源列表"""
        self.resource_list.clear()

        try:
            if self.visa_manager is None:
                self.visa_manager = VisaManager()

            resources = self.visa_manager.list_resources()
            for resource in resources:
                item = QListWidgetItem(resource)
                self.resource_list.addItem(item)

            if not resources:
                self.resource_list.addItem("未发现VISA资源")

        except Exception as e:
            self.resource_list.addItem(f"错误: {str(e)}")

    def detect_devices(self):
        """检测设备"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定模式
        self.detect_button.setEnabled(False)
        self.test_button.setEnabled(False)

        # 模拟检测过程
        QTimer.singleShot(2000, self._on_detection_finished)

    def _on_detection_finished(self):
        """设备检测完成"""
        self.progress_bar.setVisible(False)
        self.detect_button.setEnabled(True)
        self.test_button.setEnabled(True)

        # 刷新资源列表
        self.refresh_resources()

        # 显示结果
        if self.resource_list.count() > 0:
            QMessageBox.information(self, "检测完成", f"发现 {self.resource_list.count()} 个资源")
        else:
            QMessageBox.warning(self, "检测完成", "未发现任何资源")

    def test_connection(self):
        """测试连接"""
        # 获取当前选择的资源
        current_items = self.resource_list.selectedItems()
        if not current_items:
            QMessageBox.warning(self, "警告", "请先选择一个资源")
            return

        resource_name = current_items[0].text()
        if not resource_name or resource_name.startswith("错误:") or resource_name.startswith("未发现"):
            QMessageBox.warning(self, "警告", "无效的资源")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.ok_button.setEnabled(False)

        # 测试连接
        if self.visa_manager is None:
            self.visa_manager = VisaManager()

        success, message = self.visa_manager.test_connection(resource_name)

        self.progress_bar.setVisible(False)
        self.ok_button.setEnabled(True)

        if success:
            QMessageBox.information(self, "连接测试", f"连接测试成功\n{message}")
            self.ok_button.setEnabled(True)
        else:
            QMessageBox.warning(self, "连接测试", f"连接测试失败\n{message}")

    def test_mock_connection(self):
        """测试模拟连接"""
        try:
            from ...communication.mock_adapter import MockAdapter

            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)

            # 创建模拟适配器
            adapter_id = self.mock_device_id_edit.text() or "fluke8846a_simulator"
            adapter = MockAdapter(adapter_id)

            # 设置模拟参数
            base_value = self.mock_base_value_spin.value()
            noise_level = self.mock_noise_spin.value()
            response_delay = self.mock_delay_spin.value()

            # 连接测试
            success = adapter.connect(
                base_value=base_value,
                noise_level=noise_level,
                response_delay=response_delay
            )

            if success:
                # 测试通信
                adapter.send(b"*IDN?")
                response = adapter.receive()

                if response:
                    # 断开连接
                    adapter.disconnect()

                    self.progress_bar.setVisible(False)
                    QMessageBox.information(
                        self,
                        "模拟连接测试",
                        f"模拟连接测试成功\n"
                        f"设备响应: {response.decode('utf-8', errors='ignore')}"
                    )
                    self.ok_button.setEnabled(True)
                    return

            # 如果失败
            adapter.disconnect()
            self.progress_bar.setVisible(False)
            QMessageBox.warning(
                self,
                "模拟连接测试",
                "模拟连接测试失败，请检查参数"
            )

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.warning(
                self,
                "模拟连接测试",
                f"模拟连接测试时发生错误:\n{str(e)}"
            )

    def get_connection_params(self) -> Dict[str, Any]:
        """获取连接参数

        Returns:
            连接参数字典
        """
        interface = self.interface_combo.currentText()

        params = {
            "interface": interface,
            "timeout": self.settings.device.timeout
        }

        if interface == INTERFACE_GPIB:
            params.update({
                "resource_name": self.gpib_resource_label.text(),
                "gpib_address": self.gpib_address_spin.value(),
                "timeout": self.gpib_timeout_spin.value()
            })

        elif interface == INTERFACE_USB:
            params.update({
                "resource_name": self.usb_resource_label.text(),
                "vendor_id": self.usb_vendor_edit.text(),
                "product_id": self.usb_product_edit.text(),
                "serial_number": self.usb_serial_edit.text(),
                "timeout": self.usb_timeout_spin.value()
            })

        elif interface == INTERFACE_SERIAL:
            # 提取串口号
            port_text = self.serial_port_combo.currentText()
            port = port_text.split(" - ")[0] if " - " in port_text else port_text

            params.update({
                "port": port,
                "baudrate": int(self.serial_baudrate_combo.currentText()),
                "bytesize": int(self.serial_bytesize_combo.currentText()),
                "parity": self.serial_parity_combo.currentText(),
                "stopbits": float(self.serial_stopbits_combo.currentText()),
                "timeout": self.serial_timeout_spin.value() / 1000.0,  # 转换为秒
                "flow_control": self.serial_flowcontrol_check.isChecked()
            })

        elif interface == INTERFACE_MOCK:
            params.update({
                "adapter_id": self.mock_device_id_edit.text(),
                "mode": self.mock_mode_combo.currentText(),
                "base_value": self.mock_base_value_spin.value(),
                "noise_level": self.mock_noise_spin.value(),
                "response_delay": self.mock_delay_spin.value()
            })

        return params

    def accept(self):
        """接受对话框"""
        # 保存设置
        interface = self.interface_combo.currentText()
        self.settings.device.interface = interface

        if interface == INTERFACE_GPIB:
            self.settings.device.gpib_address = self.gpib_address_spin.value()
            self.settings.device.timeout = self.gpib_timeout_spin.value()

        elif interface == INTERFACE_USB:
            self.settings.device.usb_vendor_id = self.usb_vendor_edit.text()
            self.settings.device.usb_product_id = self.usb_product_edit.text()
            self.settings.device.timeout = self.usb_timeout_spin.value()

        elif interface == INTERFACE_SERIAL:
            port_text = self.serial_port_combo.currentText()
            port = port_text.split(" - ")[0] if " - " in port_text else port_text
            self.settings.device.serial_port = port
            self.settings.device.serial_baudrate = int(self.serial_baudrate_combo.currentText())
            # 注意：串口超时单位不同，这里不保存

        elif interface == INTERFACE_MOCK:
            # 模拟接口不需要保存特殊设置，使用默认值即可
            pass

        # 保存设置
        self.settings.save()

        super().accept()

    def closeEvent(self, event):
        """关闭事件"""
        if self.visa_manager:
            self.visa_manager.cleanup()
        event.accept()