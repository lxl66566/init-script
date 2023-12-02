import logging
from subprocess import run

from proxy import ln_caddy_cert
from utils import *

assert exists("crontab")

MAIN_PATH = "/absx"


def add_task(s: str):
    """
    尝试使用脚本添加 cron 任务失败，cronie 不支持
    """
    rc_sudo(f"""(crontab -l 2>/dev/null; echo "{s}") | crontab -""")


def add_task_daily(s: str):
    # add_task(f"0 0 * * * {s}")
    try:
        with open("/etc/cron.daily/init-script", "a") as f:
            f.write(f"{s}\n")
    except PermissionError:
        logging.error(
            "Cannot add task to /etc/cron.daily/init-script without root permission."
        )


def cron_init():
    python_exe = (
        run("which python", shell=True, capture_output=True)
        .stdout.decode("utf-8")
        .strip()
    )
    assert python_exe
    task = f"{python_exe} {os.path.realpath(__file__)}"
    add_task_daily(task)
    logging.info(f"Added daily cron task: `{task}`")


if __name__ == "__main__":
    rc(
        "git pull origin main && git reset --hard origin/main",
        cwd=os.path.join(MAIN_PATH, "lxl66566.github.io"),
    )
    ln_caddy_cert(MAIN_PATH)
