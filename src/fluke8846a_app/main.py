"""
FLUKE 8846A控制应用 - 主入口点
"""

import sys
import signal
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fluke8846a_app.app import Fluke8846AApp
from fluke8846a_app.utils.logger import setup_logging


def setup_signal_handlers():
    """设置信号处理"""
    def signal_handler(sig, frame):
        print("\n接收到中断信号，正在关闭应用...")
        sys.exit(0)

    # SIGINT   2   Ctrl+C    终止程序 触发后调用我的函数signal_handler
    # SIGTERM  15  kill命令  终止程序 触发后调用我的函数signal_handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """应用主函数"""
    # 设置信号处理
    setup_signal_handlers()

    # 设置日志
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir)

    # 创建并运行应用
    app = Fluke8846AApp()

    try:
        exit_code = app.run()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n应用被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"应用运行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()