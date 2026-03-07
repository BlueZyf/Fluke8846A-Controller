"""
应用设置管理
"""

import json
from typing import Any, Dict, Optional
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime

from .constants import *
from .paths import paths


@dataclass
class DeviceSettings:
    """设备设置"""
    interface: str = INTERFACE_GPIB
    gpib_address: int = 22
    usb_vendor_id: str = "0x1234"
    usb_product_id: str = "0x5678"
    serial_port: str = "COM3"
    serial_baudrate: int = 9600
    timeout: int = DEFAULT_TIMEOUT


@dataclass
class MeasurementSettings:
    """测量设置"""
    default_function: str = MEASUREMENT_DCV
    default_range: str = RANGE_AUTO
    default_resolution: str = RESOLUTION_6_5
    sample_count: int = DEFAULT_SAMPLE_COUNT
    measurement_interval: float = DEFAULT_INTERVAL
    auto_record: bool = False
    log_format: str = EXT_CSV


@dataclass
class DisplaySettings:
    """显示设置"""
    theme: str = THEME_LIGHT
    language: str = LANGUAGE_ZH_CN
    window_width: int = 1200
    window_height: int = 800
    show_grid: bool = True
    auto_scale: bool = True
    refresh_rate: int = 1000  # 毫秒


@dataclass
class AppSettings:
    """应用设置"""
    device: DeviceSettings = field(default_factory=DeviceSettings)
    measurement: MeasurementSettings = field(default_factory=MeasurementSettings)
    display: DisplaySettings = field(default_factory=DisplaySettings)

    # 元数据
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = APP_VERSION

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "device": asdict(self.device),
            "measurement": asdict(self.measurement),
            "display": asdict(self.display),
            "last_modified": self.last_modified,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """从字典创建实例"""
        settings = cls()

        if "device" in data:
            device_data = data["device"]
            settings.device = DeviceSettings(**device_data)

        if "measurement" in data:
            measurement_data = data["measurement"]
            settings.measurement = MeasurementSettings(**measurement_data)

        if "display" in data:
            display_data = data["display"]
            settings.display = DisplaySettings(**display_data)

        if "last_modified" in data:
            settings.last_modified = data["last_modified"]

        if "version" in data:
            settings.version = data["version"]

        return settings

    def save(self, filepath: Optional[Path] = None) -> bool:
        """保存设置到文件"""
        try:
            if filepath is None:
                filepath = paths.settings_file

            # 更新修改时间
            self.last_modified = datetime.now().isoformat()

            # 转换为字典并保存
            data = self.to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"保存设置失败: {e}")
            return False

    def load(self, filepath: Optional[Path] = None) -> bool:
        """从文件加载设置"""
        try:
            if filepath is None:
                filepath = paths.settings_file

            if not filepath.exists():
                print(f"设置文件不存在: {filepath}")
                return False

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 更新当前实例
            loaded_settings = self.from_dict(data)
            self.__dict__.update(loaded_settings.__dict__)

            return True

        except json.JSONDecodeError as e:
            print(f"设置文件格式错误: {e}")
            return False
        except Exception as e:
            print(f"加载设置失败: {e}")
            return False

    def reset_to_defaults(self):
        """重置为默认设置"""
        self.device = DeviceSettings()
        self.measurement = MeasurementSettings()
        self.display = DisplaySettings()
        self.last_modified = datetime.now().isoformat()
        self.version = APP_VERSION