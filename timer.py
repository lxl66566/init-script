import logging
from pathlib import Path
from subprocess import run

from info import mypath

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
        with daily.open("a", encoding="utf-8") as f:
            f.write(f"{s}\n")
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
    task = f"{python_exe} {os.path.realpath(__file__)}"
    add_task_daily(task)
    assert daily.exists(), "write daily cron script failed"
    daily.chmod(0o755)
    logging.info(f"Added daily cron task: `{task}`")


if __name__ == "__main__":
    rc(
        "git fetch origin main && git reset --hard origin/main",
        cwd=os.path.join(mypath(), "lxl66566.github.io"),
    )
    ln_caddy_cert()
