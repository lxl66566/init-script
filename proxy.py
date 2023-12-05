#!/usr/bin/env python
#
# My linux proxy script.
#
# https://github.com/lxl66566/init-script
#
# PLEASE RUN AS ROOT, YOU ARE AWARE OF THE RISKS INVOLVED AND CONTINUE.

import json
import logging
import os
import subprocess
import time
from contextlib import suppress
from pathlib import Path

from utils import *

MAIN_PATH = "/absx"
distro = ""
version = 6.0
PROXY_PORT = {"hysteria": "30000", "trojan-go": 40000, "trojan": "50000"}

domain = ""
password = []
cert_abspath = ""
key_abspath = ""


def get_info(main_path, distro_, version_):
    global MAIN_PATH, distro, version
    MAIN_PATH = main_path
    assert Path(MAIN_PATH).exists(), "main path does not exist"
    distro = distro_
    version = float(version_)


def init(*args):
    assert exists("caddy"), "caddy is not installed"
    assert exists("hysteria"), "hysteria is not installed"
    assert exists("trojan"), "trojan is not installed"
    assert exists("trojan-go"), "trojan-go is not installed"
    assert exists("systemctl"), "systemctl is not configured"
    get_info(*args)
    ask()
    config_caddy()
    config_hysteria()
    config_trojan()
    config_trojan_go()


def ask(**kwargs):
    global domain, password, MAIN_PATH
    while temp := input(
        f"是否使用目录 {MAIN_PATH} 作为证书存放位置，y 使用，或输入自定义根目录："
    ):
        if temp.lower() != "y":
            MAIN_PATH = temp.strip()
            if not Path(MAIN_PATH).exists():
                print("输入的根目录不存在，请重新输入")
            else:
                break
        else:
            break

    domain = kwargs.get("domain") or input("domain: ").strip()

    def ask_password():
        password = []
        while pswd := input("password（每行一个，空行结束）: ").strip():
            if pswd:
                password.append(pswd)
            else:
                break
        return password

    password = kwargs.get("password") or ask_password()


def check_cert():
    """
    检查证书是否存在
    """
    assert Path(cert_abspath).exists(), f"{cert_abspath} 位置未找到证书"
    assert Path(key_abspath).exists(), f"{key_abspath} 位置未找到密钥"


def config_caddy():
    """
    配置 caddy 及其证书
    """
    (Path(MAIN_PATH) / "lxl66566.github.io").exists() or rc(
        "git clone https://github.com/lxl66566/lxl66566.github.io.git -b main --depth 1",
        cwd=MAIN_PATH,
    )

    content = Path("./config/Caddyfile").read_text(encoding="utf-8")
    content = content.replace("/absx", MAIN_PATH)
    content = content.replace("jp.absx.online", domain)

    Path("/etc/caddy/Caddyfile").write_text(content, encoding="utf-8")
    logging.info("Caddyfile has been written.")
    rc_sudo("systemctl enable --now caddy")
    assert is_service_running("caddy"), "caddy 未正常启动！"
    logging.info("caddy 服务成功启动")
    time.sleep(8)  # 等待 caddy 获取证书

    ln_caddy_cert(MAIN_PATH)


def ln_caddy_cert(MAIN_PATH: str):
    # ln cert
    certs_dir = "/var/lib/caddy"
    cert_files = []
    for subdir, dirs, files in os.walk(certs_dir):
        for file in files:
            if file == f"{domain}.crt" or file == f"{domain}.key":
                cert_files.append(os.path.join(subdir, file))
    assert len(cert_files) == 2, "找到了 {} 个证书文件，应该只有 2 个：\n{}".format(
        len(cert_files),
        "\n".join(cert_files),
    )
    for file in cert_files:
        filename = file.rstrip("/").split("/")[-1]
        global cert_abspath, key_abspath
        if filename.endswith(".crt"):
            cert_abspath = os.path.join(MAIN_PATH, filename)
        elif filename.endswith(".key"):
            key_abspath = os.path.join(MAIN_PATH, filename)

    logging.info("证书文件路径：\n{}".format("\n".join((cert_abspath, key_abspath))))
    # 这里如果用软连接会出现权限问题，硬链接则需要想办法定期更新。
    rc_sudo(" ".join(("ln -f", file, MAIN_PATH)))
    rc_sudo(" ".join(("chmod 777", cert_abspath)))
    rc_sudo(" ".join(("chmod 777", key_abspath)))

    check_cert()
    logging.info("证书配置完成")


def config_hysteria():
    """
    配置 hysteria
    """

    with open("./config/hysteria.json", "r") as f:
        config = json.load(f)

    config["listen"] = ":" + str(PROXY_PORT["hysteria"])
    config["tls"]["cert"] = cert_abspath
    config["tls"]["key"] = key_abspath
    config["auth"]["password"] = password[0]

    with open("/etc/hysteria/hysteria.json", "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    logging.info("hysteria 配置完成")

    assert os.geteuid() == 0, "This function must be run as root."
    for p in (
        "/etc/systemd/system/hysteria-server@.service",
        "/usr/lib/systemd/system/hysteria-server@.service",
    ):
        with suppress(FileNotFoundError):
            s = Path(p).read_text(encoding="utf-8")
            s = s.replace(r"/etc/hysteria/%i.yaml", r"/etc/hysteria/%i.json")
            Path(p).write_text(s, encoding="utf-8")

    logging.info("修改服务成功")
    rc_sudo("systemctl daemon-reload")
    rc_sudo("systemctl enable --now hysteria-server@hysteria")
    assert is_service_running("hysteria-server@hysteria"), "hysteria 服务启动失败"
    logging.info("hysteria 服务启动成功")


def config_trojan():
    """
    配置 trojan
    """
    with open("./config/trojan.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    config["local_port"] = int(PROXY_PORT["trojan"])  # trojan-go 需要数字值
    config["password"] = password
    config["ssl"]["cert"] = cert_abspath
    config["ssl"]["key"] = key_abspath

    with open("/etc/trojan/config.json", "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    logging.info("trojan 配置完成")
    rc_sudo("systemctl enable --now trojan")
    assert is_service_running("trojan"), "trojan 服务启动失败"
    logging.info("trojan 服务启动成功")


def config_trojan_go():
    """
    配置 trojan-go
    """
    with open("./config/trojan-go.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    config["local_port"] = str(PROXY_PORT["trojan-go"])
    config["password"] = password
    config["ssl"]["cert"] = cert_abspath
    config["ssl"]["key"] = key_abspath
    config["ssl"]["sni"] = domain

    with open("/etc/trojan-go/config.json", "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    logging.info("trojan-go 配置完成")
    rc_sudo("systemctl enable --now trojan-go")
    assert is_service_running("trojan-go"), "trojan-go 服务启动失败"
    logging.info("trojan-go 服务启动成功")


if __name__ == "__main__":
    init("/absx", "a", "6")  # arg for test
