import contextlib
import functools
import logging
import os
import pathlib
import shutil
import subprocess


def rc(s: str, **kwargs):
    """
    rc means run with check.
    """
    logging.debug(colored(f"run: {s}", "yellow"))
    return subprocess.run(s, shell=True, check=True, **kwargs)


def rc_sudo(s: str, **kwargs):
    """
    rc_sudo means run with check, automaticly check sudo needs
    """

    if is_root():
        return rc(s, **kwargs)
    else:
        logging.debug(colored(f"sudo run: {s}", "yellow"))
        return subprocess.run(f"sudo {s}", shell=True, check=True, **kwargs)


def exists(s: str) -> bool:
    if s.startswith("/") or s.startswith("~"):
        return pathlib.Path(s).exists()
    else:
        return shutil.which(s) is not None


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


# info utils
@functools.lru_cache
def mypath():
    return os.getenv("mypath") or "/absx"


@functools.lru_cache
def debug_mode():
    return os.getenv("debug")


@functools.lru_cache
def get_os_info() -> dict:
    def read_os_info(f):
        """f is an opened file"""
        os_info = {}
        for line in f:
            line = line.strip()
            if not line:
                continue
            key, separator, value = line and line.partition("=")
            if key and separator and value:
                os_info[key.strip()] = value.strip().strip('"')
        return os_info

    files = ["/etc/os-release"]  # , "/etc/redhat-release", "/etc/lsb-release"
    for file in files:
        with contextlib.suppress(FileNotFoundError):
            with open(file, "r") as f:
                os_info = read_os_info(f)
                break
    assert os_info, "Could not detect OS info."
    return os_info


@functools.lru_cache
def distro():
    os_name = str(get_os_info().get("NAME")).split(maxsplit=1)[0].lower()
    match os_name:
        case "arch":
            return "a"
        case "debian":
            return "d"
        case "ubuntu":
            return "u"
        case "almalinux":
            return "al"
        case _:
            logging.error(
                f"""found NAME: {os_info.get("NAME")}, version: {os_info.get("VERSION_ID")}"""
            )
            error_exit("Unsupported OS.")


@functools.lru_cache
def version():
    return float(get_os_info().get("VERSION_ID") or 0)


@functools.lru_cache
def pm():
    if exists("pacman"):
        return "p"
    elif exists("apt"):
        return "a"
    elif exists("yum"):
        return "y"
    elif exists("dnf"):
        return "d"
