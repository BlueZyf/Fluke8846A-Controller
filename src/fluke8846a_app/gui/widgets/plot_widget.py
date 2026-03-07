"""
绘图组件

使用pyqtgraph显示实时测量数据图表。
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import pyqtgraph as pg
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor

from ...core.measurements import MeasurementData
from ...utils.converters import format_value
from ...config.constants import *


class PlotWidget(QWidget):
    """绘图组件"""

    # 自定义信号
    data_point_added = Signal(MeasurementData)
    plot_cleared = Signal()

    def __init__(self):
        """初始化绘图组件"""
        super().__init__()
        self.data_points: List[MeasurementData] = []
        self.max_points = 1000
        self.plot_colors = {
            MEASUREMENT_DCV: (66, 165, 245),    # 蓝色
            MEASUREMENT_ACV: (255, 112, 67),    # 橙色
            MEASUREMENT_DCI: (102, 187, 106),   # 绿色
            MEASUREMENT_ACI: (171, 71, 188),    # 紫色
            MEASUREMENT_OHM: (255, 193, 7),     # 黄色
            MEASUREMENT_FREQ: (239, 83, 80),    # 红色
        }
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        # 工具栏
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)

        # 绘图区域
        self.plot_widget = self._create_plot_widget()
        main_layout.addWidget(self.plot_widget, 1)

        # 状态栏
        status_bar = self._create_status_bar()
        main_layout.addWidget(status_bar)

    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        # 图表类型
        type_label = QLabel("图表类型:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["折线图", "散点图", "柱状图", "面积图"])
        self.type_combo.setCurrentText("折线图")
        layout.addWidget(type_label)
        layout.addWidget(self.type_combo)

        # 显示设置
        self.grid_check = QCheckBox("显示网格")
        self.grid_check.setChecked(True)
        layout.addWidget(self.grid_check)

        self.legend_check = QCheckBox("显示图例")
        self.legend_check.setChecked(True)
        layout.addWidget(self.legend_check)

        self.auto_scale_check = QCheckBox("自动缩放")
        self.auto_scale_check.setChecked(True)
        layout.addWidget(self.auto_scale_check)

        # 时间范围
        range_label = QLabel("时间范围:")
        self.range_combo = QComboBox()
        self.range_combo.addItems(["1分钟", "5分钟", "10分钟", "30分钟", "1小时", "全部"])
        self.range_combo.setCurrentText("10分钟")
        layout.addWidget(range_label)
        layout.addWidget(self.range_combo)

        # 数据点限制
        points_label = QLabel("最大点数:")
        self.points_spin = QSpinBox()
        self.points_spin.setRange(10, 10000)
        self.points_spin.setValue(self.max_points)
        layout.addWidget(points_label)
        layout.addWidget(self.points_spin)

        layout.addStretch(1)

        # 控制按钮
        self.clear_button = QPushButton("清空图表")
        layout.addWidget(self.clear_button)

        self.export_button = QPushButton("导出图表")
        layout.addWidget(self.export_button)

        return toolbar

    def _create_plot_widget(self) -> pg.PlotWidget:
        """创建绘图部件"""
        # 创建PlotWidget
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground('w')
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        plot_widget.setLabel('left', '值', units='')
        plot_widget.setLabel('bottom', '时间', units='')
        plot_widget.addLegend()

        # 设置抗锯齿
        plot_widget.setAntialiasing(True)

        # 存储引用
        self.pg_plot = plot_widget.getPlotItem()
        self.plot_curves = {}
        self.plot_data = {}

        # 初始化每种测量功能的曲线
        for function in MEASUREMENTS:
            color = self.plot_colors.get(function, (128, 128, 128))
            pen = pg.mkPen(color=color, width=2)

            curve = self.pg_plot.plot(
                [], [],
                pen=pen,
                name=function,
                symbol='o',
                symbolSize=4,
                symbolBrush=color
            )

            self.plot_curves[function] = curve
            self.plot_data[function] = {'time': [], 'value': []}

        return plot_widget

    def _create_status_bar(self) -> QWidget:
        """创建状态栏"""
        status_bar = QWidget()
        layout = QHBoxLayout(status_bar)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(10)

        # 数据统计
        self.count_label = QLabel("点数: 0")
        layout.addWidget(self.count_label)

        self.time_range_label = QLabel("时间范围: --")
        layout.addWidget(self.time_range_label)

        self.value_range_label = QLabel("值范围: --")
        layout.addWidget(self.value_range_label)

        self.mean_label = QLabel("平均值: --")
        layout.addWidget(self.mean_label)

        self.std_label = QLabel("标准差: --")
        layout.addWidget(self.std_label)

        layout.addStretch(1)

        # 当前选择
        self.selection_label = QLabel("选择: 无")
        layout.addWidget(self.selection_label)

        return status_bar

    def _setup_connections(self):
        """设置信号连接"""
        # 工具栏连接
        self.type_combo.currentTextChanged.connect(self._update_plot_type)
        self.grid_check.stateChanged.connect(self._update_grid)
        self.legend_check.stateChanged.connect(self._update_legend)
        self.auto_scale_check.stateChanged.connect(self._update_auto_scale)
        self.range_combo.currentTextChanged.connect(self._update_time_range)
        self.points_spin.valueChanged.connect(self._update_max_points)
        self.clear_button.clicked.connect(self.clear)
        self.export_button.clicked.connect(self.export_plot)

        # 绘图区域信号
        self.pg_plot.scene().sigMouseMoved.connect(self._on_mouse_moved)

    def _update_plot_type(self, plot_type: str):
        """更新图表类型

        Args:
            plot_type: 图表类型
        """
        for function, curve in self.plot_curves.items():
            if plot_type == "折线图":
                curve.setSymbol(None)
                curve.setSymbolSize(0)
            elif plot_type == "散点图":
                curve.setSymbol('o')
                curve.setSymbolSize(4)
                curve.setPen(None)
            elif plot_type == "柱状图":
                # 柱状图需要特殊处理
                pass
            elif plot_type == "面积图":
                curve.setFillLevel(0)

    def _update_grid(self, state: int):
        """更新网格显示

        Args:
            state: 复选框状态
        """
        show_grid = state == Qt.Checked
        self.pg_plot.showGrid(x=show_grid, y=show_grid, alpha=0.3)

    def _update_legend(self, state: int):
        """更新图例显示

        Args:
            state: 复选框状态
        """
        show_legend = state == Qt.Checked
        if show_legend:
            self.pg_plot.addLegend()
        else:
            self.pg_plot.legend.clear()

    def _update_auto_scale(self, state: int):
        """更新自动缩放

        Args:
            state: 复选框状态
        """
        auto_scale = state == Qt.Checked
        if auto_scale:
            self.pg_plot.enableAutoRange()
        else:
            self.pg_plot.disableAutoRange()

    def _update_time_range(self, time_range: str):
        """更新时间范围

        Args:
            time_range: 时间范围字符串
        """
        self._update_plot()

    def _update_max_points(self, max_points: int):
        """更新最大点数

        Args:
            max_points: 最大点数
        """
        self.max_points = max_points
        self._trim_data()

    def _on_mouse_moved(self, pos):
        """鼠标移动事件

        Args:
            pos: 鼠标位置
        """
        if self.pg_plot.sceneBoundingRect().contains(pos):
            mouse_point = self.pg_plot.vb.mapSceneToView(pos)
            x_val = mouse_point.x()
            y_val = mouse_point.y()

            # 查找最近的数据点
            closest_point = None
            min_distance = float('inf')

            for measurement in self.data_points[-100:]:  # 只检查最近100个点
                time_val = measurement.timestamp.timestamp()
                distance = abs(time_val - x_val) + abs(measurement.value - y_val) * 0.1

                if distance < min_distance:
                    min_distance = distance
                    closest_point = measurement

            if closest_point and min_distance < 10:  # 阈值
                self.selection_label.setText(
                    f"选择: {closest_point.timestamp.strftime('%H:%M:%S')} "
                    f"{closest_point.function}: {format_value(closest_point.value, precision=6)} {closest_point.unit}"
                )
            else:
                self.selection_label.setText(
                    f"位置: {datetime.fromtimestamp(x_val).strftime('%H:%M:%S') if x_val > 0 else '--:--:--'}, "
                    f"值: {format_value(y_val, precision=6) if y_val else '--'}"
                )

    # 公共方法
    def add_data_point(self, measurement: MeasurementData):
        """添加数据点

        Args:
            measurement: 测量数据
        """
        # 添加到数据列表
        self.data_points.append(measurement)

        # 添加到对应函数的数据集
        function = measurement.function
        if function not in self.plot_data:
            # 如果函数不存在，创建新的数据集
            color = self.plot_colors.get(function, (128, 128, 128))
            pen = pg.mkPen(color=color, width=2)

            curve = self.pg_plot.plot(
                [], [],
                pen=pen,
                name=function,
                symbol='o',
                symbolSize=4,
                symbolBrush=color
            )

            self.plot_curves[function] = curve
            self.plot_data[function] = {'time': [], 'value': []}

        # 添加数据
        self.plot_data[function]['time'].append(measurement.timestamp.timestamp())
        self.plot_data[function]['value'].append(measurement.value)

        # 修剪数据
        self._trim_data()

        # 更新图表
        self._update_plot()

        # 更新状态
        self._update_status()

        # 发射信号
        self.data_point_added.emit(measurement)

    def clear(self):
        """清空图表"""
        # 清空数据
        self.data_points.clear()
        for function in self.plot_data:
            self.plot_data[function]['time'].clear()
            self.plot_data[function]['value'].clear()

        # 清空曲线
        for curve in self.plot_curves.values():
            curve.setData([], [])

        # 更新状态
        self._update_status()

        # 发射信号
        self.plot_cleared.emit()

    def export_plot(self):
        """导出图表"""
        # 这里可以添加导出功能
        # 例如保存为图片或数据文件
        pass

    def set_data(self, measurements: List[MeasurementData]):
        """设置数据

        Args:
            measurements: 测量数据列表
        """
        self.clear()
        for measurement in measurements:
            self.add_data_point(measurement)

    def get_plot_data(self) -> Dict[str, Any]:
        """获取绘图数据

        Returns:
            绘图数据字典
        """
        return {
            'data_points': self.data_points.copy(),
            'plot_data': self.plot_data.copy(),
            'max_points': self.max_points
        }

    # 私有方法
    def _trim_data(self):
        """修剪数据"""
        # 修剪总数据点
        if len(self.data_points) > self.max_points:
            remove_count = len(self.data_points) - self.max_points
            self.data_points = self.data_points[remove_count:]

        # 修剪每个函数的数据
        for function in self.plot_data:
            times = self.plot_data[function]['time']
            values = self.plot_data[function]['value']

            if len(times) > self.max_points:
                remove_count = len(times) - self.max_points
                self.plot_data[function]['time'] = times[remove_count:]
                self.plot_data[function]['value'] = values[remove_count:]

    def _update_plot(self):
        """更新图表"""
        for function, curve in self.plot_curves.items():
            times = self.plot_data[function]['time']
            values = self.plot_data[function]['value']

            if times:
                # 应用时间范围过滤
                filtered_times, filtered_values = self._filter_by_time_range(times, values)

                if filtered_times:
                    curve.setData(filtered_times, filtered_values)
                else:
                    curve.setData([], [])
            else:
                curve.setData([], [])

    def _filter_by_time_range(self, times: List[float], values: List[float]) -> tuple:
        """按时间范围过滤数据

        Args:
            times: 时间列表
            values: 值列表

        Returns:
            (过滤后的时间列表, 过滤后的值列表)
        """
        if not times:
            return [], []

        time_range = self.range_combo.currentText()
        now = datetime.now().timestamp()

        if time_range == "全部":
            return times, values

        # 计算时间范围
        if time_range == "1分钟":
            min_time = now - 60
        elif time_range == "5分钟":
            min_time = now - 300
        elif time_range == "10分钟":
            min_time = now - 600
        elif time_range == "30分钟":
            min_time = now - 1800
        elif time_range == "1小时":
            min_time = now - 3600
        else:
            min_time = times[0]  # 默认使用最早时间

        # 过滤数据
        filtered_times = []
        filtered_values = []

        for t, v in zip(times, values):
            if t >= min_time:
                filtered_times.append(t)
                filtered_values.append(v)

        return filtered_times, filtered_values

    def _update_status(self):
        """更新状态栏"""
        # 数据点数
        total_points = len(self.data_points)
        self.count_label.setText(f"点数: {total_points}")

        if total_points == 0:
            self.time_range_label.setText("时间范围: --")
            self.value_range_label.setText("值范围: --")
            self.mean_label.setText("平均值: --")
            self.std_label.setText("标准差: --")
            return

        # 时间范围
        first_time = self.data_points[0].timestamp
        last_time = self.data_points[-1].timestamp
        time_diff = last_time - first_time

        if time_diff.total_seconds() < 60:
            time_str = f"{time_diff.total_seconds():.1f}秒"
        elif time_diff.total_seconds() < 3600:
            time_str = f"{time_diff.total_seconds()/60:.1f}分钟"
        else:
            time_str = f"{time_diff.total_seconds()/3600:.1f}小时"

        self.time_range_label.setText(f"时间范围: {time_str}")

        # 值范围
        values = [m.value for m in self.data_points]
        min_val = min(values)
        max_val = max(values)
        self.value_range_label.setText(f"值范围: {format_value(min_val)} ~ {format_value(max_val)}")

        # 统计信息
        mean_val = np.mean(values)
        std_val = np.std(values)
        self.mean_label.setText(f"平均值: {format_value(mean_val, precision=6)}")
        self.std_label.setText(f"标准差: {format_value(std_val, precision=6)}")

    def resizeEvent(self, event):
        """重设大小事件"""
        super().resizeEvent(event)
        # 可以在这里调整图表大小等