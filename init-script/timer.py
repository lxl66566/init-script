# ruff: noqa: F403, F405
import logging

from .install.proxy import ln_caddy_cert
from .utils import *
from .utils.constant import SYSTEMD_SERVICE_DIR
from .utils.service import restart_all_proxy_services

service_name = SYSTEMD_SERVICE_DIR / "init-script.service"
timer_name = SYSTEMD_SERVICE_DIR / "init-script.timer"


def add_task(command: str):
    try:
        content = f"""
[Unit]
Description=init-script timer

[Service]
ExecStart={command}
"""
        service_name.write_text(content, encoding="utf-8")
        service_name.chmod(0o755)
        content = f"""
[Unit]
Description=Runs mytimer every day

[Timer]
OnCalendar=daily
Unit={service_name.name}

[Install]
WantedBy=multi-user.target
"""
        timer_name.write_text(content, encoding="utf-8")
        timer_name.chmod(0o755)
    except PermissionError:
        logging.error(
            "Cannot add task to /etc/cron.daily/init-script without root permission."
        )


def init():
    assert exists("crontab")
    task = f"""cd {(mypath() / "init-script").absolute()} && {sys.executable} -m init-script.timer"""
    add_task(task)
    assert service_name.exists(), "write systemd timer service failed"
    assert timer_name.exists(), "write systemd timer failed"
    rc_sudo(f"systemctl enable {timer_name.name}")
    logging.info(f"Added daily task: `{task}`")


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
