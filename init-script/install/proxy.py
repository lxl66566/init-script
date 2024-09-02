#!/usr/bin/env python3
#
# My linux proxy script.
#
# https://github.com/lxl66566/init-script
#
# PLEASE RUN AS ROOT, YOU ARE AWARE OF THE RISKS INVOLVED AND CONTINUE.

# ruff: noqa: F403, F405

import json
import logging as log
import multiprocessing
import shutil
import time
from contextlib import suppress
from pathlib import Path

from ..utils import *
from ..utils.constant import SYSTEMD_SERVICE_DIR
from ..utils.mycache import BaseCache, SimpleCache
from ..utils.service import (
    is_service_running,
    reload_or_start_service,
)
from ..var import GET_CERT_DEFAULT_WAIT, GET_CERT_MAX_RETRY, PROXY_PORT, DomainPassword

WAITNAME = "proxy.wait"

cert_crt_ln = BaseCache("cert").load()
cert_key_ln = BaseCache("key").load()
wait = int(not SimpleCache.load(WAITNAME)) * GET_CERT_DEFAULT_WAIT
config_path = mypath() / "init-script" / "config"


def check_cert():
    """
    检查证书是否存在
    """
    assert cert_crt_ln is not None and cert_key_ln is not None, "无法读取链接位置！"
    assert cert_crt_ln.exists(), f"{str(cert_crt_ln.absolute())} 位置未找到证书"
    assert cert_key_ln.exists(), f"{str(cert_key_ln.absolute())} 位置未找到密钥"
    assert (
        cert_crt_ln.is_file()
    ), f"{str(cert_crt_ln.absolute())} 位置未找到证书或不合法"
    assert (
        cert_key_ln.is_file()
    ), f"{str(cert_key_ln.absolute())} 位置未找到密钥或不合法"


def config_caddy():
    """
    配置 caddy 及其证书
    """
    if not exists("caddy"):
        log.warn("caddy 未安装，跳过配置...")
        return
    assert DomainPassword().domain(), "域名未设置，拒绝配置 caddy"
    update_blog()

    content = (
        (config_path / "Caddyfile")
        .read_text(encoding="utf-8")
        .format(path=str(mypath()).rstrip(os.sep), domain=DomainPassword().domain())
    )

    caddy_file_path = Path("/etc/caddy/Caddyfile")
    caddy_file_path.parent.mkdir(parents=True, exist_ok=True)
    caddy_file_path.write_text(content, encoding="utf-8")
    log.info("Caddyfile has been written.")

    reload_or_start_service("caddy")
    assert is_service_running("caddy"), "caddy 未正常启动！"
    for _ in range(GET_CERT_MAX_RETRY):  # 重试次数
        log.info(f"caddy 服务成功启动，等待 caddy 获取证书（{wait} 秒）")
        time.sleep(wait)  # 等待 caddy 获取证书
        try:
            ln_caddy_cert()
            return
        except StopIteration:
            log.info("未找到证书，尝试重新启动 caddy...")
            reload_or_start_service("caddy")
    error_exit(
        "无法获取证书。"
        + "这可能是由于 archlinux 更新内核后需要重启导致的，您可能需要手动 reboot。"
        if pm() == "p"
        else "" + "您可以执行 `journalctl -xeu caddy` 获取更多信息。"
    )


def ln_caddy_cert():
    """
    硬链接 caddy 证书到主目录
    """
    global cert_crt_ln, cert_key_ln

    certs_dir = Path("/var/lib/caddy")
    domain = DomainPassword().domain()
    assert domain, "域名未设置，拒绝配置 caddy"
    cert_crt = next(certs_dir.rglob(domain + ".crt"))
    cert_key = next(certs_dir.rglob(domain + ".key"))

    # if not found, raise StopIteration

    assert cert_crt.exists() and cert_key.exists(), "未找到证书，尝试重新生成"
    cert_crt_ln = mypath() / cert_crt.name
    cert_key_ln = mypath() / cert_key.name
    cert_crt_ln.unlink(True)
    cert_key_ln.unlink(True)

    # 这里如果用软连接会出现权限问题，硬链接则需要想办法定期更新。
    cert_crt_ln.hardlink_to(cert_crt)
    cert_key_ln.hardlink_to(cert_key)
    log.info(
        "证书文件路径：  {}  {}".format(
            str(cert_crt_ln.absolute()), str(cert_key_ln.absolute())
        )
    )
    cert_crt_ln.chmod(0o777)
    cert_key_ln.chmod(0o777)
    BaseCache("cert").save(cert_crt_ln)
    BaseCache("key").save(cert_key_ln)
    check_cert()
    SimpleCache.save(WAITNAME)
    log.info("证书配置完成")


