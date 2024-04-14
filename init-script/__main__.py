# ruff:  noqa: F403
import logging
import shutil

from .install import ask_install_one
from .install import init as install_init
from .lib.PyConsoleMenu import SelectorMenu
from .proxy import show_all_status
from .timer import init as timer_init
from .utils import error_exit
from .utils.mycache import mycache

options = """
ALL（所有软件 + 代理 + 定时）
安装所有软件包
安装单独软件包（手动）
部署定时任务，用于证书与博客更新
一键挂机（本人的挂机脚本）
查看代理服务运行情况
清除脚本缓存
""".strip().split("\n")

menu = SelectorMenu(options, title="请选择需要进行的项目：")
ans = menu.input()

match ans.index:
    case 0:
        install_init()
        timer_init()
    case 1:
        install_init()
    case 2:
        ask_install_one()
    case 3:
        timer_init()
    case 4:
        from .afk import init

        init()
    case 5:
        show_all_status()
    case 6:
        shutil.rmtree(
            mycache.cache_dir(),
            onerror=lambda *args: error_exit(
                f"清除缓存失败，请手动删除{str(mycache.cache_dir().absolute())}"
            ),
        )
        logging.info("已清除脚本缓存。")
    case _:
        error_exit("输入有误，程序内部错误")
