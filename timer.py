# ruff: noqa: F403, F405
import logging
from pathlib import Path
from subprocess import run

from proxy import ln_caddy_cert
from utils import *

daily = Path("/etc/cron.daily/init-script")


def add_task(s: str):
    """
    尝试使用脚本添加 cron 任务失败，cronie 不支持
    因此此函数不使用。
    """
    rc_sudo(f"""(crontab -l 2>/dev/null; echo "{s}") | crontab -""")


def add_task_daily(s: str):
    # add_task(f"0 0 * * * {s}")
    try:
        daily.write_text(s, encoding="utf-8")
        daily.chmod(0o755)
    except PermissionError:
        logging.error(
            "Cannot add task to /etc/cron.daily/init-script without root permission."
        )
    except FileNotFoundError:
        logging.error(
            "Cannot add task to /etc/cron.daily/init-script because dir does not exist."
        )


def init():
    assert exists("crontab")
    python_exe = (
        run("which python3", shell=True, capture_output=True)
        .stdout.decode("utf-8")
        .strip()
    )
    if not python_exe:
        python_exe = (
            run("which python", shell=True, capture_output=True)
            .stdout.decode("utf-8")
            .strip()
        )
    assert python_exe, "Python path not found"
    task = f"#!/bin/bash\n{python_exe} {Path(__file__).resolve()}\nexit 0\n"
    add_task_daily(task)
    assert daily.exists(), "write daily cron script failed"
    daily.chmod(0o755)
    logging.info(f"Added daily cron task: `{task}`")


if __name__ == "__main__":
    update_blog()
    try:
        ln_caddy_cert()
    except Exception as e:
        error_exit(e)
