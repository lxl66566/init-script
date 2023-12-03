#!/usr/bin/env python
#
# My linux init script.
#
# https://github.com/lxl66566/init-script

import json
import logging
import os
import platform
import sys
from contextlib import suppress
from subprocess import run

from utils import *

logging.basicConfig(level=logging.INFO)

mypath = ""
os_info = {}
distro = ""
version = ""


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

    global distro, version, os_info
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
            version = os_info["VERSION_ID"]
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
            assert exists("pacman")
        case "d" | "u":
            assert exists("apt")


def init():
    cut()
    print("""init-script by https://github.com/lxl66566/init-script""")
    cut()

    system_check()
    install_init()


if __name__ == "__main__":
    init()
