"""
GUI主窗口

提供FLUKE 8846A控制应用的主界面。
包含菜单栏、工具栏、状态栏和主要功能面板。
"""

import sys
from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QToolBar, QStatusBar, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QIcon

from ..config.settings import AppSettings
from ..config.constants import INTERFACE_SERIAL, INTERFACE_MOCK, INTERFACE_TCP, DEFAULT_TCP_PORT
from ..core.instrument import Fluke8846AInstrument, MeasurementData
from ..utils.logger import get_logger

from .widgets.measurement_panel import MeasurementPanel
from .widgets.control_panel import ControlPanel
from .widgets.plot_widget import PlotWidget
from .widgets.status_bar import StatusBar
from .dialogs.connection_dialog import ConnectionDialog
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.about_dialog import AboutDialog


logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """主窗口类"""

    # 自定义信号
    measurement_received = Signal(MeasurementData)
    connection_changed = Signal(bool)
    error_occurred = Signal(str)

    def __init__(self, settings: AppSettings):
        """初始化主窗口

        Args:
            settings: 应用设置
        """
        super().__init__()
        self.settings = settings
        self.instrument: Optional[Fluke8846AInstrument] = None
        self._setup_ui()
        self._setup_connections()
        self._setup_timers()

        # 加载窗口设置
        self._load_window_settings()

        logger.info("主窗口初始化完成")

    def _setup_ui(self):
        """设置UI"""
        # 设置窗口属性
        self.setWindowTitle(f"FLUKE 8846A Control - {self.settings.version}")
        self.resize(
            self.settings.display.window_width,
            self.settings.display.window_height
        )

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        # 创建菜单栏
        self._create_menu_bar()

        # 创建工具栏
        self._create_tool_bar()

        # 创建主内容区域
        content_widget = self._create_content_area()
        main_layout.addWidget(content_widget, 1)

        # 创建状态栏
        self._create_status_bar()
        main_layout.addWidget(self.status_bar)

        logger.debug("UI设置完成")

    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        # 连接操作
        self.connect_action = QAction("连接设备", self)
        self.connect_action.setShortcut("Ctrl+C")
        file_menu.addAction(self.connect_action)

        self.disconnect_action = QAction("断开连接", self)
        self.disconnect_action.setEnabled(False)
        file_menu.addAction(self.disconnect_action)

        file_menu.addSeparator()

        # 导出数据
        self.export_action = QAction("导出数据...", self)
        self.export_action.setShortcut("Ctrl+E")
        self.export_action.setEnabled(False)
        file_menu.addAction(self.export_action)

        file_menu.addSeparator()

        # 退出
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 测量菜单
        measure_menu = menubar.addMenu("测量")

        self.single_measure_action = QAction("单次测量", self)
        self.single_measure_action.setShortcut("F5")
        self.single_measure_action.setEnabled(False)
        measure_menu.addAction(self.single_measure_action)

        self.start_continuous_action = QAction("开始连续测量", self)
        self.start_continuous_action.setShortcut("F6")
        self.start_continuous_action.setEnabled(False)
        measure_menu.addAction(self.start_continuous_action)

        self.stop_continuous_action = QAction("停止连续测量", self)
        self.stop_continuous_action.setShortcut("F7")
        self.stop_continuous_action.setEnabled(False)
        measure_menu.addAction(self.stop_continuous_action)

        measure_menu.addSeparator()

        self.clear_data_action = QAction("清空数据", self)
        self.clear_data_action.setShortcut("Ctrl+D")
        self.clear_data_action.setEnabled(False)
        measure_menu.addAction(self.clear_data_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图")

        self.toggle_measurement_panel_action = QAction("显示/隐藏测量面板", self)
        self.toggle_measurement_panel_action.setCheckable(True)
        self.toggle_measurement_panel_action.setChecked(True)
        view_menu.addAction(self.toggle_measurement_panel_action)

        self.toggle_plot_panel_action = QAction("显示/隐藏图表", self)
        self.toggle_plot_panel_action.setCheckable(True)
        self.toggle_plot_panel_action.setChecked(True)
        view_menu.addAction(self.toggle_plot_panel_action)

        view_menu.addSeparator()

        self.zoom_in_action = QAction("放大", self)
        self.zoom_in_action.setShortcut("Ctrl++")
        view_menu.addAction(self.zoom_in_action)

        self.zoom_out_action = QAction("缩小", self)
        self.zoom_out_action.setShortcut("Ctrl+-")
        view_menu.addAction(self.zoom_out_action)

        self.zoom_reset_action = QAction("重置缩放", self)
        self.zoom_reset_action.setShortcut("Ctrl+0")
        view_menu.addAction(self.zoom_reset_action)

        # 设置菜单
        settings_menu = menubar.addMenu("设置")

        self.settings_action = QAction("应用设置...", self)
        self.settings_action.setShortcut("Ctrl+P")
        settings_menu.addAction(self.settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        self.about_action = QAction("关于...", self)
        self.about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(self.about_action)

        logger.debug("菜单栏创建完成")

    def _create_tool_bar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 连接按钮
        self.toolbar_connect = toolbar.addAction("连接")
        self.toolbar_connect.triggered.connect(self.show_connection_dialog)

        # 断开按钮
        self.toolbar_disconnect = toolbar.addAction("断开")
        self.toolbar_disconnect.setEnabled(False)
        self.toolbar_disconnect.triggered.connect(self.disconnect_instrument)

        toolbar.addSeparator()

        # 单次测量按钮
        self.toolbar_single = toolbar.addAction("单次测量")
        self.toolbar_single.setEnabled(False)

        # 连续测量按钮
        self.toolbar_continuous = toolbar.addAction("连续测量")
        self.toolbar_continuous.setEnabled(False)

        # 停止测量按钮
        self.toolbar_stop = toolbar.addAction("停止")
        self.toolbar_stop.setEnabled(False)

        toolbar.addSeparator()

        # 清空数据按钮
        self.toolbar_clear = toolbar.addAction("清空数据")
        self.toolbar_clear.setEnabled(False)

        logger.debug("工具栏创建完成")

    def _create_content_area(self) -> QWidget:
        """创建内容区域"""
        # 创建水平分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：测量和控制面板
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(2)

        # 测量面板
        self.measurement_panel = MeasurementPanel(self.settings)
        left_layout.addWidget(self.measurement_panel, 1)

        # 控制面板
        self.control_panel = ControlPanel(self.settings)
        left_layout.addWidget(self.control_panel, 1)

        # 右侧：绘图区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(2)

        self.plot_widget = PlotWidget()
        right_layout.addWidget(self.plot_widget, 1)

        # 添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # 设置分割器初始比例
        splitter.setSizes([400, 600])

        return splitter

    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

        # 初始状态
        self.status_bar.update_connection_status(False)
        self.status_bar.update_measurement_status("未连接")

        logger.debug("状态栏创建完成")

    def _setup_connections(self):
        """设置信号连接"""
        # 菜单栏连接
        self.connect_action.triggered.connect(self.show_connection_dialog)
        self.disconnect_action.triggered.connect(self.disconnect_instrument)
        self.settings_action.triggered.connect(self.show_settings_dialog)

        # 工具栏连接
        self.toolbar_single.triggered.connect(self.measure_single)
        self.toolbar_continuous.triggered.connect(self.start_continuous_measurement)
        self.toolbar_stop.triggered.connect(self.stop_continuous_measurement)
        self.toolbar_clear.triggered.connect(self.clear_measurement_data)

        # 测量面板连接
        self.measurement_panel.measurement_requested.connect(self.measure_single)
        self.measurement_panel.configuration_changed.connect(self.update_measurement_config)

        # 控制面板连接
        self.control_panel.function_changed.connect(self.update_measurement_function)
        self.control_panel.range_changed.connect(self.update_measurement_range)
        self.control_panel.resolution_changed.connect(self.update_measurement_resolution)

        # 自定义信号连接
        self.measurement_received.connect(self.on_measurement_received)
        self.connection_changed.connect(self.on_connection_changed)
        self.error_occurred.connect(self.on_error_occurred)

        logger.debug("信号连接设置完成")

    def _setup_timers(self):
        """设置定时器"""
        # 状态更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # 1秒更新一次

        logger.debug("定时器设置完成")

    def _load_window_settings(self):
        """加载窗口设置"""
        try:
            # 这里可以加载窗口位置、大小等设置
            pass
        except Exception as e:
            logger.warning(f"加载窗口设置失败: {e}")

    def _save_window_settings(self):
        """保存窗口设置"""
        try:
            # 保存当前窗口大小
            self.settings.display.window_width = self.width()
            self.settings.display.window_height = self.height()
            self.settings.save()
        except Exception as e:
            logger.warning(f"保存窗口设置失败: {e}")

    # 公共方法
    def show_connection_dialog(self):
        """显示连接对话框"""
        dialog = ConnectionDialog(self.settings, self)
        if dialog.exec():
            connection_params = dialog.get_connection_params()
            self.connect_instrument(connection_params)

    def show_settings_dialog(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            # 设置已更新，刷新UI
            self.refresh_ui()

    def show_about_dialog(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec()

    def connect_instrument(self, params: dict):
        """连接仪器

        Args:
            params: 连接参数
        """
        try:
            # 创建仪器实例
            self.instrument = Fluke8846AInstrument()

            # 根据接口类型连接
            interface = params.get("interface")
            success = False

            if interface == INTERFACE_SERIAL:
                success = self.instrument.connect_serial(
                    port=params.get("port", "COM3"),
                    baudrate=params.get("baudrate", 9600),
                    timeout=params.get("timeout", 1.0)
                )
            elif interface == INTERFACE_MOCK:
                success = self.instrument.connect_mock(
                    adapter_id=params.get("adapter_id", "fluke8846a_simulator"),
                    base_value=params.get("base_value", 5.0),
                    noise_level=params.get("noise_level", 0.001),
                    response_delay=params.get("response_delay", 50)
                )
            elif interface == INTERFACE_TCP:
                success = self.instrument.connect_tcp(
                    host=params.get("host", "192.168.1.100"),
                    port=params.get("port", DEFAULT_TCP_PORT),
                    timeout=params.get("timeout", 5.0)
                )
            else:
                # VISA连接（GPIB/USB）
                resource_name = params.get("resource_name", "")
                if resource_name:
                    success = self.instrument.connect_visa(
                        resource_name=resource_name,
                        timeout=params.get("timeout", 5000)
                    )

            if success:
                self.connection_changed.emit(True)
                self.status_bar.update_connection_status(True)
                logger.info("仪器连接成功")

                # 更新UI状态
                self._update_ui_connection_state(True)

                # 获取设备信息
                self._update_device_info()
            else:
                self.error_occurred.emit("仪器连接失败")
                self.instrument = None

        except Exception as e:
            self.error_occurred.emit(f"连接仪器时发生错误: {str(e)}")
            logger.error(f"连接仪器失败: {e}")
            self.instrument = None

    def disconnect_instrument(self):
        """断开仪器连接"""
        try:
            if self.instrument:
                self.instrument.disconnect()
                self.instrument = None

            self.connection_changed.emit(False)
            self.status_bar.update_connection_status(False)
            logger.info("仪器已断开连接")

            # 更新UI状态
            self._update_ui_connection_state(False)

        except Exception as e:
            self.error_occurred.emit(f"断开连接时发生错误: {str(e)}")
            logger.error(f"断开连接失败: {e}")

    def measure_single(self):
        """执行单次测量"""
        if not self.instrument or not self.instrument.connected:
            self.error_occurred.emit("仪器未连接")
            return

        try:
            measurement = self.instrument.measure_single()
            if measurement:
                self.measurement_received.emit(measurement)
            else:
                self.error_occurred.emit("测量失败")
        except Exception as e:
            self.error_occurred.emit(f"测量时发生错误: {str(e)}")
            logger.error(f"单次测量失败: {e}")

    def start_continuous_measurement(self):
        """开始连续测量"""
        if not self.instrument or not self.instrument.connected:
            self.error_occurred.emit("仪器未连接")
            return

        try:
            interval = self.settings.measurement.measurement_interval
            success = self.instrument.start_continuous_measurement(interval)
            if success:
                self._update_ui_measurement_state(True)
                logger.info(f"连续测量开始，间隔: {interval}秒")
            else:
                self.error_occurred.emit("启动连续测量失败")
        except Exception as e:
            self.error_occurred.emit(f"启动连续测量时发生错误: {str(e)}")
            logger.error(f"启动连续测量失败: {e}")

    def stop_continuous_measurement(self):
        """停止连续测量"""
        try:
            if self.instrument:
                self.instrument.stop_continuous_measurement()

            self._update_ui_measurement_state(False)
            logger.info("连续测量已停止")
        except Exception as e:
            self.error_occurred.emit(f"停止连续测量时发生错误: {str(e)}")
            logger.error(f"停止连续测量失败: {e}")

    def clear_measurement_data(self):
        """清空测量数据"""
        try:
            if self.instrument:
                self.instrument.clear_history()

            # 清空图表
            self.plot_widget.clear()

            # 清空测量面板显示
            self.measurement_panel.clear_measurements()

            logger.info("测量数据已清空")
        except Exception as e:
            self.error_occurred.emit(f"清空数据时发生错误: {str(e)}")
            logger.error(f"清空数据失败: {e}")

    def update_measurement_config(self, config: dict):
        """更新测量配置

        Args:
            config: 配置字典
        """
        if not self.instrument or not self.instrument.connected:
            return

        try:
            success = self.instrument.configure_measurement(
                function=config.get("function"),
                range_val=config.get("range"),
                resolution=config.get("resolution")
            )

            if not success:
                self.error_occurred.emit("更新测量配置失败")
        except Exception as e:
            self.error_occurred.emit(f"更新测量配置时发生错误: {str(e)}")
            logger.error(f"更新测量配置失败: {e}")

    def update_measurement_function(self, function: str):
        """更新测量功能

        Args:
            function: 测量功能
        """
        self.update_measurement_config({"function": function})

    def update_measurement_range(self, range_val: str):
        """更新测量量程

        Args:
            range_val: 量程
        """
        self.update_measurement_config({"range": range_val})

    def update_measurement_resolution(self, resolution: str):
        """更新测量分辨率

        Args:
            resolution: 分辨率
        """
        self.update_measurement_config({"resolution": resolution})

    # 信号处理器
    def on_measurement_received(self, measurement: MeasurementData):
        """处理测量数据

        Args:
            measurement: 测量数据
        """
        try:
            # 更新测量面板
            self.measurement_panel.add_measurement(measurement)

            # 更新图表
            self.plot_widget.add_data_point(measurement)

            # 更新状态栏
            self.status_bar.update_last_measurement(measurement)

        except Exception as e:
            logger.error(f"处理测量数据失败: {e}")

    def on_connection_changed(self, connected: bool):
        """处理连接状态变化

        Args:
            connected: 是否已连接
        """
        logger.info(f"连接状态变化: {connected}")

    def on_error_occurred(self, error_message: str):
        """处理错误

        Args:
            error_message: 错误消息
        """
        QMessageBox.warning(self, "错误", error_message)
        logger.error(f"发生错误: {error_message}")

    # 辅助方法
    def _update_ui_connection_state(self, connected: bool):
        """更新UI连接状态

        Args:
            connected: 是否已连接
        """
        # 更新菜单项
        self.connect_action.setEnabled(not connected)
        self.disconnect_action.setEnabled(connected)

        # 更新工具栏按钮
        self.toolbar_connect.setEnabled(not connected)
        self.toolbar_disconnect.setEnabled(connected)

        # 更新测量相关控件
        self.single_measure_action.setEnabled(connected)
        self.start_continuous_action.setEnabled(connected)
        self.stop_continuous_action.setEnabled(False)  # 初始状态
        self.clear_data_action.setEnabled(connected)

        self.toolbar_single.setEnabled(connected)
        self.toolbar_continuous.setEnabled(connected)
        self.toolbar_clear.setEnabled(connected)

        # 更新控制面板
        self.control_panel.set_enabled(connected)

        # 更新测量面板
        self.measurement_panel.set_enabled(connected)

    def _update_ui_measurement_state(self, measuring: bool):
        """更新UI测量状态

        Args:
            measuring: 是否正在测量
        """
        # 更新菜单项
        self.start_continuous_action.setEnabled(not measuring)
        self.stop_continuous_action.setEnabled(measuring)

        # 更新工具栏按钮
        self.toolbar_continuous.setEnabled(not measuring)
        self.toolbar_stop.setEnabled(measuring)

    def _update_device_info(self):
        """更新设备信息"""
        if not self.instrument:
            return

        try:
            device_info = self.instrument.get_status().get("device_info", {})
            if device_info:
                info_text = f"{device_info.get('model', 'Unknown')} - {device_info.get('serial_number', 'Unknown')}"
                self.status_bar.update_device_info(info_text)
        except Exception as e:
            logger.warning(f"更新设备信息失败: {e}")

    def update_status(self):
        """更新状态信息"""
        if self.instrument and self.instrument.connected:
            try:
                status = self.instrument.get_status()
                self.status_bar.update_measurement_status(
                    f"模式: {status.get('measurement_mode', 'unknown')}, "
                    f"功能: {status.get('current_function', 'unknown')}"
                )
            except Exception as e:
                logger.warning(f"更新状态失败: {e}")

    def refresh_ui(self):
        """刷新UI"""
        # 重新加载设置并更新UI
        self.settings.load()

        # 更新窗口大小
        self.resize(
            self.settings.display.window_width,
            self.settings.display.window_height
        )

        # 更新其他UI元素
        self.measurement_panel.refresh()
        self.control_panel.refresh()

        logger.info("UI已刷新")

    def cleanup(self):
        """清理资源"""
        try:
            # 停止定时器
            if hasattr(self, 'status_timer'):
                self.status_timer.stop()

            # 断开仪器连接
            self.disconnect_instrument()

            # 保存窗口设置
            self._save_window_settings()

            logger.info("主窗口资源清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.cleanup()
        event.accept()

    def __del__(self):
        """析构函数"""
        try:
            self.cleanup()
        except:
            pass