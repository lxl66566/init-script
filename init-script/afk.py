# this script was only tested on podman.
# ruff: noqa: F403, F405
import logging as log

from .utils import error_exit, exists, rc, rc_sudo

prefix = ""
TOKENS = {
    "packetstream": "5wA2",
    "traffmonetizer": "N5SmpurHI0TArINp8KiHb6VVpV8iaeqkwhhy3sxP0l4=",
    "earnfm": "52d56223-15b5-4162-9608-a79c2dc87230",
}


def check_container():
    global prefix
    if exists("podman"):
        prefix = "podman"
    elif exists("docker"):
        prefix = "docker"
    else:
        error_exit("Please install a container manager, like podman or docker")


def init():
    check_container()
    log.warning(
        "the AFk script is to earn money FOR ME. If you want to use this, make sure you have replaced this script with your ids."
    )
    # https://packetstream.io/
    rc_sudo(
        f"{prefix} run -d --restart=always -e CID={TOKENS['packetstream']} --name psclient docker.io/packetstream/psclient:latest"
    )
    # https://app.traffmonetizer.com
    rc_sudo(
        f"{prefix} run -d --name tm docker.io/traffmonetizer/cli_v2 start accept --token {TOKENS['traffmonetizer']}"
    )
    # https://app.earn.fm
    rc_sudo(
        f"""{prefix} run -d --restart=always -e EARNFM_TOKEN="{TOKENS['earnfm']}" --name earnfm-client docker.io/earnfm/earnfm-client:latest"""
    )


def remove():
    check_container()
    result = (
        rc(
            f"{prefix} ps -q",
            capture_output=True,
        )
        .stdout.decode()
        .split()
    )
    for name in result:
        rc(f"{prefix} kill {name}")
        rc(f"{prefix} rm {name}")
