import logging
import shutil

import afk
import install
import proxy
import utils.mycache as mycache

from .timer import init as timer_init
from .utils import colored, cut, error_exit


def ask() -> int:
    cut()
    print(
        """
1. ALL (2 + 4 + 5)
2. 安装所有推荐软件包
3. 安装软件包（手动）
4. 部署代理（前置：2）
5. 部署定时任务，用于证书与博客更新（前置：4）
6. 一键挂机（本人的挂机脚本）
"""
    )
    cut()
    print(
        """
7. 查看代理服务运行情况（前置：4）
8. 清除脚本缓存
"""
    )
    cut()
    while True:
        try:
            choice = input("输入执行序号：").strip()
            if not choice:
                raise KeyboardInterrupt
            return int(choice)
        except KeyboardInterrupt:
            error_exit("程序终止。")
        except ValueError:
            print(colored("输入有误，请重新输入", "red"))


if __name__ == "__main__":
    match ask():
        case 1:
            install.init()
            proxy.init()
            timer_init()
            afk.init()
        case 2:
            install.init()
        case 3:
            install.show_all_available_packages()
            temp = (
                input("请输入安装软件名，以空格隔开，输入 -y 无视缓存安装：")
                .strip()
                .split(" ")
            )
            flag = False
            if "-y" in temp:
                temp.remove("-y")
                flag = True
            for i in temp:
                install.install_one(i, flag)
        case 4:
            proxy.init()
        case 5:
            timer_init()
        case 6:
            afk.init()
        case 7:
            proxy.show_all_status()
        case 8:
            shutil.rmtree(
                mycache.cache_dir(),
                onerror=lambda *args: error_exit(
                    f"清除缓存失败，请手动删除{str(mycache.cache_dir().absolute())}"
                ),
            )
            logging.info("已清除脚本缓存。")
        case _:
            error_exit("输入有误。")
