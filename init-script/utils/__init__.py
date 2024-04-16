import contextlib
import functools
import logging
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import traceback


def once(func):
    """Runs a function only once."""
    results = {}

    def wrapper(*args, **kwargs):
        if func not in results:
            results[func] = func(*args, **kwargs)
        return results[func]

    return wrapper


# shell utils
def rc(s: str, **kwargs):
    """
    rc means run with check.
    """
    logging.debug(colored(f"run: {s}", "yellow"))
    kwargs.setdefault("check", True)
    kwargs.setdefault("shell", True)
    return subprocess.run(s, **kwargs)


def rc_sudo(s: str, **kwargs):
    """
    rc_sudo means run with check, automaticly check sudo needs
    """

    if is_root():
        return rc(s, **kwargs)
    else:
        logging.debug(colored(f"sudo run: {s}", "yellow"))
        kwargs.setdefault("check", True)
        kwargs.setdefault("shell", True)
        return subprocess.run(f"sudo {s}", **kwargs)


def fish(s: str):
    """
    run fish command
    """
    rc(f"fish -c '{s}'")


def exists(s: str) -> bool:
    if s.startswith("/") or s.startswith("~"):
        return pathlib.Path(s).exists()
    else:
        return shutil.which(s) is not None


def is_root() -> bool:
    return os.geteuid() == 0


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
    print(colored(msg, "red"), file=sys.stderr)
    exit(1)


# info utils
@once
def mypath() -> pathlib.Path:
    return pathlib.Path(os.getenv("mypath") or "/absx")


def debug_mode() -> bool:
    return logging.getLogger().isEnabledFor(logging.DEBUG)


def quiet() -> str:
    """
    do you need quiet?
    """
    if debug_mode():
        return ""
    else:
        return "-q"


def trace():
    """
    Trace back only in debug mode.
    """
    if debug_mode():
        traceback.print_exc()


@once
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

    files = ["/etc/os-release", "/etc/redhat-release", "/etc/lsb-release"]
    for file in files:
        with contextlib.suppress(FileNotFoundError):
            with open(file, "r") as f:
                os_info = read_os_info(f)
                break
    assert os_info, "Could not detect OS info."
    return os_info


@once
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
        case "centos":
            return "c"
        case _:
            logging.error(
                f"""found NAME: {get_os_info.get("NAME")}, version: {get_os_info.get("VERSION_ID")}"""
            )
            error_exit("Unsupported OS.")


@once
def kernel_ver():
    _tuple = platform.release().split("-", 1)[0].split(".", 2)
    return int(_tuple[0]) + float(_tuple[1]) / 100


@once
def ip():
    """
    ref: https://stackoverflow.com/a/28950776/18929691
    """
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(("10.254.254.254", 1))
        IP = str(s.getsockname()[0])
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


def update_blog():
    """
    更新博客，如果不存在则自动创建
    """
    blog_path = mypath() / "lxl66566.github.io"
    if not blog_path.exists():
        rc(
            "git clone https://github.com/lxl66566/lxl66566.github.io.git -b main --depth 1",
            cwd=blog_path.parent,
        )
    else:
        rc(
            "git fetch origin main --filter=tree:0 && git reset --hard origin/main",
            cwd=blog_path,
        )


@once
def version():
    return float(get_os_info().get("VERSION_ID") or 0)


@once
def pm():
    for p in ["pacman", "apt", "yum", "dnf"]:
        if exists(p):
            return p[0]


@once
def pm_fullname():
    for p in ["pacman", "apt", "yum", "dnf"]:
        if p.startswith(pm()):
            return p


def log_wrapper(func):
    """
    It's a logging decorator, can print some messages in pre_running and post_running a function.
    """

    @functools.wraps(func)
    def decorator(*args, **kwargs):
        cut()
        logging.info(
            f"called {colored(func.__name__,'green')}"
            + (f" with args: {str(args)}, {str(kwargs)}" if args or kwargs else "")
        )
        result = func(*args, **kwargs)
        logging.info(f"finished {colored(func.__name__,'green')}")
        return result

    return decorator
