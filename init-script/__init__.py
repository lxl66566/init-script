#!/usr/bin/env python
#
# My linux init script.
#
# https://github.com/lxl66566/init-script

# ruff: noqa: F403, F405

import logging
import os
import platform

from .utils import colored, cut, distro, error_exit, pm


def debug_mode():
    return os.getenv("debug") is not None or os.getenv("DEBUG") is not None or False


cut()
print("""init-script by https://github.com/lxl66566/init-script""")
if os.name != "posix" or platform.system() != "Linux":
    error_exit("This script is only for Linux.")
logging.basicConfig(level=logging.DEBUG if debug_mode() else logging.INFO)
cut()
print(
    f"""运行环境：distro: {colored(distro(), 'green')}, pm: {colored(pm(), 'green')}, debug mode: {colored(str(True if debug_mode() else False), 'green')}"""
)
