# ruff:  noqa: F403
import logging
import shutil

from .install import ask_install_one
from .install import init as install_init
from .install.proxy import reconfig_all_proxies
from .timer import init as timer_init
from .timer import main as timer_main
from .utils import error_exit
from .utils.input import get_user_choice
from .utils.mycache import cache_dir
from .utils.service import show_all_status

options = f"""
ALL（所有软件 + 代理 + 定时）
安装所有软件包
安装单独软件包（手动）
部署定时任务，用于证书与博客更新
一键挂机（本人的挂机脚本）
查看代理服务运行情况，重启失败服务
重新配置代理（需要代理已安装）
清除缓存（aka. 删除{cache_dir()}）
立即启动定时脚本（更新证书、博客，重启服务）
""".strip().split("\n")


def afk_options():
    from .afk import init, remove

    match get_user_choice(["安装", "卸载"]):
        case 0:
            init()
            logging.info("已部署挂机脚本。")
        case 1:
            remove()
            logging.info("已卸载挂机脚本，清理所有容器。")


match get_user_choice(options):
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
        afk_options()
    case 5:
        show_all_status()
    case 6:
        reconfig_all_proxies()
    case 7:
        try:
            shutil.rmtree(cache_dir())
        except:  # noqa: E722
            error_exit(f"清除缓存失败，请手动删除{str(cache_dir().absolute())}")
        logging.info("已清除脚本缓存。")
    case 8:
        timer_main()
    case get_code:
        error_exit(
            f"程序内部错误：获取到不正确的输入码：`{get_code}`，请开启 issue 报告"
        )
