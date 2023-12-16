#!/usr/bin/env python
#
# My linux proxy script.
#
# https://github.com/lxl66566/init-script
#
# PLEASE RUN AS ROOT, YOU ARE AWARE OF THE RISKS INVOLVED AND CONTINUE.

# ruff: noqa: F403, F405

import json
import logging
import time
from contextlib import suppress
from pathlib import Path

from mycache import *
from utils import *

PROXY_PORT = {"hysteria": "30000", "trojan-go": 40000, "trojan": 50000}

domain = ""
password = []
cert_crt_ln = Path()
cert_key_ln = Path()
wait = 10
config_path = mypath() / "init-script" / "config"


def init():
    assert exists("caddy"), "caddy is not installed"
    assert exists("hysteria"), "hysteria is not installed"
    assert exists("trojan"), "trojan is not installed"
    assert exists("trojan-go"), "trojan-go is not installed"
    assert exists("systemctl"), "systemctl is not configured"
    cache()
    if not domain or not password:
        ask()
    config_caddy()
    config_hysteria()
    config_trojan()
    config_trojan_go()


def cache():
    """
    从 cache 中读取 domain, password
    """
    global domain, password, wait

    if mycache.simple_load("proxy.wait"):
        wait = 1

    cache = mycache("proxy").load()
    if isinstance(cache, dict) and len(cache) == 2:
        domain, password = (cache.get(k) for k in ("domain", "password"))
        logging.info("successfully read domain and password from cache.")
    else:
        logging.info("cache is empty or corrupted.")


def ask():
    """
    domain: str, password: list[str]
    """

    domain = input("domain: ").strip()

    def ask_password():
        password = []
        while pswd := input("password（每行一个，空行结束）: ").strip():
            if pswd:
                password.append(pswd)
            else:
                break
        return password

    password = ask_password()

    assert domain and password, "domain and password is empty"

    mycache("proxy").save({"domain": domain, "password": password})


def check_cert():
    """
    检查证书是否存在
    """
    assert cert_crt_ln.exists(), f"{str(cert_crt_ln.absolute())} 位置未找到证书"
    assert cert_key_ln.exists(), f"{str(cert_key_ln.absolute())} 位置未找到密钥"


def config_caddy():
    """
    配置 caddy 及其证书
    """
    (mypath() / "lxl66566.github.io").exists() or rc(
        "git clone https://github.com/lxl66566/lxl66566.github.io.git -b main --depth 1",
        cwd=mypath(),
    )

    content = (config_path / "Caddyfile").read_text(encoding="utf-8")
    content = content.replace("/absx", str(mypath()))
    content = content.replace("jp.absx.online", domain)

    Path("/etc/caddy/Caddyfile").write_text(content, encoding="utf-8")
    logging.info("Caddyfile has been written.")
    rc_sudo("systemctl enable --now caddy")
    assert is_service_running("caddy"), "caddy 未正常启动！"
    logging.info(f"caddy 服务成功启动，等待 caddy 获取证书（{wait} 秒）")
    time.sleep(wait)  # 等待 caddy 获取证书
    if ln_caddy_cert():
        return
    logging.info("未找到证书，尝试重新启动 caddy...")
    rc_sudo("systemctl restart caddy")
    logging.info(f"caddy 服务成功启动，等待 caddy 获取证书（{wait} 秒）")
    time.sleep(wait)
    ln_caddy_cert() or error_exit("无法获取证书。")


def ln_caddy_cert() -> bool:
    """
    硬链接 caddy 证书到主目录
    """
    global cert_crt_ln, cert_key_ln

    certs_dir = Path("/var/lib/caddy")
    try:
        cert_crt = next(certs_dir.rglob(domain + ".crt"))
        cert_key = next(certs_dir.rglob(domain + ".key"))
    except StopIteration:
        return False

    assert cert_crt.exists() and cert_key.exists(), "未找到证书，尝试重新生成"
    cert_crt_ln = mypath() / cert_crt.name
    cert_key_ln = mypath() / cert_key.name
    cert_crt_ln.unlink(True)
    cert_key_ln.unlink(True)

    # 这里如果用软连接会出现权限问题，硬链接则需要想办法定期更新。
    cert_crt_ln.hardlink_to(cert_crt)
    cert_key_ln.hardlink_to(cert_key)
    logging.info(
        "证书文件路径：  {}  {}".format(
            str(cert_crt_ln.absolute()), str(cert_key_ln.absolute())
        )
    )
    cert_crt_ln.chmod(0o777)
    cert_key_ln.chmod(0o777)
    check_cert()
    mycache.simple_save("proxy.wait")
    logging.info("证书配置完成")
    return True


def config_hysteria():
    """
    配置 hysteria
    """

    with (config_path / "hysteria.json").open(encoding="utf-8") as f:
        config = json.load(f)

    config["listen"] = ":" + str(PROXY_PORT["hysteria"])
    config["tls"]["cert"] = str(cert_crt_ln.absolute())
    config["tls"]["key"] = str(cert_key_ln.absolute())
    config["auth"]["password"] = password[0]

    with open("/etc/hysteria/hysteria.json", "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    logging.info("hysteria 配置完成")

    assert is_root(), "This function must be run as root."
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
    with (config_path / "trojan.json").open(encoding="utf-8") as f:
        config = json.load(f)

    config["local_port"] = int(PROXY_PORT["trojan"])  # trojan-go 需要数字值
    config["password"] = password
    config["ssl"]["cert"] = str(cert_crt_ln.absolute())
    config["ssl"]["key"] = str(cert_key_ln.absolute())

    with open("/etc/trojan/config.json", "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    logging.info("trojan 配置完成")

    rc_sudo(
        "sed -i '/User=nobody/ s/User=nobody/DynamicUser=yes/' /usr/lib/systemd/system/trojan.service"
    )
    rc_sudo("systemctl daemon-reload")
    rc_sudo("systemctl enable --now trojan")
    assert is_service_running("trojan"), "trojan 服务启动失败"
    logging.info("trojan 服务启动成功")


def config_trojan_go():
    """
    配置 trojan-go
    """
    with (config_path / "trojan-go.json").open(encoding="utf-8") as f:
        config = json.load(f)

    config["local_port"] = int(PROXY_PORT["trojan-go"])
    config["password"] = password
    config["ssl"]["cert"] = str(cert_crt_ln.absolute())
    config["ssl"]["key"] = str(cert_key_ln.absolute())
    config["ssl"]["sni"] = domain

    with open("/etc/trojan-go/config.json", "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    logging.info("trojan-go 配置完成")

    rc_sudo(
        "sed -i '/User=nobody/ s/User=nobody/DynamicUser=yes/' /usr/lib/systemd/system/trojan-go.service"
    )
    rc_sudo("systemctl daemon-reload")
    rc_sudo("systemctl enable --now trojan-go")
    assert is_service_running("trojan-go"), "trojan-go 服务启动失败"
    logging.info("trojan-go 服务启动成功")


def show_all_status():
    """
    展示服务运行状态
    """

    def show_one_status(service: str):
        rc(f"systemctl status {service} --no-pager")

    show_one_status("caddy")
    show_one_status("hysteria-server@hysteria")
    show_one_status("trojan-go")
    show_one_status("trojan")
