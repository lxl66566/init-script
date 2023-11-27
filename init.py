#!/usr/bin/env python
#
# My linux init script.
#
# https://github.com/lxl66566/init-script

import json
import os
import platform
from contextlib import suppress
from shutil import which
from subprocess import run

from .utils import colored, cut, error_exit

os_info = {}
distro = ""
# 多发行版通用的安装列表
my_install_list = ["btop", "fish", "zoxide", "fzf", "ncdu", "caddy", "trojan"]


def install_mylist():
    match distro:
        case "a":
            run(("sudo", "paru", "-S", "--needed", *my_install_list), check=True)
        case "d":
            run(("sudo", "apt", "install", *my_install_list), check=True)


def install_paru():
    assert os_info["NAME"] == "Arch Linux", "Only support Arch Linux"
    assert which("git") is not None, "Git not found"
    assert which("makepkg") is not None, "Makepkg not found"

    if which("paru") is not None:
        return
    run(("mkdir", "-p", "/tmp/init_script"), check=True)
    run(
        ("git", "clone", "https://aur.archlinux.org/paru-bin.git", "--depth=1"),
        cwd="/tmp/init_script",
        check=True,
    )
    run(("makepkg", "-si"), check=True)


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
    match os_info["NAME"]:
        case "Arch Linux":
            distro = "a"
        case "Debian GNU/Linux":
            distro = "d"
        case _:
            error_exit("Unsupported OS.")


def system_check():
    if os.name != "posix" or platform.system() != "Linux":
        error_exit("This script is only for Linux.")
    if os.geteuid() != 0:
        error_exit("This script must be run as root.")
    info()
    match distro:
        case "a":
            assert which("pacman") is not None
        case "d":
            assert which("apt") is not None


def install_init():
    match distro:
        case "a":
            run(("sudo", "pacman", "-Syu", "--noconfirm"))
            run(
                ("sudo", "pacman", "-S", "--noconfirm", "archlinux-keyring"),
                check=True,
            )
            run(
                ("sudo", "pacman", "-S", "--needed", "--noconfirm", "base-devel"),
                check=True,
            )
        case "d":
            run(("sudo", "apt", "update", "-y"))
            run(("sudo", "apt", "upgrade", "-y"))


def init():
    cut()
    print("""init-script by https://github.com/lxl66566/init-script""")
    cut()

    system_check()
    install_init()


if __name__ == "__main__":
    init()
