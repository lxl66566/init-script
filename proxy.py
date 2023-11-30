#!/usr/bin/env python
#
# My linux proxy script.
#
# https://github.com/lxl66566/init-script
#
# PLEASE RUN AS ROOT, YOU ARE AWARE OF THE RISKS INVOLVED AND CONTINUE.

import json
import os
import subprocess
from contextlib import suppress
from pathlib import Path
from shutil import which
from subprocess import run

from utils import *
from init import mypath

MAIN_PATH = mypath
PROXY_PORT = {"hysteria": 30000, "trojan-go": 40000, "trojan": 50000}

domain = ""
password = []
cert_abspath = ""
key_abspath = ""

assert Path(MAIN_PATH).exists(), "main path does not exist"
assert which("caddy") is not None, "caddy is not installed"
assert which("hysteria") is not None, "hysteria is not installed"
assert which("trojan") is not None, "trojan is not installed"
assert which("trojan-go") is not None, "trojan-go is not installed"
assert which("systemctl") is not None, "systemctl is not configured"


def ask():
    global domain, password
    temp = input(
        f"是否使用目录 {MAIN_PATH} 作为证书存放位置，y 使用，或输入自定义根目录："
    )
    if temp.lower() != "y":
        MAIN_PATH = temp.strip()
        assert Path(MAIN_PATH).exists(), "存放位置不存在"
    domain = input("domain: ").strip()
    while pswd := input("password（每行一个，空行结束）:").strip():
        if pswd:
            password.append(pswd)
        else:
            break


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
    rc(
        "git clone git@github.com:lxl66566/lxl66566.github.io.git -b main --depth 1",
        cwd=MAIN_PATH,
    )

    content = Path("./config/Caddyfile").read_text(encoding="utf-8")
    content = content.replace(
        "STATIC_PATH", os.path.join(MAIN_PATH, "lxl66566.github.io")
    )

    Path.open("/etc/caddy/Caddyfile").write_text(content, encoding="utf-8")
    rc("sudo systemctl enable --now caddy")
    assert is_service_running("caddy"), "caddy 未正常启动！"

    # ln cert
    certs_dir = "/var/lib/caddy/certificates"
    cert_files = []
    for subdir, dirs, files in os.walk(certs_dir):
        for file in files:
            if file.endswith(".crt") or file.endswith(".key"):
                cert_files.append(os.path.join(subdir, file))
    assert len(cert_files) == 2, "找到了 {0} 个证书文件，应该只有 2 个".format(
        len(cert_files)
    )
    for file in cert_files:
        filename = file.split("/")[-1]
        global cert_abspath, key_abspath
        if filename.endswith(".crt"):
            cert_abspath = os.path.join(MAIN_PATH, filename)
        elif filename.endswith(".key"):
            key_abspath = os.path.join(MAIN_PATH, filename)
        run("sudo", "ln", "-sf", file, MAIN_PATH, check=True)

    check_cert()


def config_hysteria():
    """
    配置 hysteria
    """

    with open("./config/hysteria.json", "r") as f:
        config = json.load(f)

    config["listen"] = ":" + PROXY_PORT["hysteria"]
    config["tls"]["cert"] = cert_abspath
    config["tls"]["key"] = key_abspath
    config["auth"]["password"] = password[0]

    with open("/etc/hysteria/hysteria.json", "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    assert os.geteuid() == 0, "This function must be run as root."
    for p in (
        "/etc/systemd/system/hysteria-server.service",
        "/usr/lib/systemd/system/hysteria-server.service",
    ):
        with suppress(FileNotFoundError):
            s = Path(p).read_text(encoding="utf-8")
            s = s.replace(r"/etc/hysteria/%i.yaml", r"/etc/hysteria/%i.json")
            Path(p).write_text(s, encoding="utf-8")

    run("sudo systemctl daemon-reload", shell=True)
    rc("sudo systemctl enable --now hysteria-server@hysteria")
    assert is_service_running("hysteria-server@hysteria"), "hysteria 服务启动失败"


def config_trojan():
    """
    配置 trojan
    """
    with open("./config/trojan.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    config["local_port"] = PROXY_PORT["trojan"]
    config["password"] = password
    config["ssl"]["cert"] = cert_abspath
    config["ssl"]["key"] = key_abspath

    with open("/etc/trojan/config.json", "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False, encoding="utf-8")

    run("sudo systemctl enable --now trojan", shell=True, check=True)
    assert is_service_running("trojan"), "trojan 服务启动失败"


def config_trojan_go():
    """
    配置 trojan-go
    """
    with open("./config/trojan-go.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    config["local_port"] = PROXY_PORT["trojan"]
    config["password"] = password
    config["ssl"]["cert"] = cert_abspath
    config["ssl"]["key"] = key_abspath
    config["ssl"]["sni"] = domain

    with open("/etc/trojan-go/config.json", "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False, encoding="utf-8")

    rc("sudo systemctl enable --now trojan-go")
    assert is_service_running("trojan-go"), "trojan-go 服务启动失败"


if __name__ == "__main__":
    ask()
    config_caddy()
    config_hysteria()
    config_trojan()
    config_trojan_go()
