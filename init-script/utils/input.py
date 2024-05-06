import os
from functools import wraps

from ..lib.PyConsoleMenu import SelectorMenu
from . import colored


def user_interrupt(func):
    """
    一个装饰器，用于捕获用户中断输入的异常，并打印提示信息。
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print(colored("用户取消输入.", "yellow"))
            exit(0)
        except Exception as e:
            raise e

    return wrapper


@user_interrupt
def user_input(s: str):
    """
    获取用户输入，并返回。
    """
    return input(s)


@user_interrupt
def get_user_choice_classic(options: list[str], title=""):
    # 打印选项列表
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")

    # 获取用户输入
    user_input_value = input(title)

    # 验证用户输入
    while (
        not user_input_value.isdigit()
        or int(user_input_value) < 1
        or int(user_input_value) > len(options)
    ):
        user_input_value = input(colored("输入有误，请输入一个在列表中的数字", "red"))

    return int(user_input_value) - 1


@user_interrupt
def get_user_choice_tui(options: list[str], title=""):
    menu = SelectorMenu(options, title=title)
    return menu.input().index


def get_user_choice(options: list[str], title="请选择需要进行的项目，Ctrl + c 取消："):
    if os.environ.get("DISABLE_TUI"):
        return get_user_choice_classic(options, title)
    else:
        return get_user_choice_tui(options, title)
