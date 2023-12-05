import os
import subprocess
from pathlib import Path
from shutil import which


def rc(s: str, **kwargs):
    """
    rc means run with check.
    """

    return subprocess.run(s, shell=True, check=True, **kwargs)


def rc_sudo(s: str, **kwargs):
    """
    rc_sudo means run with check, automaticly check sudo needs
    """

    return subprocess.run(
        "" if is_root() else "sudo " + s, shell=True, check=True, **kwargs
    )


def exists(s: str) -> bool:
    if s.startswith("/") or s.startswith("~"):
        return Path(s).exists()
    else:
        return which(s) is not None


def is_service_running(service_name: str):
    """
    检查服务是否正在运行
    :param service_name: 待检查的服务名
    :return: 如果服务正在运行返回 True，否则返回 False
    """
    cmd = ["systemctl", "is-active", service_name]
    output = subprocess.check_output(cmd).decode().strip()
    return output == "active"


def is_root():
    return os.geteuid() == 0


def current_dir():
    return os.path.dirname(os.path.realpath(__file__))


def colored(msg: str, color: str):
    match color:
        case "red":
            prefix = "\033[0;31;31m"
        case "green":
            prefix = "\033[0;31;32m"
        case "yellow":
            prefix = "\033[0;31;33m"
        case "blue":
            prefix = "\033[0;31;36m"
        case _:
            prefix = ""
    return f"{prefix}{msg}\033[0m"


def cut():
    print("-" * 70)


def error_exit(msg: str):
    print(colored(msg, "red"))
    exit(1)