def config_hysteria():
    """
    配置 hysteria
    """

    if not exists("hysteria"):
        log.warn("hysteria 未安装，跳过配置...")
        return

    assert cert_crt_ln and cert_key_ln, "未找到链接的证书。"

    with (config_path / "hysteria.json").open(encoding="utf-8") as f:
        config = json.load(f)

    config["listen"] = ":" + str(PROXY_PORT["hysteria"])
    config["tls"]["cert"] = str(cert_crt_ln.absolute())
    config["tls"]["key"] = str(cert_key_ln.absolute())
    pswd = DomainPassword().password()
    assert pswd, "密码未设置，拒绝配置 hysteria"
    config["auth"]["password"] = pswd[0]

    with open("/etc/hysteria/hysteria.json", "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    log.info("hysteria 配置完成")

    assert is_root(), "This function must be run as root."
    for p in (
        "/etc/systemd/system/hysteria-server@.service",
        "/usr/lib/systemd/system/hysteria-server@.service",
    ):
        with suppress(FileNotFoundError):
            s = Path(p).read_text(encoding="utf-8")
            s = s.replace(r"/etc/hysteria/%i.yaml", r"/etc/hysteria/%i.json")
            Path(p).write_text(s, encoding="utf-8")

    log.info("修改服务成功")
    rc_sudo("systemctl daemon-reload")
    reload_or_start_service("hysteria-server@hysteria")
    assert is_service_running("hysteria-server@hysteria"), "hysteria 服务启动失败"
    log.info("hysteria 服务启动成功")


def config_trojan():
    """
    配置 trojan
    """

    if not exists("trojan"):
        log.warn("trojan 未安装，跳过配置...")
        return

    assert cert_crt_ln and cert_key_ln, "未找到链接的证书。"

    with (config_path / "trojan.json").open(encoding="utf-8") as f:
        config = json.load(f)

    config["local_port"] = int(PROXY_PORT["trojan"])  # trojan-go 需要数字值
    config["password"] = DomainPassword().password()
    config["ssl"]["cert"] = str(cert_crt_ln.absolute())
    config["ssl"]["key"] = str(cert_key_ln.absolute())

    with open("/etc/trojan/config.json", "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    log.info("trojan 配置完成")

    rc_sudo(
        "sed -i '/User=nobody/ s/User=nobody/DynamicUser=yes/' /usr/lib/systemd/system/trojan.service"
    )
    rc_sudo("systemctl daemon-reload")
    reload_or_start_service("trojan")
    assert is_service_running("trojan"), "trojan 服务启动失败"
    log.info("trojan 服务启动成功")


def config_trojan_go():
    """
    配置 trojan-go
    """

    if not exists("trojan-go"):
        log.warn("trojan-go 未安装，跳过配置...")
        return

    assert cert_crt_ln and cert_key_ln, "未找到链接的证书。"

    Path("/etc/trojan-go").mkdir(parents=True, exist_ok=True)
    geo_dir = Path("/usr/share/trojan-go/")
    geo_dir.mkdir(parents=True, exist_ok=True)

    with (config_path / "trojan-go.json").open(encoding="utf-8") as f:
        config = json.load(f)

    config["local_port"] = int(PROXY_PORT["trojan-go"])
    config["password"] = DomainPassword().password()
    config["ssl"]["cert"] = str(cert_crt_ln.absolute())
    config["ssl"]["key"] = str(cert_key_ln.absolute())
    config["ssl"]["sni"] = DomainPassword().domain()

    with open("/etc/trojan-go/config.json", "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    if not (geo_dir / "geoip.dat").exists():
        rc(
            "wget https://github.com/Loyalsoldier/v2ray-rules-dat/releases/download/202409012211/geoip.dat",
            cwd=geo_dir,
        )
    if not (geo_dir / "geosite.dat").exists():
        rc(
            "wget https://github.com/Loyalsoldier/v2ray-rules-dat/releases/download/202409012211/geosite.dat",
            cwd=geo_dir,
        )
    log.info("trojan-go 配置完成")

    rc_sudo(
        "sed -i '/User=nobody/ s/User=nobody/DynamicUser=yes/' /usr/lib/systemd/system/trojan-go.service"
    )
    rc_sudo("systemctl daemon-reload")
    reload_or_start_service("trojan-go")
    assert is_service_running("trojan-go"), "trojan-go 服务启动失败"
    log.info("trojan-go 服务启动成功")


def config_openppp2():
    """
    配置 openppp
    """

    if not exists("ppp"):
        log.warn("openppp2 未安装，跳过配置...")
        return

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
ExecStart={shutil.which("ppp")} --mode=server --config={ppp_json.absolute()}
StandardOutput=null
StandardError=journal
# Restart=on-failure

[Install]
WantedBy=multi-user.target
"""
    service_ppp = SYSTEMD_SERVICE_DIR / "openppp2.service"
    service_ppp.write_text(service, encoding="utf-8")
    service_ppp.chmod(0o644)
    log.debug("openppp2 服务配置完成，正在启动...")
    rc_sudo("systemctl daemon-reload")
    reload_or_start_service("openppp2")
    assert is_service_running("openppp2"), "openppp2 服务启动失败"
    log.info("openppp2 服务启动成功")


def show_all_status():
    """
    展示服务运行状态
    """

    def show_one_status(service: str):
        subprocess.run(
            f"systemctl status {service} --no-pager", shell=True, check=False
        )

    if DomainPassword().domain():
        show_one_status("caddy")
        show_one_status("hysteria-server@hysteria")
        show_one_status("trojan-go")
        show_one_status("trojan")
    show_one_status("openppp2")


def reconfig_all_proxies():
    """
    重新配置所有代理，并重启所有代理服务
    """
    SimpleCache.remove(WAITNAME)
    if DomainPassword().domain():
        config_caddy()
        config_hysteria()
        config_trojan()
        config_trojan_go()
    config_openppp2()
