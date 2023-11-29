import json
import subprocess
from contextlib import suppress
from pathlib import Path

import yaml

from utils import rc


def sync():
    rc("rsync -avz jp:/etc/caddy/Caddyfile  ./config/Caddyfile")
    rc("rsync -avz jp:/etc/hysteria/config.yaml  ./config/hysteria.yaml")
    rc("rsync -avz jp:/etc/trojan-go/config.json  ./config/trojan-go.json")
    rc("rsync -avz jp:/etc/trojan/config.json  ./config/trojan.json")


def update():
    """
    去除敏感信息
    """
    # update hysteria
    with open("config/hysteria.yaml", "r", encoding="utf-8") as f:
        hysteria_config = yaml.load(f, Loader=yaml.FullLoader)
        hysteria_config["auth"]["password"] = ""
        with open("config/hysteria.json", "w", encoding="utf-8") as f:
            json.dump(hysteria_config, f, indent=2, ensure_ascii=False)
    # remove hysteria yaml old file
    with suppress(FileNotFoundError):
        Path("config/hysteria.yaml").unlink()

    # update trojan-go
    with open("config/trojan-go.json", "r", encoding="utf-8") as f:
        trojan_go_config = json.load(f)
        trojan_go_config["password"] = []
        with open("config/trojan-go.json", "w", encoding="utf-8") as f:
            json.dump(trojan_go_config, f, indent=2, ensure_ascii=False)

    # update trojan
    with open("config/trojan.json", "r", encoding="utf-8") as f:
        trojan_config = json.load(f)
        trojan_config["password"] = []
        with open("config/trojan.json", "w", encoding="utf-8") as f:
            json.dump(trojan_config, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    sync()
    update()
