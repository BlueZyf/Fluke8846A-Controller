"""
FLUKE 8846A控制应用 - 主应用类
"""

import sys
from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from .gui.main_window import MainWindow
from .config.settings import AppSettings
from .utils.logger import get_logger


logger = get_logger(__name__)


class Fluke8846AApp:
    """主应用类"""

    def __init__(self):
        """初始化应用"""
        self.app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.settings = AppSettings()

    def setup_application(self) -> bool:
        """设置Qt应用"""
        try:
            # 创建Qt应用
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("FLUKE 8846A Control")
            self.app.setApplicationVersion("0.1.0")
            self.app.setOrganizationName("FLUKE 8846A Project")

            # 设置样式
            self._setup_styles()

            # 创建主窗口
            self.main_window = MainWindow(self.settings)
            self.main_window.show()

            logger.info("应用初始化完成")
            return True

        except Exception as e:
            logger.error(f"应用初始化失败: {e}")
            return False

    def _setup_styles(self):
        """设置应用样式"""
        try:
            # 加载样式表
            style_file = Path(__file__).parent / "gui" / "styles" / "light.qss"
            if style_file.exists():
                with open(style_file, 'r', encoding='utf-8') as f:
                    style_sheet = f.read()
                    self.app.setStyleSheet(style_sheet)
                    logger.debug("样式表加载成功")
        except Exception as e:
            logger.warning(f"样式表加载失败: {e}")

    def run(self) -> int:
        """运行应用"""
        try:
            logger.info("启动FLUKE 8846A控制应用")

            # 设置应用
            if not self.setup_application():
                return 1

            # 运行主循环
            exit_code = self.app.exec()

            logger.info(f"应用退出，代码: {exit_code}")
            return exit_code

        except Exception as e:
            logger.error(f"应用运行错误: {e}")
            return 1

    def cleanup(self):
        """清理资源"""
        try:
            if self.main_window:
                self.main_window.cleanup()
            logger.info("应用资源清理完成")
        except Exception as e:
            logger.error(f"应用清理错误: {e}")

    @staticmethod
    def process_events():
        """处理挂起的事件"""
        if QApplication.instance():
            QApplication.instance().processEvents()