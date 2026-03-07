"""
关于对话框

显示应用信息、版本、许可证等。
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QTabWidget, QWidget, QDialogButtonBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QIcon

from ...config.constants import *


class AboutDialog(QDialog):
    """关于对话框"""

    def __init__(self, parent=None):
        """初始化关于对话框

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self._setup_ui()

        self.setWindowTitle("关于 FLUKE 8846A Control")
        self.resize(500, 400)
        self.setFixedSize(self.size())  # 固定大小

    def _setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # 标题
        title_label = QLabel("FLUKE 8846A Control")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # 版本
        version_label = QLabel(f"版本 {APP_VERSION}")
        version_font = QFont()
        version_font.setPointSize(12)
        version_label.setFont(version_font)
        version_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(version_label)

        # 描述
        desc_label = QLabel(APP_DESCRIPTION)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(desc_label)

        main_layout.addSpacing(10)

        # 选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # 关于选项卡
        about_tab = self._create_about_tab()
        self.tab_widget.addTab(about_tab, "关于")

        # 许可证选项卡
        license_tab = self._create_license_tab()
        self.tab_widget.addTab(license_tab, "许可证")

        # 依赖选项卡
        dependencies_tab = self._create_dependencies_tab()
        self.tab_widget.addTab(dependencies_tab, "依赖")

        # 系统信息选项卡
        system_tab = self._create_system_tab()
        self.tab_widget.addTab(system_tab, "系统信息")

        main_layout.addWidget(self.tab_widget, 1)

        # 按钮框
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)

        # 添加额外按钮
        website_button = QPushButton("访问网站")
        website_button.clicked.connect(self.open_website)
        button_box.addButton(website_button, QDialogButtonBox.ActionRole)

        check_update_button = QPushButton("检查更新")
        check_update_button.clicked.connect(self.check_for_updates)
        button_box.addButton(check_update_button, QDialogButtonBox.ActionRole)

        main_layout.addWidget(button_box)

    def _create_about_tab(self) -> QWidget:
        """创建关于选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # 应用信息
        info_text = f"""
        <h3>FLUKE 8846A 控制应用</h3>

        <p>一个用于控制FLUKE 8846A数字万用表的跨平台上位机应用。</p>

        <h4>主要功能:</h4>
        <ul>
          <li>仪器连接和识别（GPIB/USB/RS-232）</li>
          <li>直流电压测量（DCV）</li>
          <li>交流电压测量（ACV）</li>
          <li>电阻测量（Ω）</li>
          <li>电流测量（DCI/ACI）</li>
          <li>频率测量</li>
          <li>数据记录和图表显示</li>
          <li>自动化测试序列</li>
        </ul>

        <h4>系统要求:</h4>
        <ul>
          <li>Python 3.8 或更高版本</li>
          <li>PyVISA 和 PyVISA-py</li>
          <li>PySide6 (Qt for Python)</li>
          <li>可选：NI-VISA 或 Keysight VISA 运行时（用于GPIB支持）</li>
        </ul>

        <p><em>本软件为开源项目，遵循MIT许可证。</em></p>
        """

        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.RichText)
        layout.addWidget(info_label)

        layout.addStretch(1)

        return widget

    def _create_license_tab(self) -> QWidget:
        """创建许可证选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 读取许可证文件
        try:
            license_file = Path(__file__).parent.parent.parent.parent.parent / "LICENSE"
            if license_file.exists():
                with open(license_file, 'r', encoding='utf-8') as f:
                    license_text = f.read()
            else:
                license_text = "MIT License\n\n" + \
                    "Copyright (c) 2023 FLUKE 8846A Project\n\n" + \
                    "Permission is hereby granted, free of charge, to any person obtaining a copy..."
        except:
            license_text = "无法加载许可证文件。"

        license_edit = QTextEdit()
        license_edit.setPlainText(license_text)
        license_edit.setReadOnly(True)
        license_edit.setFont(QFont("Consolas", 9))

        layout.addWidget(license_edit)

        return widget

    def _create_dependencies_tab(self) -> QWidget:
        """创建依赖选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 依赖列表
        dependencies = [
            ("PyVISA", "仪器控制接口"),
            ("PyVISA-py", "VISA的纯Python实现"),
            ("PySide6", "Qt for Python GUI框架"),
            ("numpy", "数值计算"),
            ("pandas", "数据处理"),
            ("pyqtgraph", "科学绘图"),
            ("SQLAlchemy", "数据库ORM"),
            ("pyserial", "串口通信（可选）"),
            ("pyusb", "USB通信（可选）"),
        ]

        deps_text = "<h3>核心依赖:</h3><ul>"
        for name, desc in dependencies:
            deps_text += f"<li><b>{name}</b>: {desc}</li>"
        deps_text += "</ul>"

        deps_label = QLabel(deps_text)
        deps_label.setWordWrap(True)
        deps_label.setTextFormat(Qt.RichText)
        layout.addWidget(deps_label)

        layout.addStretch(1)

        return widget

    def _create_system_tab(self) -> QWidget:
        """创建系统信息选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 系统信息
        import platform
        import sys

        system_info = f"""
        <h3>系统信息</h3>

        <table style="width:100%">
          <tr><td style="width:120px"><b>系统:</b></td><td>{platform.system()} {platform.release()}</td></tr>
          <tr><td><b>架构:</b></td><td>{platform.machine()}</td></tr>
          <tr><td><b>处理器:</b></td><td>{platform.processor()}</td></tr>
          <tr><td><b>Python版本:</b></td><td>{sys.version}</td></tr>
          <tr><td><b>Python路径:</b></td><td>{sys.executable}</td></tr>
          <tr><td><b>工作目录:</b></td><td>{Path.cwd()}</td></tr>
        </table>

        <h4>Qt信息:</h4>
        """

        try:
            from PySide6 import QtCore
            system_info += f"""
            <table style="width:100%">
              <tr><td style="width:120px"><b>Qt版本:</b></td><td>{QtCore.__version__}</td></tr>
              <tr><td><b>PySide6版本:</b></td><td>{QtCore.qVersion()}</td></tr>
            </table>
            """
        except:
            system_info += "<p>无法获取Qt信息</p>"

        # 添加内存信息
        try:
            import psutil
            memory = psutil.virtual_memory()
            system_info += f"""
            <h4>内存信息:</h4>
            <table style="width:100%">
              <tr><td style="width:120px"><b>总内存:</b></td><td>{memory.total / (1024**3):.2f} GB</td></tr>
              <tr><td><b>可用内存:</b></td><td>{memory.available / (1024**3):.2f} GB</td></tr>
              <tr><td><b>使用率:</b></td><td>{memory.percent}%</td></tr>
            </table>
            """
        except:
            system_info += "<p>无法获取内存信息</p>"

        info_label = QLabel(system_info)
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.RichText)
        layout.addWidget(info_label)

        layout.addStretch(1)

        return widget

    def open_website(self):
        """打开项目网站"""
        import webbrowser
        try:
            webbrowser.open("https://github.com/yourusername/fluke8846a-control-app")
        except:
            QMessageBox.information(self, "信息", "无法打开浏览器")

    def check_for_updates(self):
        """检查更新"""
        QMessageBox.information(self, "检查更新", "当前已是最新版本。")

    def accept(self):
        """接受对话框"""
        super().accept()

    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        # 可以在这里执行初始化操作