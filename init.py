#!/usr/bin/env python
#
# My linux init script.
#
# https://github.com/lxl66566/init-script

import json
import os
import platform
from configparser import ConfigParser
from contextlib import suppress
from shutil import which
from subprocess import run

os_info = {}
configparser = ConfigParser()


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


def check_package_manager() -> bool:
    match os_info["NAME"]:
        case "Arch Linux":
            return which("paru") is not None


def install(pac: list):
    def install_paru():
        assert os_info["NAME"] == "Arch Linux", "Only support Arch Linux"

        # install base-devel
        if which("makepkg") is None:
            run(
                ("sudo", "pacman", "-S", "--needed", "--noconfirm", "base-devel"),
                check=True,
            )
        assert which("makepkg") is not None, "Makepkg not found"

        run(("mkdir", "-p", "/tmp/init_script"), check=True)
        run(
            ("git", "clone", "https://aur.archlinux.org/paru-bin.git", "--depth=1"),
            cwd="/tmp/init_script",
            check=True,
        )
        run(("sudo", "makepkg", "-si"), check=True)

    match os_info["NAME"]:
        case "Arch Linux":
            if not check_package_manager():
                install_paru()
            assert check_package_manager(), "Package manager can not be installed."

            os.system("yes | paru -Syu --needed " + " ".join(pac))


def info():
    def read_os_info(f):
        """f is an opened file"""
        global os_info
        for line in f:
            line = line.strip()
            if not line:
                continue
            key, separator, value = line and line.partition("=")
            if key and separator and value:
                os_info[key.strip()] = value.strip()

    global distro
    files = ("/etc/os-release", "/etc/redhat-release", "/etc/lsb-release")
    for file in files:
        with suppress():
            with open(file, "r") as f:
                read_os_info(f)
    assert os_info, "Could not detect OS info."


def system_check():
    if os.name != "posix" or platform.system() != "Linux":
        error_exit("This script is only for Linux.")
    if os.geteuid() != 0:
        error_exit("This script must be run as root.")
    if which("git") is None:
        error_exit("git must be installed.")
    info()
    match os_info["NAME"]:
        case "Arch Linux":
            if which("pacman") is None:
                error_exit("pacman must be installed.")


def init():
    cut()
    print("""init-script by https://github.com/lxl66566/init-script""")
    cut()


if __name__ == "__main__":
    init()
