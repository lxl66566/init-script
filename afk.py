# this script was only tested on podman.
from utils import *


def init():
    if exists("podman"):
        prefix = "podman"
    elif exists("docker"):
        prefix = "docker"
    else:
        error_exit("Please install a container manager, like podman or docker")
    logging.warning(
        "the AFk script is to earn money FOR ME. If you want to use this, make sure you have replaced this script with your ids."
    )
    # https://packetstream.io/
    rc_sudo(
        prefix
        + " run -d --restart=always -e CID=5wA2 --name psclient docker.io/packetstream/psclient:latest"
    )
    # https://app.traffmonetizer.com
    rc_sudo(
        prefix
        + " run -d --name tm docker.io/traffmonetizer/cli_v2 start accept --token N5SmpurHI0TArINp8KiHb6VVpV8iaeqkwhhy3sxP0l4="
    )
    # https://app.earn.fm
    rc_sudo(
        prefix
        + """ run -d --restart=always -e EARNFM_TOKEN="52d56223-15b5-4162-9608-a79c2dc87230" --name earnfm-client docker.io/earnfm/earnfm-client:latest"""
    )
