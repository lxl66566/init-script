# ruff: noqa: F403, F405
import logging
from pathlib import Path

from .install.proxy import ln_caddy_cert
from .utils import *
from .utils.service import restart_all_proxy_services

daily = Path("/etc/cron.daily/init-script")


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
    logging.info(f"Added daily cron task: `{s}`")


def init():
    assert exists("crontab")
    task = f"""#!/bin/bash
cd {(mypath() / "init-script").absolute()}
{sys.executable} -m init-script.timer
exit 0
"""
    add_task_daily(task)
    assert daily.exists(), "write daily cron script failed"


def main():
    update_blog()
    try:
        ln_caddy_cert()
        restart_all_proxy_services()
    except Exception as e:
        trace()
        error_exit(e)


if __name__ == "__main__":
    main()
