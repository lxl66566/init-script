import logging
import subprocess

from . import rc_sudo
from .mycache import SetCache

map_name_servicename = {
    "caddy": "caddy",
    "hysteria": "hysteria-server@hysteria",
    "trojan-go": "trojan-go",
    "trojan": "trojan",
    "openppp2": "openppp2",
}


def enable_start_service(service_name: str):
    """
    启用服务并设置开机自启
    :param service_name: 服务名
    """
    rc_sudo(f"systemctl enable --now {service_name}")


def show_all_status():
    """
    展示服务运行状态，尝试重启失败服务
    """

    def show_one_status_and_restart_failed(service: str):
        rc_sudo(f"systemctl status {service} --no-pager", check=False)
        if not is_service_running(service):
            restart_service(service)

    for name, service in map_name_servicename.items():
        if SetCache("package_installed").in_set(name):
            show_one_status_and_restart_failed(service)


def restart_service(service_name: str | list[str]):
    """
    重启服务
    :param service_name: 待重启的服务名
    """
    if isinstance(service_name, str):
        service_name = [service_name]
    for name in service_name:
        if SetCache("package_installed").in_set(name):
            rc_sudo(f"systemctl restart {map_name_servicename[name]}", check=False)


def restart_all_proxy_services():
    """
    重启所有服务
    """
    for name, service in map_name_servicename.items():
        if SetCache("package_installed").in_set(name):
            restart_service(service)


def is_service_running(service_name: str):
    """
    检查服务是否正在运行
    :param service_name: 待检查的服务名
    :return: 如果服务正在运行返回 True，否则返回 False
    """
    cmd = ["systemctl", "is-active", service_name]
    try:
        output = subprocess.check_output(cmd).decode().strip()
        return output == "active"
    except subprocess.CalledProcessError:
        return False


def reload_or_start_service(service_name: str):
    """
    重新加载服务配置文件，如果服务正在运行则尝试重新加载，否则启动服务。
    :param service_name: 待重新加载的服务名
    """
    logging.info(f"Reloading/Starting service: {service_name}")
    if is_service_running(service_name):
        try:
            rc_sudo(f"systemctl reload {service_name}", capture_output=True)
            logging.info(f"重新加载 {service_name} 成功")
        except subprocess.CalledProcessError:
            rc_sudo(f"systemctl restart {service_name}")
        rc_sudo(f"systemctl reload {service_name}")
    else:
        logging.warning(f"Service {service_name} is not running. Starting...")
