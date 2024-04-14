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
import multiprocessing
import time
from contextlib import suppress
from pathlib import Path

from .utils import *
from .utils.mycache import *
from .var import PROXY_PORT, domain, password

cert_crt_ln = Path()
cert_key_ln = Path()
wait = int(mycache.simple_load("proxy.wait")) * 10
config_path = mypath() / "init-script" / "config"


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
    assert exists("caddy"), "caddy 安装失败"
    update_blog()

    content = (config_path / "Caddyfile").read_text(encoding="utf-8")
    content = content.replace("/absx", str(mypath()))
    content = content.replace("jp.absx.online", domain())

    Path("/etc/caddy/Caddyfile").write_text(content, encoding="utf-8")
    logging.info("Caddyfile has been written.")
    rc_sudo("systemctl enable --now caddy")
    assert is_service_running("caddy"), "caddy 未正常启动！"
    logging.info(f"caddy 服务成功启动，等待 caddy 获取证书（{wait} 秒）")
    time.sleep(wait)  # 等待 caddy 获取证书
    try:
        ln_caddy_cert()
        return
    except StopIteration:
        logging.info("未找到证书，尝试重新启动 caddy...")
    rc_sudo("systemctl restart caddy")
    logging.info(f"caddy 服务成功启动，等待 caddy 获取证书（{wait} 秒）")
    time.sleep(wait)
    try:
        ln_caddy_cert()
    except StopIteration:
        error_exit("无法获取证书。")


def ln_caddy_cert():
    """
    硬链接 caddy 证书到主目录
    """
    global cert_crt_ln, cert_key_ln

    certs_dir = Path("/var/lib/caddy")
    cert_crt = next(certs_dir.rglob(domain() + ".crt"))
    cert_key = next(certs_dir.rglob(domain() + ".key"))

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


def config_hysteria():
    """
    配置 hysteria
    """

    with (config_path / "hysteria.json").open(encoding="utf-8") as f:
        config = json.load(f)

    config["listen"] = ":" + str(PROXY_PORT["hysteria"])
    config["tls"]["cert"] = str(cert_crt_ln.absolute())
    config["tls"]["key"] = str(cert_key_ln.absolute())
    config["auth"]["password"] = password()[0]

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
    config["password"] = password()
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
    Path("/etc/trojan-go").mkdir(parents=True, exist_ok=True)

    with (config_path / "trojan-go.json").open(encoding="utf-8") as f:
        config = json.load(f)

    config["local_port"] = int(PROXY_PORT["trojan-go"])
    config["password"] = password()
    config["ssl"]["cert"] = str(cert_crt_ln.absolute())
    config["ssl"]["key"] = str(cert_key_ln.absolute())
    config["ssl"]["sni"] = domain()

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


def config_openppp2():
    """
    配置 openppp
    """
    assert exists("/usr/bin/ppp"), "openppp2 未安装或安装失败"

    ppp_json = config_path / "openppp2.json"
    assert ppp_json.exists(), "openppp2.json 配置文件不存在"

    config = json.load(ppp_json.open("r", encoding="utf_8_sig"))
    config["concurrent"] = multiprocessing.cpu_count()
    config["tcp"]["listen"]["port"] = int(PROXY_PORT["openppp2"])
    config["udp"]["listen"]["port"] = int(PROXY_PORT["openppp2"])
    json.dump(config, ppp_json.open("w", encoding="utf_8_sig"), indent=2)

    service = f"""
[Unit]
Description=openppp tui server
After=network.target nss-lookup.target

[Service]
ExecStart=/usr/bin/ppp --mode=server --config={ppp_json.absolute()}
StandardOutput=null
StandardError=journal
# Restart=on-failure

[Install]
WantedBy=multi-user.target
"""
    service_ppp = Path("/usr/lib/systemd/system/openppp2.service")
    service_ppp.write_text(service, encoding="utf-8")
    service_ppp.chmod(0o644)

    rc_sudo("systemctl daemon-reload")
    rc_sudo("systemctl enable --now openppp2")
    assert is_service_running("openppp2"), "openppp2 服务启动失败"
    logging.info("openppp2 服务启动成功")


def show_all_status():
    """
    展示服务运行状态
    """

    def show_one_status(service: str):
        subprocess.run(
            f"systemctl status {service} --no-pager", shell=True, check=False
        )

    if domain():
        show_one_status("caddy")
        show_one_status("hysteria-server@hysteria")
        show_one_status("trojan-go")
        show_one_status("trojan")
    show_one_status("openppp2")
