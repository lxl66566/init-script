#!/usr/bin/env python
#
# My linux init script.
#
# https://github.com/lxl66566/init-script

import json
import os
import sys
import platform
from contextlib import suppress
from shutil import which
from subprocess import run

from .utils import *

mypath = ""
os_info = {}
distro = ""

# 多发行版通用的安装列表
my_install_list = ["wget", "btop", "fish", "zoxide", "fzf", "ncdu", "caddy", "trojan"]


def install_mylist():
    match distro:
        case "a":
            run(("sudo", "paru", "-S", "--needed", *my_install_list), check=True)
        case "d":
            run(("sudo", "apt", "install", *my_install_list), check=True)


def install_paru():
    assert distro == "a", "Only support Arch Linux"
    assert not is_root(), "installing paru must not be root"
    assert which("git") is not None, "Git not found"
    assert which("makepkg") is not None, "Makepkg not found"

    if which("paru") is not None:
        return
    rc("mkdir -p /tmp/init_script")
    rc(
        "git clone https://aur.archlinux.org/paru-bin.git --depth=1",
        cwd="/tmp/init_script",
    )
    rc("makepkg -si")


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
        case "Ubuntu":
            distro = "u"
        case _:
            error_exit("Unsupported OS.")


def system_check():
    if os.name != "posix" or platform.system() != "Linux":
        error_exit("This script is only for Linux.")

    global mypath
    try:
        mypath = sys.argv[1].strip()
    except IndexError:
        error_exit("Usage: init-script <path>")

    info()
    match distro:
        case "a":
            assert which("pacman") is not None
        case "d" | "u":
            assert which("apt") is not None


def install_init():
    match distro:
        case "a":
            rc("sudo pacman -Syu --noconfirm")
            rc("sudo pacman -S --noconfirm archlinux-keyring")
            rc("sudo pacman -S --needed --noconfirm base-devel")
        case "d":
            rc("sudo apt update -y")
            rc("sudo apt upgrade -y")


def init():
    cut()
    print("""init-script by https://github.com/lxl66566/init-script""")
    cut()

    system_check()
    install_init()


if __name__ == "__main__":
    init()
