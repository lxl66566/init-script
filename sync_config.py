import json
import subprocess
from contextlib import suppress
from pathlib import Path

from utils import rc

vps_name = "jp"


def sync():
    assert vps_name, "vps_name is empty"
    rc(f"rsync -avz {vps_name}:/etc/caddy/Caddyfile  ./config/Caddyfile")
    # previously use hysteria.yaml, now use json
    rc(f"rsync -avz {vps_name}:/etc/hysteria/hysteria.json  ./config/hysteria.json")
    rc(f"rsync -avz {vps_name}:/etc/trojan-go/config.json  ./config/trojan-go.json")
    rc(f"rsync -avz {vps_name}:/etc/trojan/config.json  ./config/trojan.json")


def update():
    """
    去除敏感信息
    """
    # update hysteria
    with open("config/hysteria.json", "r", encoding="utf-8") as f:
        hysteria_config = json.load(f)
        hysteria_config["auth"]["password"] = ""
        with open("config/hysteria.json", "w", encoding="utf-8") as f:
            json.dump(hysteria_config, f, indent=2, ensure_ascii=False)

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
    vps_name = "jp"
    sync()
    update()
