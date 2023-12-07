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

import install
import proxy
from utils import *

logging.basicConfig(level=logging.INFO)

mypath = "/absx"
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
                os_info[key.strip()] = value.strip().strip('"')

    global distro, version, os_info
    files = ("/etc/os-release", "/etc/redhat-release", "/etc/lsb-release")
    for file in files:
        with suppress(FileNotFoundError):
            with open(file, "r") as f:
                read_os_info(f)
    assert os_info, "Could not detect OS info."
    if os_info.get("NAME").startswith("Arch"):
        distro = "a"
        version = 0
    elif os_info.get("NAME").startswith("Debian"):
        distro = "d"
        version = os_info.get("VERSION_ID")
    elif os_info.get("NAME").startswith("Ubuntu"):
        distro = "u"
        version = os_info.get("VERSION_ID")
    else:
        logging.error(
            f"""found NAME: {os_info.get("NAME")}, version: {os_info.get("VERSION_ID")}"""
        )
        error_exit("Unsupported OS.")
    logging.info(f"OS detected success. distro: {distro}, version: {version}")


def system_check():
    if os.name != "posix" or platform.system() != "Linux":
        error_exit("This script is only for Linux.")

    global mypath
    try:
        mypath = sys.argv[1].strip()
    except IndexError:
        error_exit("Usage: init-script <path>")
    logging.info(f"Path detected success. path: {mypath}")


def init():
    cut()
    print("""init-script by https://github.com/lxl66566/init-script""")
    cut()

    system_check()
    info()
    rc_sudo(f"chmod 777 {mypath} -R")
    logging.info("init success. next: install")


if __name__ == "__main__":
    init()
    install.init(mypath, distro, version)
    proxy.init(mypath, distro, version)
    timer.init(mypath)
