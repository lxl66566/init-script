import os
from functools import lru_cache

from utils import error_exit, exists


@lru_cache
def mypath():
    return os.getenv("mypath") or "/absx"


@lru_cache
def debug_mode():
    return os.getenv("debug")


@lru_cache
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
        with suppress(FileNotFoundError):
            with open(file, "r") as f:
                os_info = read_os_info(f)
                break
    assert os_info, "Could not detect OS info."
    return os_info


@lru_cache
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


@lru_cache
def version():
    return float(get_os_info().get("VERSION_ID")) or 0


@lru_cache
def pm():
    if exists("pacman"):
        return "p"
    elif exists("apt"):
        return "a"
    elif exists("yum"):
        return "y"
    elif exists("dnf"):
        return "d"
