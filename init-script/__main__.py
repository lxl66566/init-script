# ruff:  noqa: F403
import logging as log
import shutil

from .install import ask_install_one
from .install import init as install_init
from .install.proxy import reconfig_all_proxies, show_all_status
from .timer import init as timer_init
from .timer import main as timer_main
from .utils import error_exit
from .utils.input import get_user_choice
from .utils.mycache import cache_dir
from .var import ask, reset

options = f"""
ALL（所有软件 + 代理 + 定时）
安装所有软件包
安装单独软件包（手动）
部署定时任务，用于证书与博客更新
* 一键挂机（本人的挂机脚本）
* 代理相关（确保代理已安装）
清除缓存（aka. 删除{cache_dir()}）
立即启动定时脚本（更新证书、博客，重启服务）
""".strip().split("\n")


def afk_options():
    from .afk import init, remove

    match get_user_choice(["安装", "卸载"]):
        case 0:
            init()
            log.info("已部署挂机脚本。")
        case 1:
            remove()
            log.info("已卸载挂机脚本，清理所有容器。")


def reconfig_proxy_options():
    match get_user_choice(
        [
            "重设域名&密码 + 重新配置代理",
            "重新配置代理",
            "查看代理服务运行情况",
        ]
    ):
        case 0:
            reset()
            ask()
            reconfig_all_proxies()
            log.info("已重新配置代理。")
        case 1:
            reconfig_all_proxies()
            log.info("已重新配置代理。")
        case 2:
            show_all_status()


match get_user_choice(
    options, "请选择需要进行的项目，`*` 代表有子条目，Ctrl + c 取消："
):
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
        reconfig_proxy_options()
    case 6:
        try:
            shutil.rmtree(cache_dir())
        except:  # noqa: E722
            error_exit(f"清除缓存失败，请手动删除{str(cache_dir().absolute())}")
        log.info("已清除脚本缓存。")
    case 7:
        timer_main()
    case get_code:
        error_exit(
            f"程序内部错误：获取到不正确的输入码：`{get_code}`，请开启 issue 报告"
        )
