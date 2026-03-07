"""
应用路径管理
"""

from pathlib import Path
import sys


class AppPaths:
    """应用路径管理类"""

    def __init__(self):
        # 项目根目录
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件所在目录
            self.project_root = Path(sys.executable).parent
        else:
            # 开发时源码所在目录
            self.project_root = Path(__file__).parent.parent.parent.parent

        # 数据目录
        self.data_dir = self.project_root / "data"
        self.config_dir = self.data_dir / "config"
        self.logs_dir = self.data_dir / "logs"
        self.measurements_dir = self.data_dir / "measurements"

        # 资源目录
        self.resources_dir = self.project_root / "resources"
        self.icons_dir = self.resources_dir / "icons"
        self.images_dir = self.resources_dir / "images"
        self.translations_dir = self.resources_dir / "translations"

        # 样式目录
        self.styles_dir = self.project_root / "src" / "fluke8846a_app" / "gui" / "styles"

        # 确保所有目录存在
        self._ensure_directories()

    def _ensure_directories(self):
        """确保所有必要的目录存在"""
        directories = [
            self.data_dir,
            self.config_dir,
            self.logs_dir,
            self.measurements_dir,
            self.resources_dir,
            self.icons_dir,
            self.images_dir,
            self.translations_dir,
            self.styles_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_config_file(self, filename: str) -> Path:
        """获取配置文件路径"""
        return self.config_dir / filename

    def get_log_file(self, filename: str) -> Path:
        """获取日志文件路径"""
        return self.logs_dir / filename

    def get_measurement_file(self, filename: str) -> Path:
        """获取测量数据文件路径"""
        return self.measurements_dir / filename

    def get_icon_path(self, icon_name: str) -> Path:
        """获取图标文件路径"""
        return self.icons_dir / icon_name

    def get_image_path(self, image_name: str) -> Path:
        """获取图片文件路径"""
        return self.images_dir / image_name

    def get_style_file(self, theme: str) -> Path:
        """获取样式表文件路径"""
        return self.styles_dir / f"{theme}.qss"

    def get_translation_file(self, language: str) -> Path:
        """获取翻译文件路径"""
        return self.translations_dir / f"{language}.qm"

    @property
    def settings_file(self) -> Path:
        """获取设置文件路径"""
        return self.config_dir / "settings.json"

    @property
    def default_log_file(self) -> Path:
        """获取默认日志文件路径"""
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        return self.logs_dir / f"app_{date_str}.log"


# 全局路径实例
paths = AppPaths()