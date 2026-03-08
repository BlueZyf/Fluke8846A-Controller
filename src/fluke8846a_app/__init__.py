"""
FLUKE 8846A 控制应用包

一个用于控制FLUKE 8846A数字万用表的跨平台上位机应用。
"""

__version__ = "0.1.0"
__author__ = "FLUKE 8846A Control App Developers"
__email__ = ""

from .main import main
from .app import Fluke8846AApp

#控制 import * 的行为
__all__ = ["main", "Fluke8846AApp", "__version__"]  